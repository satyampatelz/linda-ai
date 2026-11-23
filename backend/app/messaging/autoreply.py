"""Auto-reply engine — the brain behind WhatsApp + Instagram replies.

One inbound text message in, one reply out, fully automatic: the user
never gets asked what to say. The only things that can stop a reply are
Meta's own rules and loop guards (never a prompt to the user):
  * platform OFF or not configured yet
  * message already handled (Meta redelivers sometimes — dedupe by id)
  * outside Meta's 24-hour customer-service window
  * more than 30 replies to the same contact in the last hour (loop guard)
  * the brain or the send itself fails (logged, no crash, no retry storm)
"""
import logging
import time

from .. import brain
from ..config import settings
from . import instagram, store, whatsapp

logger = logging.getLogger("satyam.messaging.autoreply")

REPLY_WINDOW_SECONDS = 24 * 3600  # Meta's 24-hour customer-service window
MAX_REPLIES_PER_HOUR = 30         # loop guard per contact
MAX_TEXT_LEN = {"whatsapp": 4096, "instagram": 2000}

PERSONA_PROMPT = (
    "You are Satyam, replying to a friend's WhatsApp/Instagram DM as yourself. "
    "You are texting back as Satyam — casual, short, natural, like a real person "
    "chatting on their phone. Reply in the same language and script the sender "
    "used (English, Hindi in Devanagari, or Hinglish in Roman letters); default "
    "to English when unclear. Keep replies to 1-3 short sentences. Never say you "
    "are an AI, a bot, or an assistant. Never add explanations about yourself — "
    "just reply to the message."
)


def platform_config(platform: str) -> dict:
    """Live config for one platform (enabled, token, send target id).

    Enabled comes from the SQLite control table (v0.7): the user turns
    a platform ON/OFF by talking to Satyam in chat. Token + target id
    come from .env only — never from Settings, never from chat."""
    if platform == "whatsapp":
        return {
            "enabled": store.get_platform_enabled("whatsapp"),
            "token": settings.whatsapp_token,
            "target_id": settings.whatsapp_phone_number_id,
        }
    if platform == "instagram":
        return {
            "enabled": store.get_platform_enabled("instagram"),
            "token": settings.instagram_token,
            "target_id": settings.instagram_page_id,
        }
    return {"enabled": False, "token": "", "target_id": ""}


def is_active(platform: str) -> bool:
    """True only when the platform is ON and has what sending needs.
    Default is OFF: a platform starts auto-replying only after the user
    says so in chat ("ab se Instagram ke messages dekhna")."""
    cfg = platform_config(platform)
    return bool(cfg["enabled"] and cfg["token"] and cfg["target_id"])


def send_reply(platform: str, contact_id: str, text: str) -> str:
    """Send via the right client. Returns Meta's message id."""
    cfg = platform_config(platform)
    if platform == "whatsapp":
        return whatsapp.send_text(contact_id, text, cfg["token"],
                                  cfg["target_id"])
    if platform == "instagram":
        return instagram.send_text(contact_id, text, cfg["token"],
                                   cfg["target_id"])
    raise ValueError(f"Unknown platform: {platform}")


def _clean_reply(text: str, platform: str) -> str:
    """Tidy a brain reply for chat: no code fences, no huge gaps,
    within the platform's length limit."""
    reply = (text or "").strip()
    if reply.startswith("```") and reply.endswith("```") and len(reply) > 6:
        reply = reply[3:-3].strip()
        if "\n" in reply and reply.split("\n", 1)[0].strip().lower() in (
                "text", "plain", "plaintext"):
            reply = reply.split("\n", 1)[1].strip()
    while "\n\n\n" in reply:
        reply = reply.replace("\n\n\n", "\n\n")
    limit = MAX_TEXT_LEN.get(platform, 2000)
    if len(reply) > limit:
        reply = reply[: limit - 3].rstrip() + "..."
    return reply


def handle_incoming(platform: str, message_id: str, contact_id: str,
                    text: str, timestamp: float,
                    chat_fn=None, send_fn=None) -> dict:
    """Handle one inbound text message. Returns {"action", "reason"[,
    "reply"]}. Never raises — every failure is logged and reported as
    a skip, so one bad message can never crash the webhook.

    `chat_fn` / `send_fn` are injectable for tests (they default to the
    real brain and the real Meta send).
    """
    chat_fn = chat_fn or brain.chat
    send_fn = send_fn or send_reply
    try:
        return _handle(platform, message_id, contact_id, text, timestamp,
                       chat_fn, send_fn)
    except Exception:  # noqa: BLE001 — the webhook must never crash
        logger.exception("Auto-reply failed for %s message %s",
                         platform, message_id)
        return {"action": "skipped", "reason": "internal_error"}


def _handle(platform, message_id, contact_id, text, timestamp,
            chat_fn, send_fn) -> dict:
    if not is_active(platform):
        return {"action": "skipped", "reason": "platform_off_or_unconfigured"}

    # Dedupe FIRST, before any work — Meta redelivers webhooks, and a
    # crash mid-reply must never cause a second reply to the same message.
    if not store.seen_message(platform, message_id):
        return {"action": "skipped", "reason": "duplicate"}

    # 24-hour window: measured from the contact's LAST inbound message
    # (this one, or a newer one we already recorded).
    now = time.time()
    msg_ts = timestamp or now
    last_in = store.get_last_incoming(platform, contact_id) or 0
    window_start = max(msg_ts, last_in)
    store.update_last_incoming(platform, contact_id, msg_ts)
    if now - window_start > REPLY_WINDOW_SECONDS:
        logger.info("Skipping %s message %s: outside 24h window",
                    platform, message_id)
        return {"action": "skipped", "reason": "outside_24h_window"}

    # Loop guard: never flood one contact.
    if store.count_recent_replies(platform, contact_id) >= MAX_REPLIES_PER_HOUR:
        logger.warning("Skipping %s message %s: rate limit for %s",
                       platform, message_id, contact_id)
        return {"action": "skipped", "reason": "rate_limited"}

    store.record_message(platform, contact_id, "user", text)
    history = store.get_history(platform, contact_id)
    messages = [{"role": "system", "content": PERSONA_PROMPT}] + history
    try:
        raw_reply = chat_fn(messages, temperature=0.7)
    except brain.BrainError as e:
        logger.warning("Brain failed for %s message %s: %s",
                       platform, message_id, e)
        return {"action": "skipped", "reason": "brain_error"}
    reply = _clean_reply(raw_reply, platform)
    if not reply:
        return {"action": "skipped", "reason": "empty_reply"}
    try:
        sent_id = send_fn(platform, contact_id, reply)
    except Exception as e:  # noqa: BLE001 — send errors are logged, not fatal
        logger.warning("Send failed for %s message %s: %s",
                       platform, message_id, e)
        return {"action": "skipped", "reason": "send_failed"}
    store.record_message(platform, contact_id, "assistant", reply)
    logger.info("Replied to %s %s (inbound %s, sent %s)",
                platform, contact_id, message_id, sent_id)
    return {"action": "replied", "reason": "ok", "reply": reply}
