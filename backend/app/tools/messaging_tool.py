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
            "Couldn't understand the platform — say 'WhatsApp' or "
            "'Instagram'. For example: 'watch my Instagram messages from "
            "now on' or 'turn off WhatsApp'."
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
            keys = " and ".join(missing)
            logger.info("Cannot enable %s auto-reply: missing %s",
                        platform, keys)
            return (
                f"Couldn't turn on {name} auto-reply — {keys} not set. "
                f"A secure box has opened below in this chat — paste "
                f"{keys} there and I'll save them and turn auto-reply on. "
                f"(Never type a token in a chat message — secure box only. "
                f"To add them to .env by hand, the steps are in "
                f"MESSAGING_SETUP.md.)"
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
            base = (f"{name} auto-reply is already on."
                    if already else
                    f"Done — from now on I'll reply to {name} messages "
                    f"myself, without asking you.")
            return (
                f"{base} One more thing: the webhook also needs a verify "
                f"token (otherwise no messages will arrive) — put it in "
                f"the secure box below."
            )
        store.clear_pending_credential(platform)
        if already:
            return (f"{name} auto-reply is already on — I'm already "
                    f"replying to incoming messages myself.")
        return (
            f"Done — from now on I'll reply to {name} messages myself, "
            f"without asking you."
        )

    already_off = not store.get_platform_enabled(platform)
    store.set_platform_enabled(platform, False)
    logger.info("%s auto-reply disabled from chat", platform)
    if already_off:
        return f"{name} auto-reply is already off."
    return (
        f"Done — {name} auto-reply is now off. Incoming messages won't "
        f"get a reply."
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
    Used when the user asks ('Is WhatsApp reply on?')."""
    lines = []
    for platform in PLATFORMS:
        name = _DISPLAY[platform]
        enabled = store.get_platform_enabled(platform)
        missing = _missing_keys(platform)
        if enabled and not missing:
            lines.append(
                f"{name}: ON — I'm replying to incoming messages myself.")
        elif enabled:
            lines.append(
                f"{name}: ON but setup is incomplete "
                f"({', '.join(missing)} not set) — no replies will go out "
                f"until you add these in the secure box (say 'watch my "
                f"{name} messages' and the box will open).")
        elif missing:
            lines.append(
                f"{name}: OFF, and not set up yet "
                f"({', '.join(missing)} missing) — say 'watch my {name} "
                f"messages', then add these in the secure box.")
        else:
            lines.append(
                f"{name}: OFF (setup is ready — to turn it on, say "
                f"'watch my {name} messages').")
    return " ".join(lines)
