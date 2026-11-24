"""Messaging control tool — the agent turns WhatsApp / Instagram
auto-reply ON and OFF from chat (v0.7).

The user never touches Settings for this: he just talks to Linda
("ab se Instagram ke messages dekhna", "WhatsApp band kar do") and the
agent calls set_messaging. The ON/OFF state lives in SQLite, so it
survives restarts.

Credentials (token, IDs) come from the in-chat SECURE BOX: when the
user enables a platform whose credentials are missing, the tool records
a pending request and the chat UI shows a masked password-style input
card in the conversation. He pastes the token there once; it is saved
to .env (same pattern as the Gemini key — never echoed back, never
logged) and auto-reply starts. .env by hand stays as an alternative
for advanced users. Secrets are NEVER pasted as plain chat text.
"""
import logging

from ..config import settings
from ..messaging import autoreply, store

logger = logging.getLogger("linda.tools.messaging")

PLATFORMS = ("whatsapp", "instagram")

# What the brain may pass as `platform` (small local models vary).
_ALIASES = {
    "whatsapp": "whatsapp",
    "wa": "whatsapp",
    "whats app": "whatsapp",
    "instagram": "instagram",
    "ig": "instagram",
    "insta": "instagram",
}

# Human names + the .env keys each platform needs to send replies.
_DISPLAY = {"whatsapp": "WhatsApp", "instagram": "Instagram"}
_REQUIRED_ENV = {
    "whatsapp": ["WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"],
    "instagram": ["INSTAGRAM_TOKEN", "INSTAGRAM_PAGE_ID"],
}
# All credential fields per platform (UI field name -> settings attr).
# token + target_id are needed to SEND; verify_token is needed for the
# webhook (without it Meta never delivers messages); app_secret is
# recommended (webhook signature check).
_CREDENTIAL_ATTRS = {
    "whatsapp": {
        "token": "whatsapp_token",
        "target_id": "whatsapp_phone_number_id",
        "verify_token": "whatsapp_verify_token",
        "app_secret": "whatsapp_app_secret",
    },
    "instagram": {
        "token": "instagram_token",
        "target_id": "instagram_page_id",
        "verify_token": "instagram_verify_token",
        "app_secret": "instagram_app_secret",
    },
}


def _normalize(platform: str) -> str:
    return _ALIASES.get((platform or "").strip().lower(), "")


def _missing_keys(platform: str) -> list:
    """Which .env keys are still empty for SENDING (token + target id)."""
    cfg = autoreply.platform_config(platform)
    missing = []
    if not cfg["token"]:
        missing.append(_REQUIRED_ENV[platform][0])
    if not cfg["target_id"]:
        missing.append(_REQUIRED_ENV[platform][1])
    return missing


def missing_fields(platform: str) -> list:
    """Which credential fields are still empty for this platform, as UI
    field names (["token", "target_id", "verify_token", "app_secret"]
    subset). Used to build the secure-box pending request."""
    attrs = _CREDENTIAL_ATTRS.get(platform, {})
    return [f for f, attr in attrs.items() if not getattr(settings, attr, "")]


