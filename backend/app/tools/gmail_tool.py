"""Gmail brain tools (v0.8) — the agent reads the user's mailbox.

Two tools, both chat-driven:
  * read_gmail — list/search recent emails (sender, subject, snippet, body)
  * find_otp   — find the OTP code in a recent email from a site/sender

Read-only: the agent never sends, deletes, or modifies mail. When Gmail
is not set up yet, both tools return a clear one-time setup message
(pointing at GMAIL_SETUP.md) instead of crashing — the user runs the
one-time auth once, then these just work.

The OTP code itself is returned to the agent (it needs the digits to
fill the form in the browser). Codes are short-lived by design; they are
never stored anywhere by Satyam.
"""
import logging

from ..gmail import client as gmail_client
from ..gmail import otp as gmail_otp

logger = logging.getLogger("satyam.tools.gmail")

MAX_BODY_CHARS = 1500


def _format_message(msg: dict, include_body: bool = True) -> str:
    lines = [
        f"From: {msg.get('sender', '')}",
        f"Subject: {msg.get('subject', '')}",
    ]
    if msg.get("date"):
        lines.append(f"Date: {msg['date']}")
    if include_body:
        body = (msg.get("body") or msg.get("snippet") or "").strip()
        if len(body) > MAX_BODY_CHARS:
            body = body[:MAX_BODY_CHARS] + "… (aage ka hissa cut hai)"
        lines.append(body if body else "(khali email)")
    else:
        lines.append(msg.get("snippet", ""))
    return "\n".join(lines)


def read_gmail(query: str = "", max_results: int = 5) -> str:
    """Search/read recent emails. `query` uses Gmail search syntax
    ('from:internshala', 'internship', 'newer_than:2d'); empty means the
    newest inbox mail. Returns sender/subject/body for each match."""
    try:
        service = gmail_client.get_service()
    except gmail_client.GmailNotConfigured as e:
        return str(e)
    try:
        messages = gmail_client.search_messages(
            service, query or "in:inbox", max_results=max_results)
    except RuntimeError as e:
        logger.warning("read_gmail failed: %s", e)
        return str(e)
    if not messages:
        return ("Koi email nahi mila"
                + (f" — query thi: '{query}'." if query else "."))
    parts = [f"{len(messages)} email mile:\n"]
    for i, msg in enumerate(messages, 1):
        parts.append(f"--- Email {i} ---\n{_format_message(msg)}")
    return "\n\n".join(parts)


def get_otp_code(sender: str, minutes: int = 10) -> str | None:
    """Internal helper: the raw OTP code (or None). Used by the browser
    OTP auto-fill so it can fill the code without parsing chat text."""
    try:
        service = gmail_client.get_service()
    except gmail_client.GmailNotConfigured:
        return None
    found = gmail_otp.find_otp_code(service, sender, minutes=minutes)
    return found["code"] if found else None


def find_otp(sender: str, minutes: int = 10) -> str:
    """Find the OTP code in a recent email from `sender` (a site name
    like 'Internshala' or an email address). Only emails from the last
    `minutes` minutes count — OTPs expire, stale codes are never used.
    Returns the code, or a clear message when none is found."""
    try:
        service = gmail_client.get_service()
    except gmail_client.GmailNotConfigured as e:
        return str(e)
    found = gmail_otp.find_otp_code(service, sender, minutes=minutes)
    if not found:
        return (
            f"Pichhle {minutes} minute me '{sender}' se OTP wala koi email "
            f"nahi mila — ye SMS OTP ho sakta hai (SMS Gmail me nahi aata). "
            f"User se chat me code maango: finish answer me bas ye likho — "
            f"'SMS pe aaya OTP bhejo' — browser band mat karo, aur jab code "
            f"aaye toh browser_fill_otp me code de ke khud bhar do. (Ye bhi "
            f"check karo ki OTP wala email isi Gmail account pe aaya hai ya "
            f"kisi aur pe.)"
        )
    return (
        f"OTP mil gaya: {found['code']} "
        f"(email: '{found['subject']}' — {found['sender']})"
    )
