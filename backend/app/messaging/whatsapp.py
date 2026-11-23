"""WhatsApp Cloud API client — official Meta API only.

Send: POST https://graph.facebook.com/v26.0/{phone-number-id}/messages
Docs: developers.facebook.com/docs/whatsapp/cloud-api

No unofficial libraries, no WhatsApp Web automation — this is the
official route, so there is no ban risk from the integration itself.
"""
import logging

import httpx

logger = logging.getLogger("satyam.messaging.whatsapp")

GRAPH_BASE = "https://graph.facebook.com"
GRAPH_VERSION = "v26.0"  # pinned; Meta keeps old versions working for years

MAX_TEXT_LEN = 4096  # WhatsApp text-message limit


class MessagingError(Exception):
    """Raised when Meta rejects a send (or the network fails)."""


def parse_webhook(payload: dict):
    """Pull inbound TEXT messages out of a WhatsApp webhook payload.

    Returns a list of dicts: {message_id, contact_id, text, timestamp}.
    Skips delivery receipts (statuses), non-text messages (image/audio/
    sticker/...), and anything malformed — silently, like Meta expects
    (the webhook must still answer 200).

    Groups: the WhatsApp Cloud API does not deliver group messages to
    business webhooks at all, so every message here is a 1:1 chat.
    """
    messages = []
    if not isinstance(payload, dict):
        return messages
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            if value.get("messaging_product") != "whatsapp":
                continue
            for msg in value.get("messages", []) or []:
                if msg.get("type") != "text":
                    continue
                body = (msg.get("text") or {}).get("body", "")
                if not body or not str(body).strip():
                    continue
                try:
                    ts = float(msg.get("timestamp", 0) or 0)
                except (TypeError, ValueError):
                    ts = 0.0
                messages.append({
                    "message_id": msg.get("id", ""),
                    "contact_id": msg.get("from", ""),
                    "text": str(body),
                    "timestamp": ts,
                })
    # Drop anything without an id or sender — dedupe needs both.
    return [m for m in messages if m["message_id"] and m["contact_id"]]


def send_text(to: str, text: str, token: str, phone_number_id: str,
              timeout: int = 30) -> str:
    """Send one text message. Returns Meta's message id."""
    body = (text or "").strip()
    if len(body) > MAX_TEXT_LEN:
        body = body[: MAX_TEXT_LEN - 3].rstrip() + "..."
    url = f"{GRAPH_BASE}/{GRAPH_VERSION}/{phone_number_id}/messages"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"preview_url": False, "body": body},
                },
            )
    except httpx.TimeoutException as e:
        raise MessagingError(f"WhatsApp send timeout: {e}") from e
    except httpx.HTTPError as e:
        raise MessagingError(f"WhatsApp send failed (network): {e}") from e
    if resp.status_code >= 400:
        detail = ""
        try:
            err = resp.json().get("error", {})
            detail = f" — {err.get('message', '')} (code {err.get('code', '?')})"
        except ValueError:
            detail = f" — {resp.text[:200]}"
        raise MessagingError(
            f"WhatsApp send rejected (HTTP {resp.status_code}){detail}")
    try:
        return resp.json()["messages"][0]["id"]
    except (KeyError, IndexError, ValueError):
        logger.warning("WhatsApp send: unparseable success response: %s",
                       resp.text[:300])
        return ""
