"""Instagram Messaging API client — official Meta API only.

Send: POST https://graph.facebook.com/v26.0/{page-id}/messages
Docs: developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login
      (Page-connected flow: Instagram Business/Creator account linked to
      a Facebook Page; the Page access token sends the DMs.)

No unofficial libraries, no login automation — this is the official
route, so there is no ban risk from the integration itself.
"""
import logging

import httpx

from .whatsapp import GRAPH_BASE, GRAPH_VERSION, MessagingError

logger = logging.getLogger("satyam.messaging.instagram")

MAX_TEXT_LEN = 2000  # Instagram text-message limit


def parse_webhook(payload: dict):
    """Pull inbound TEXT messages out of an Instagram webhook payload.

    Returns a list of dicts: {message_id, contact_id, text, timestamp}.
    Skips echoes of our own sent messages (is_echo), delivery/read
    receipts, reactions, postbacks, and non-text messages — silently,
    like Meta expects (the webhook must still answer 200).

    Groups: the Instagram Messaging API does not support group messaging
    at all — a professional account only converses 1:1 — so every
    message here is a 1:1 DM.
    """
    messages = []
    if not isinstance(payload, dict):
        return messages
    for entry in payload.get("entry", []) or []:
        for event in entry.get("messaging", []) or []:
            msg = event.get("message")
            if not isinstance(msg, dict):
                continue  # delivery / read / reaction / postback event
            if msg.get("is_echo"):
                continue  # our own sent message coming back — never reply
            text = msg.get("text", "")
            if not text or not str(text).strip():
                continue  # attachment-only message (share, sticker, ...)
            sender = (event.get("sender") or {}).get("id", "")
            mid = msg.get("mid", "")
            try:
                # Instagram timestamps are epoch MILLIseconds.
                ts = float(event.get("timestamp", 0) or 0) / 1000.0
            except (TypeError, ValueError):
                ts = 0.0
            if sender and mid:
                messages.append({
                    "message_id": mid,
                    "contact_id": sender,
                    "text": str(text),
                    "timestamp": ts,
                })
    return messages


def send_text(recipient_id: str, text: str, token: str, page_id: str,
              timeout: int = 30) -> str:
    """Send one DM. Returns Meta's message id."""
    body = (text or "").strip()
    if len(body) > MAX_TEXT_LEN:
        body = body[: MAX_TEXT_LEN - 3].rstrip() + "..."
    url = f"{GRAPH_BASE}/{GRAPH_VERSION}/{page_id}/messages"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "recipient": {"id": recipient_id},
                    "messaging_type": "RESPONSE",
                    "message": {"text": body},
                },
            )
    except httpx.TimeoutException as e:
        raise MessagingError(f"Instagram send timeout: {e}") from e
    except httpx.HTTPError as e:
        raise MessagingError(f"Instagram send failed (network): {e}") from e
    if resp.status_code >= 400:
        detail = ""
        try:
            err = resp.json().get("error", {})
            detail = f" — {err.get('message', '')} (code {err.get('code', '?')})"
        except ValueError:
            detail = f" — {resp.text[:200]}"
        raise MessagingError(
            f"Instagram send rejected (HTTP {resp.status_code}){detail}")
    try:
        return resp.json()["message_id"]
    except (KeyError, ValueError):
        logger.warning("Instagram send: unparseable success response: %s",
                       resp.text[:300])
        return ""
