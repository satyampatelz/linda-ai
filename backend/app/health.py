"""Health checks — the Status panel in the app.

Each check returns a dict:
  {"id", "label", "status", "detail", "hint"}
status is "ok" | "fail" | "skip" (skip = not relevant right now, e.g. the
Gemini check when Ollama is the active brain). Every failed check carries a
short English "how to fix it" hint. Nothing here ever raises — a check
that itself errors reports "fail" with a hint.

The Gemini key check validates with a tiny models-list call (no generation,
no quota burned). Its result is cached for 60 seconds so the panel can be
re-opened without re-hitting Google.
"""
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import httpx

from .config import settings

_GEMINI_CACHE = {"at": 0.0, "result": None}
_GEMINI_CACHE_TTL = 60.0

CHECK_TIMEOUT = 5  # seconds per network check — the panel must stay snappy


def _check(check_id, label, status, detail="", hint=""):
    return {
        "id": check_id,
        "label": label,
        "status": status,  # ok | fail | skip
        "detail": detail,
        "hint": hint,
    }


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_ollama_reachable():
    try:
        with httpx.Client(timeout=CHECK_TIMEOUT, trust_env=False) as client:
            resp = client.get(f"{settings.ollama_url}/api/tags")
    except Exception:  # noqa: BLE001 — unreachable for any reason
        return _check(
            "ollama_reachable", "Ollama is running", "fail",
            "Couldn't connect to Ollama.",
            "Open the Ollama app, or run 'ollama serve' in the terminal. "
            "If Ollama isn't installed, install it from ollama.com.",
        )
    if resp.status_code != 200:
        return _check(
            "ollama_reachable", "Ollama is running", "fail",
            f"Ollama replied: HTTP {resp.status_code}.",
            "Restart Ollama (close the app and open it again).",
        )
    return _check(
        "ollama_reachable", "Ollama is running", "ok",
        f"Connected: {settings.ollama_url}",
    )


def check_ollama_model(ollama_ok: bool):
    if not ollama_ok:
        return _check(
            "ollama_model", f"Model '{settings.ollama_model}' downloaded",
            "skip", "Ollama isn't running, so this couldn't be checked.",
        )
    try:
        with httpx.Client(timeout=CHECK_TIMEOUT, trust_env=False) as client:
            resp = client.get(f"{settings.ollama_url}/api/tags")
        names = [m.get("name", "") for m in resp.json().get("models", [])]
    except Exception:  # noqa: BLE001
        return _check(
            "ollama_model", f"Model '{settings.ollama_model}' downloaded",
            "fail", "Couldn't get the model list.",
            "Restart Ollama, then check Status again.",
        )
    wanted = settings.ollama_model
    if wanted in names or f"{wanted}:latest" in names:
        return _check(
            "ollama_model", f"Model '{wanted}' downloaded", "ok",
            f"{wanted} is ready.",
        )
    return _check(
        "ollama_model", f"Model '{wanted}' downloaded", "fail",
        "Model not downloaded.",
        f"Run this in the terminal: ollama pull {wanted}  (~1.9 GB, once).",
    )


def check_gemini_key():
    if settings.model_provider != "gemini":
        return _check(
            "gemini_key", "Gemini key set + valid", "skip",
            "The Ollama brain is active right now — no Gemini key needed.",
        )
    if not settings.gemini_api_key:
        return _check(
            "gemini_key", "Gemini key set + valid", "fail",
            "Gemini key not set.",
            "Add a Gemini key in Settings (⚙️) — a free key is available at "
            "aistudio.google.com (no card needed).",
        )
    now = time.monotonic()
    if _GEMINI_CACHE["result"] is not None and now - _GEMINI_CACHE["at"] < _GEMINI_CACHE_TTL:
        return _GEMINI_CACHE["result"]
    # Tiny models-list call — validates the key without spending generation quota.
    resp = None
    try:
        with httpx.Client(timeout=CHECK_TIMEOUT) as client:
            resp = client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": settings.gemini_api_key, "pageSize": 1},
            )
    except Exception:  # noqa: BLE001
        pass
    if resp is None:
        result = _check(
            "gemini_key", "Gemini key set + valid", "fail",
            "Couldn't connect to Google.",
            "Check your internet, then open Status again.",
        )
    elif resp.status_code == 200:
        result = _check(
            "gemini_key", "Gemini key set + valid", "ok",
            f"Key is valid, model: {settings.gemini_model}.",
        )
    elif resp.status_code in (400, 401, 403):
        result = _check(
            "gemini_key", "Gemini key set + valid", "fail",
            "Key rejected (auth failed).",
            "Enter the correct key in Settings (⚙️) — you can make a new "
            "free key at aistudio.google.com.",
        )
    else:
        result = _check(
            "gemini_key", "Gemini key set + valid", "fail",
            f"Google replied: HTTP {resp.status_code}.",
            "Open Status again in a little while.",
        )
    _GEMINI_CACHE["at"] = now
    _GEMINI_CACHE["result"] = result
    return result


