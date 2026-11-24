"""Gmail access for Linda (v0.8) — official Gmail API, OAuth 2.0 only.

Read-only scope: the agent READS emails (list/search) and finds OTP codes
in them. It never sends, deletes, or modifies anything in the mailbox.

Setup (one time, see GMAIL_SETUP.md): create a Google Cloud project,
enable the Gmail API, download client_secret.json into the project
folder, then run: python -m backend.app.gmail.auth
That opens Google's consent screen once and saves token.json into
data/ (git-ignored). Tokens refresh automatically afterwards.
"""

from .client import GmailNotConfigured, get_service, search_messages
from .otp import extract_otp, find_otp_code

__all__ = [
    "GmailNotConfigured",
    "get_service",
    "search_messages",
    "extract_otp",
    "find_otp_code",
]
