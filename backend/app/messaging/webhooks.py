"""Meta webhook endpoints — WhatsApp Cloud API + Instagram Messaging API.

GET  /webhook/whatsapp   Meta's verification handshake
POST /webhook/whatsapp   inbound messages + statuses
GET  /webhook/instagram  same, for Instagram
POST /webhook/instagram  same, for Instagram

These endpoints are PUBLIC by design (Meta's servers call them — they
can't carry the Linda API token, so they are deliberately not in the
token middleware's protected prefixes). Their auth is Meta's own:
  * GET: the verify token (a secret string you invent in the Meta
    dashboard and put in .env) must match.
  * POST: HMAC-SHA256 of the raw body with the app secret, sent as
    X-Hub-Signature-256. Skipped only when no app secret is configured
    (logged as a warning — set the secret in .env).

Every POST answers 200 immediately and does the reply work on a
background thread: Meta retries deliveries that take too long, and the
dedupe table makes a retry harmless anyway.
"""
import json
import logging
import threading

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from ..config import settings
from . import autoreply, instagram, signature, whatsapp

logger = logging.getLogger("linda.messaging.webhooks")

router = APIRouter()


def _verify_token(platform: str) -> str:
    return (settings.whatsapp_verify_token if platform == "whatsapp"
            else settings.instagram_verify_token)


def _app_secret(platform: str) -> str:
    return (settings.whatsapp_app_secret if platform == "whatsapp"
            else settings.instagram_app_secret)


def _dispatch(platform: str, message: dict):
    """Hand one inbound message to the auto-reply engine on a thread.

    A module-level function (not inlined) so tests can replace it with
    a synchronous version and observe the full webhook -> reply path.
    """
    threading.Thread(
        target=autoreply.handle_incoming,
        args=(platform, message["message_id"], message["contact_id"],
              message["text"], message["timestamp"]),
        daemon=True,
    ).start()


async def _verify(request: Request, platform: str):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    expected = _verify_token(platform)
    if mode == "subscribe" and expected and token == expected and challenge:
        logger.info("%s webhook verified", platform)
        return PlainTextResponse(challenge)
    logger.warning("%s webhook verification failed (mode=%s)", platform, mode)
    return JSONResponse(status_code=403,
                        content={"detail": "Webhook verification failed."})


async def _receive(request: Request, platform: str):
    raw = await request.body()
    secret = _app_secret(platform)
    if secret:
        sig = request.headers.get("X-Hub-Signature-256")
        if not signature.verify_signature(raw, sig, secret):
            logger.warning("%s webhook: bad signature", platform)
            return JSONResponse(status_code=403,
                                content={"detail": "Bad webhook signature."})
    else:
        logger.warning(
            "%s webhook: no app secret configured, skipping signature "
            "check — set it in .env for safety.", platform)
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return JSONResponse(status_code=400,
                            content={"detail": "Webhook body is not JSON."})
    parser = (whatsapp.parse_webhook if platform == "whatsapp"
              else instagram.parse_webhook)
    for message in parser(payload):
        _dispatch(platform, message)
    return {"ok": True}


@router.get("/webhook/whatsapp")
async def whatsapp_verify(request: Request):
    return await _verify(request, "whatsapp")


@router.post("/webhook/whatsapp")
async def whatsapp_receive(request: Request):
    return await _receive(request, "whatsapp")


@router.get("/webhook/instagram")
async def instagram_verify(request: Request):
    return await _verify(request, "instagram")


@router.post("/webhook/instagram")
async def instagram_receive(request: Request):
    return await _receive(request, "instagram")