def check_git():
    if not shutil.which("git"):
        return _check(
            "git", "Git installed + configured", "fail",
            "Git not found.",
            "Install Git from git-scm.com, then set your name and email in "
            "the terminal (see the hint below).",
        )
    try:
        name = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        email = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return _check(
            "git", "Git installed + configured", "fail",
            "Couldn't read the Git config.",
            "Run in the terminal: 'git config --global user.name \"Your Name\"' and "
            "'git config --global user.email \"you@email.com\"'.",
        )
    if name and email:
        return _check(
            "git", "Git installed + configured", "ok",
            f"{name} <{email}>",
        )
    return _check(
        "git", "Git installed + configured", "fail",
        "Git is there, but name/email aren't set.",
        "Run this in the terminal: git config --global user.name \"Your Name\" "
        "and git config --global user.email \"you@email.com\"",
    )


def check_chromium():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _check(
            "chromium", "Playwright Chromium installed", "fail",
            "Playwright package not found.",
            "Run setup again (setup.bat or bash setup.sh).",
        )
    try:
        with sync_playwright() as p:
            exe = Path(p.chromium.executable_path)
    except Exception:  # noqa: BLE001 — executable_path raises when missing
        return _check(
            "chromium", "Playwright Chromium installed", "fail",
            "Chromium browser not downloaded.",
            "Run in the terminal (venv active): playwright install chromium",
        )
    if exe.exists():
        return _check(
            "chromium", "Playwright Chromium installed", "ok",
            "Browser is ready.",
        )
    return _check(
        "chromium", "Playwright Chromium installed", "fail",
        "Chromium browser not downloaded.",
        "Run in the terminal (venv active): playwright install chromium",
    )


def check_messaging(platform: str):
    """WhatsApp / Instagram auto-reply readiness. Not configured at all
    is a "skip" (messaging is optional — no setup failure). Partially
    configured is a "fail" with a hint, because the user clearly started
    the setup and something is missing. The ON/OFF state comes from the
    SQLite control table (v0.7) — the user flips it by talking to Linda
    in chat, not from Settings."""
    from .messaging import store as messaging_store

    if platform == "whatsapp":
        enabled = messaging_store.get_platform_enabled("whatsapp")
        token = settings.whatsapp_token
        target = settings.whatsapp_phone_number_id
        target_name = "phone number ID"
        verify = settings.whatsapp_verify_token
        secret = settings.whatsapp_app_secret
        label = "WhatsApp auto-reply"
        setup_hint = ("Steps are in MESSAGING_SETUP.md: add the WhatsApp "
                      "product in the Meta app, then say in chat 'watch my "
                      "WhatsApp messages' — put the token + IDs in the "
                      "secure box (or in .env by hand).")
    else:
        enabled = messaging_store.get_platform_enabled("instagram")
        token = settings.instagram_token
        target = settings.instagram_page_id
        target_name = "page ID"
        verify = settings.instagram_verify_token
        secret = settings.instagram_app_secret
        label = "Instagram auto-reply"
        setup_hint = ("Steps are in MESSAGING_SETUP.md: make Instagram a "
                      "Business/Creator account, link it to a Facebook Page, "
                      "then say in chat 'watch my Instagram messages' — put "
                      "the token + IDs in the secure box (or in .env by hand).")

    check_id = f"{platform}_autoreply"
    if not enabled:
        return _check(check_id, label, "skip",
                      "Auto-reply is off — say in chat "
                      f"'watch my {platform.capitalize()} messages' to turn "
                      "it on.")
    missing = [name for name, v in (("token", token),
                                    (target_name, target),
                                    ("verify token", verify)) if not v]
    if len(missing) == 3:
        return _check(check_id, label, "skip",
                      "Not set up — set it up from MESSAGING_SETUP.md if you want.")
    if missing:
        return _check(
            check_id, label, "fail",
            f"Setup is incomplete — missing: {', '.join(missing)}.",
            setup_hint,
        )
    detail = "Ready — incoming DMs will be answered automatically."
    if not secret:
        detail += (" (App secret not set — webhook signatures won't be "
                   "checked. Add it in the secure box to be safer.)")
    return _check(check_id, label, "ok", detail)


