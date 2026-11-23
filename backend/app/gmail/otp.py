"""OTP extraction from email text + recent-mail OTP lookup.

An OTP is a 4–8 digit code. Extracting it safely matters: an email is
full of other numbers (years, order ids, phone numbers, prices), so a
bare "any digits" match would grab the wrong one. Strategy:

1. Keyword-proximity match: digits near "OTP", "code", "verification",
   "PIN" (either order, within ~40 characters). This is the reliable
   case — almost every OTP mail says "Your OTP is 482916" or similar.
2. Fallback: a standalone 6-digit token on its own (the most common OTP
   length), only when no keyword match exists.

4-digit numbers in the 1900–2099 range (years) are never returned, and
digits that are part of a longer digit run are ignored.
"""
import re
from datetime import datetime, timedelta, timezone

from .client import search_messages

_KEYWORDS = r"(?:otp|one[- ]?time\s+password|verification\s+code|verify\s+code|security\s+code|login\s+code|confirmation\s+code|code|pin)"

# Digits NEAR a keyword (either order), up to 40 non-digit chars apart.
_NEAR_AFTER = re.compile(
    rf"{_KEYWORDS}\b[^0-9]{{0,40}}?(\d{{4,8}})", re.IGNORECASE)
_NEAR_BEFORE = re.compile(
    rf"(\d{{4,8}})[^0-9]{{0,40}}?\b{_KEYWORDS}\b", re.IGNORECASE)
# Fallback: a standalone 6-digit token.
_STANDALONE_6 = re.compile(r"(?<![0-9])(\d{6})(?![0-9])")


def _is_year(code: str) -> bool:
    """4-digit years (1900–2099) are never OTPs."""
    if len(code) != 4:
        return False
    try:
        return 1900 <= int(code) <= 2099
    except ValueError:
        return False


def extract_otp(text: str) -> str | None:
    """Find the OTP code in an email's text. Returns the code, or None
    when no plausible code is present."""
    if not text:
        return None
    flat = re.sub(r"\s+", " ", text)
    for pattern in (_NEAR_AFTER, _NEAR_BEFORE):
        match = pattern.search(flat)
        if match and not _is_year(match.group(1)):
            return match.group(1)
    match = _STANDALONE_6.search(flat)
    if match:
        return match.group(1)
    return None


def find_otp_code(service, sender: str, minutes: int = 10,
                  now: datetime | None = None) -> dict | None:
    """Search recent emails from `sender` (a site name or email address)
    and extract the OTP from the newest one that has a code.

    Returns {"code", "subject", "sender", "received_at"} or None. The
    time window is checked in code (not only via Gmail's newer_than)
    so the check is exact even if Gmail's search is loose. `service` is
    injectable for tests; `now` is injectable for time-window tests.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=max(1, int(minutes)))
    query = f"from:{sender}"
    messages = search_messages(service, query, max_results=5)
    for msg in messages:
        received = msg.get("received_at")
        if received is not None and received < cutoff:
            continue  # too old — OTPs expire, never use a stale one
        text = f"{msg.get('subject', '')}\n{msg.get('snippet', '')}\n{msg.get('body', '')}"
        code = extract_otp(text)
        if code:
            return {
                "code": code,
                "subject": msg.get("subject", ""),
                "sender": msg.get("sender", ""),
                "received_at": received,
            }
    return None
