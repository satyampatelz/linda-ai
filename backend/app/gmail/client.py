"""Gmail API client — OAuth 2.0, read-only.

Files:
  * client_secret.json — downloaded from Google Cloud Console. Looked for
    at the project root first, then in data/. Both are git-ignored.
  * data/token.json — created by the one-time auth flow
    (python -m backend.app.gmail.auth). Refreshed automatically when it
    expires. Never committed (data/ is git-ignored).

Nothing in this module ever launches a browser on its own: if no valid
token exists, get_service() raises GmailNotConfigured with a clear
English message pointing at GMAIL_SETUP.md. The agent loop turns that
into a chat reply — the user then runs the one-time auth himself.
"""
import base64
import html as html_lib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from ..config import BASE_DIR, settings

logger = logging.getLogger("linda.gmail")

# Read-only: list + read messages. No send, no delete, no modify.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CLIENT_SECRET_PATHS = [
    BASE_DIR / "client_secret.json",
    settings.data_dir / "client_secret.json",
]
TOKEN_PATH = settings.data_dir / "token.json"

SETUP_HINT = (
    "Gmail isn't set up. You'll need to do this once: create a Google "
    "Cloud project, enable the Gmail API, download client_secret.json "
    "into the project folder, then run in the terminal: "
    "python -m backend.app.gmail.auth — Google's consent screen will "
    "open, click Allow once, that's it. Steps are in GMAIL_SETUP.md."
)


class GmailNotConfigured(Exception):
    """Raised when Gmail cannot be used yet (no token / no secret)."""


def _find_client_secret() -> Path | None:
    for path in CLIENT_SECRET_PATHS:
        if path.is_file():
            return path
    return None


def is_configured() -> bool:
    """True when a token exists (auth already done once). Used by the
    Status panel check — never touches the network."""
    return TOKEN_PATH.is_file()


def has_client_secret() -> bool:
    """True when client_secret.json is present but auth is not done yet."""
    return _find_client_secret() is not None


def get_credentials():
    """Load saved credentials, refreshing them if expired. Returns None
    when no token exists yet (the caller must run the one-time auth)."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not TOKEN_PATH.is_file():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except Exception as e:  # noqa: BLE001 — corrupt token file
        logger.warning("Couldn't read token.json: %s", e)
        return None
    if creds.valid:
        return creds
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:  # noqa: BLE001 — refresh can fail
            logger.warning("Gmail token refresh failed: %s", e)
            return None
        TOKEN_PATH.write_text(creds.to_json())
        return creds
    return None


def get_service():
    """Build the Gmail API service. Raises GmailNotConfigured when the
    one-time auth has not been done yet."""
    from googleapiclient.discovery import build

    creds = get_credentials()
    if creds is None:
        raise GmailNotConfigured(SETUP_HINT)
    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Message parsing — Gmail API payloads are nested MIME parts.
# ---------------------------------------------------------------------------
def _decode_body(data: str) -> str:
    """Base64url-decode a Gmail body part (padding is often missing)."""
    if not data:
        return ""
    data += "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 — bad encoding, skip the part
        return ""


def _strip_html(text: str) -> str:
    """Best-effort HTML -> plain text (links/paragraphs kept readable)."""
    text = re.sub(r"(?i)<(br|/p|/div|/li|/tr)\b[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _walk_parts(payload: dict, plain: list, html_parts: list):
    """Collect text/plain and text/html bodies from a (possibly nested)
    MIME payload. Attachments are ignored — we only need readable text."""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {}) or {}
    if mime == "text/plain":
        plain.append(_decode_body(body.get("data", "")))
    elif mime == "text/html":
        html_parts.append(_decode_body(body.get("data", "")))
    for part in payload.get("parts", []) or []:
        _walk_parts(part, plain, html_parts)


def parse_message(raw: dict) -> dict:
    """Turn one Gmail API `messages.get(format='full')` response into a
    plain dict: id, sender, subject, date, snippet, body, received_at
    (UTC datetime, from internalDate). Never raises — a malformed
    message becomes an empty-body entry instead of crashing the search."""
    headers = {}
    try:
        for h in raw.get("payload", {}).get("headers", []) or []:
            headers[h.get("name", "").lower()] = h.get("value", "")
    except Exception:  # noqa: BLE001 — headers are best-effort
        pass
    plain, html_parts = [], []
    try:
        _walk_parts(raw.get("payload", {}) or {}, plain, html_parts)
    except Exception:  # noqa: BLE001 — body is best-effort
        pass
    body = "\n".join(p for p in plain if p).strip()
    if not body and html_parts:
        body = _strip_html("\n".join(html_parts))
    received_at = None
    try:
        ms = int(raw.get("internalDate", 0))
        if ms:
            received_at = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        received_at = None
    return {
        "id": raw.get("id", ""),
        "sender": headers.get("from", "(unknown sender)"),
        "subject": headers.get("subject", "(no subject)"),
        "date": headers.get("date", ""),
        "snippet": raw.get("snippet", ""),
        "body": body,
        "received_at": received_at,
    }


def search_messages(service, query: str, max_results: int = 5) -> list:
    """Search the mailbox (Gmail search syntax — e.g. 'from:internshala',
    'newer_than:1d', or plain words) and return parsed messages, newest
    first. `service` is injectable so tests can pass a stub."""
    max_results = max(1, min(int(max_results), 20))
    try:
        resp = (
            service.users().messages().list(
                userId="me", q=query or "", maxResults=max_results
            ).execute()
        )
    except Exception as e:  # noqa: BLE001 — API errors become a clear message
        raise RuntimeError(f"Gmail search failed: {e}")
    messages = []
    for item in resp.get("messages", []) or []:
        try:
            raw = (
                service.users().messages().get(
                    userId="me", id=item["id"], format="full"
                ).execute()
            )
        except Exception as e:  # noqa: BLE001 — one bad message, skip it
            logger.warning("Couldn't read message %s: %s",
                           item.get("id"), e)
            continue
        messages.append(parse_message(raw))
    return messages