def check_whatsapp_autoreply():
    return check_messaging("whatsapp")


def check_instagram_autoreply():
    return check_messaging("instagram")


def check_gmail():
    """Gmail read access (v0.8). Optional, so "not set up at all" is a
    skip, not a failure. client_secret present but no token = the user
    started the setup and did not finish the one-time auth."""
    from .gmail.client import has_client_secret, is_configured

    if is_configured():
        return _check(
            "gmail", "Gmail connected", "ok",
            "token.json is ready — Linda can read emails.",
        )
    if has_client_secret():
        return _check(
            "gmail", "Gmail connected", "fail",
            "client_secret.json is there, but the one-time auth hasn't been done.",
            "Run this in the terminal (project folder, venv active): "
            "python -m backend.app.gmail.auth — Google's consent screen will "
            "open, click Allow once. Steps are in GMAIL_SETUP.md.",
        )
    return _check(
        "gmail", "Gmail connected", "skip",
        "Gmail isn't set up — set it up from GMAIL_SETUP.md if you want "
        "(for reading emails + email OTP auto-fill).",
    )


def check_workspace_writable():
    try:
        settings.workspace_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=settings.workspace_dir, delete=True
        ) as f:
            f.write(b"ok")
        return _check(
            "workspace", "Workspace is writable", "ok",
            str(settings.workspace_dir),
        )
    except Exception as e:  # noqa: BLE001
        return _check(
            "workspace", "Workspace is writable", "fail",
            f"Couldn't write to the workspace: {e}",
            "Check the project folder's permissions, or copy the folder "
            "somewhere else (like the Desktop) and run it from there.",
        )


# ---------------------------------------------------------------------------
def run_all_checks() -> dict:
    """Run every check. Never raises — a broken check reports 'fail'."""
    checks = []
    try:
        ollama = check_ollama_reachable()
    except Exception:  # noqa: BLE001 — safety net, should not happen
        ollama = _check("ollama_reachable", "Ollama is running", "fail",
                        "The check itself couldn't run.",
                        "Open the Ollama app or run 'ollama serve'.")
    checks.append(ollama)
    ollama_ok = ollama["status"] == "ok"

    for fn in (check_gemini_key, check_git, check_chromium,
               check_workspace_writable, check_gmail,
               check_whatsapp_autoreply,
               check_instagram_autoreply):
        try:
            checks.append(fn())
        except Exception:  # noqa: BLE001
            checks.append(_check(fn.__name__, fn.__name__, "fail",
                                 "The check itself couldn't run.",
                                 "Restart the server and try again."))
    try:
        checks.insert(1, check_ollama_model(ollama_ok))
    except Exception:  # noqa: BLE001
        checks.insert(1, _check("ollama_model", "Ollama model", "fail",
                                "The check itself couldn't run.",
                                "Restart Ollama."))

    failed = [c for c in checks if c["status"] == "fail"]
    return {
        "all_ok": not failed,
        "provider": settings.model_provider,
        "checks": checks,
    }