def set_messaging(platform: str, enabled: bool) -> str:
    """Turn auto-reply ON or OFF for one platform. Returns the exact
    confirmation (or the one-time setup blocker) for the agent to relay
    to the user in chat — plain language, no follow-up questions."""
    platform = _normalize(platform)
    if not platform:
        return (
            "Platform samajh nahi aaya — 'WhatsApp' ya 'Instagram' bolo. "
            "Jaise: 'ab se Instagram ke messages dekhna' ya "
            "'WhatsApp band kar do'."
        )
    name = _DISPLAY[platform]
    enabled = bool(enabled)

    if enabled:
        missing = _missing_keys(platform)
        if missing:
            # One-time setup blocker: record a pending secure-box
            # request (all missing fields, so one card completes the
            # setup), say once what is missing and where to paste it,
            # then stop — never nag, never ask for secrets in chat text.
            pending = missing_fields(platform)
            if pending:
                store.set_pending_credential(platform, pending)
            keys = " aur ".join(missing)
            logger.info("Cannot enable %s auto-reply: missing %s",
                        platform, keys)
            return (
                f"{name} ka auto-reply on nahi ho paya — {keys} set nahi "
                f"hai. Neeche chat me ek secure box khul gaya hai — usme "
                f"{keys} paste kar do, main save karke auto-reply chalu "
                f"kar dunga. (Token kabhi chat message me mat likho — "
                f"sirf secure box me. .env me haath se daalna ho toh "
                f"steps MESSAGING_SETUP.md me hain.)"
            )
        already = store.get_platform_enabled(platform)
        store.set_platform_enabled(platform, True)
        logger.info("%s auto-reply enabled from chat", platform)
        # Sending works, but if the webhook side is still missing
        # (verify token), Meta will never deliver messages — offer the
        # secure box for those too, once.
        pending = [f for f in missing_fields(platform)
                   if f in ("verify_token", "app_secret")]
        if pending:
            store.set_pending_credential(platform, pending)
            base = (f"{name} ka auto-reply pehle se on hai."
                    if already else
                    f"Ho gaya — ab se {name} ke messages ka reply main "
                    f"khud dunga, tujhse nahi puchunga.")
            return (
                f"{base} Ek cheez aur: webhook ke liye verify token bhi "
                f"chahiye (warna message aayega hi nahi) — neeche secure "
                f"box me daal do."
            )
        store.clear_pending_credential(platform)
        if already:
            return (f"{name} ka auto-reply pehle se on hai — aane wale "
                    f"messages ka reply main khud de raha hoon.")
        return (
            f"Ho gaya — ab se {name} ke messages ka reply main khud dunga, "
            f"tujhse nahi puchunga."
        )

    already_off = not store.get_platform_enabled(platform)
    store.set_platform_enabled(platform, False)
    logger.info("%s auto-reply disabled from chat", platform)
    if already_off:
        return f"{name} ka auto-reply pehle se band hai."
    return (
        f"Ho gaya — {name} ka auto-reply band kar diya hai. Message aayega "
        f"toh reply nahi jayega."
    )


def complete_setup(platform: str) -> dict:
    """Called after credentials are saved (secure box or .env by hand):
    refresh the pending request to what is STILL missing, and auto-enable
    the platform the moment sending is configured (token + target id) —
    so the user pastes once and auto-reply just starts. Returns
    {"enabled": bool, "still_missing": [field, ...]}. Never raises for
    a bad platform — it just reports enabled False."""
    platform = _normalize(platform)
    if not platform:
        return {"enabled": False, "still_missing": []}
    still = missing_fields(platform)
    if still:
        store.set_pending_credential(platform, still)
    else:
        store.clear_pending_credential(platform)
    if not _missing_keys(platform):
        store.set_platform_enabled(platform, True)
        logger.info("%s auto-reply auto-enabled (credentials complete)",
                    platform)
        return {"enabled": True, "still_missing": still}
    return {"enabled": False, "still_missing": still}


def get_messaging_status() -> str:
    """Short status of both platforms: ON/OFF + configured or not.
    Used when the user asks ('WhatsApp reply on hai?')."""
    lines = []
    for platform in PLATFORMS:
        name = _DISPLAY[platform]
        enabled = store.get_platform_enabled(platform)
        missing = _missing_keys(platform)
        if enabled and not missing:
            lines.append(
                f"{name}: ON hai — aane wale messages ka reply main khud "
                f"de raha hoon.")
        elif enabled:
            lines.append(
                f"{name}: ON hai par setup adhoora hai "
                f"({', '.join(missing)} set nahi hai) — reply nahi jayega "
                f"jab tak secure box me ye na daal do (bolo '{name} ke "
                f"messages dekhna' toh box khul jayega).")
        elif missing:
            lines.append(
                f"{name}: OFF hai, aur setup bhi nahi hua "
                f"({', '.join(missing)} missing hai) — bolo '{name} ke "
                f"messages dekhna', phir secure box me ye daal do.")
        else:
            lines.append(
                f"{name}: OFF hai (setup ready hai — on karne ke liye bolo "
                f"'{name} ke messages dekhna').")
    return " ".join(lines)
