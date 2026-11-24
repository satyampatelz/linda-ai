"""One-time Gmail auth — run this ONCE from the terminal:

    python -m backend.app.gmail.auth

It opens Google's consent screen in your browser. Sign in with the
Google account whose Gmail Linda should read, click Allow, and the
browser tab says "The authentication flow has completed". token.json is
saved into data/ (git-ignored) and refreshes itself afterwards — you
never run this again unless you revoke access in your Google account.

Prerequisite: client_secret.json (from Google Cloud Console) must be in
the project folder — see GMAIL_SETUP.md for the full steps.
"""
import sys
from pathlib import Path

# Allow running as `python -m backend.app.gmail.auth` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.app.gmail.client import (  # noqa: E402
    CLIENT_SECRET_PATHS, SCOPES, TOKEN_PATH, _find_client_secret)


def main() -> int:
    from google_auth_oauthlib.flow import InstalledAppFlow

    secret = _find_client_secret()
    if secret is None:
        print("client_secret.json nahi mila!")
        print()
        print("Pehle Google Cloud Console se client_secret.json download")
        print("karke project folder me rakho. Steps GMAIL_SETUP.md me hain.")
        print("Dekhi gayi jagah:")
        for path in CLIENT_SECRET_PATHS:
            print(f"  - {path}")
        return 1

    print(f"client_secret.json mil gaya: {secret}")
    print("Browser me Google ka consent screen khul raha hai...")
    print("(Sign in karo, phir Allow dabao — token data/token.json me save hoga.)")
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    print()
    print(f"Ho gaya! Token save ho gaya: {TOKEN_PATH}")
    print("Ab Linda se chat me bolo: 'mere Gmail me kya aaya hai?'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
