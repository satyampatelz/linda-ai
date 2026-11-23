"""Health checks — the Status panel in the app.

Each check returns a dict:
  {"id", "label", "status", "detail", "hint"}
status is "ok" | "fail" | "skip" (skip = not relevant right now, e.g. the
Gemini check when Ollama is the active brain). Every failed check carries a
short Hinglish "kaise fix karein" hint. Nothing here ever raises — a check
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
            "ollama_reachable", "Ollama chal raha hai", "fail",
            "Ollama se connect nahi ho paya.",
            "Ollama app kholo, ya terminal me 'ollama serve' chalao. "
            "Agar Ollama install nahi hai toh ollama.com se install karo.",
        )
    if resp.status_code != 200:
        return _check(
            "ollama_reachable", "Ollama chal raha hai", "fail",
            f"Ollama ne jawab diya: HTTP {resp.status_code}.",
            "Ollama restart karo (app band karke dobara kholo).",
        )
    return _check(
        "ollama_reachable", "Ollama chal raha hai", "ok",
        f"Connected: {settings.ollama_url}",
    )


def check_ollama_model(ollama_ok: bool):
    if not ollama_ok:
        return _check(
            "ollama_model", f"Model '{settings.ollama_model}' downloaded hai",
            "skip", "Ollama nahi chal raha, isliye check nahi ho paya.",
        )
    try:
        with httpx.Client(timeout=CHECK_TIMEOUT, trust_env=False) as client:
            resp = client.get(f"{settings.ollama_url}/api/tags")
        names = [m.get("name", "") for m in resp.json().get("models", [])]
    except Exception:  # noqa: BLE001
        return _check(
            "ollama_model", f"Model '{settings.ollama_model}' downloaded hai",
            "fail", "Model list nahi mil payi.",
            "Ollama restart karo, phir Status dobara check karo.",
        )
    wanted = settings.ollama_model
    if wanted in names or f"{wanted}:latest" in names:
        return _check(
            "ollama_model", f"Model '{wanted}' downloaded hai", "ok",
            f"{wanted} ready hai.",
        )
    return _check(
        "ollama_model", f"Model '{wanted}' downloaded hai", "fail",
        "Model download nahi hua.",
        f"Terminal me ye chalao: ollama pull {wanted}  (~1.9 GB, ek baar).",
    )


def check_gemini_key():
    if settings.model_provider != "gemini":
        return _check(
            "gemini_key", "Gemini key set + valid hai", "skip",
            "Abhi Ollama brain chal raha hai — Gemini key zaroori nahi.",
        )
    if not settings.gemini_api_key:
        return _check(
            "gemini_key", "Gemini key set + valid hai", "fail",
            "Gemini key set nahi hai.",
            "Settings (⚙️) me Gemini key daalo — free key aistudio.google.com "
            "se milti hai (card nahi lagta).",
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
            "gemini_key", "Gemini key set + valid hai", "fail",
            "Google se connect nahi ho paya.",
            "Internet check karo, phir Status dobara kholo.",
        )
    elif resp.status_code == 200:
        result = _check(
            "gemini_key", "Gemini key set + valid hai", "ok",
            f"Key valid hai, model: {settings.gemini_model}.",
        )
    elif resp.status_code in (400, 401, 403):
        result = _check(
            "gemini_key", "Gemini key set + valid hai", "fail",
            "Key reject ho gayi (auth fail).",
            "Settings (⚙️) me sahi key daalo — aistudio.google.com se nayi "
            "free key bana sakte ho.",
        )
    else:
        result = _check(
            "gemini_key", "Gemini key set + valid hai", "fail",
            f"Google ne jawab diya: HTTP {resp.status_code}.",
            "Thodi der baad Status dobara kholo.",
        )
    _GEMINI_CACHE["at"] = now
    _GEMINI_CACHE["result"] = result
    return result


def check_git():
    if not shutil.which("git"):
        return _check(
            "git", "Git installed + configured hai", "fail",
            "Git nahi mila.",
            "git-scm.com se Git install karo, phir terminal me apna naam aur "
            "email set karo (neeche wala hint dekho).",
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
            "git", "Git installed + configured hai", "fail",
            "Git config padh nahi paya.",
            "Terminal me 'git config --global user.name \"Tumhara Naam\"' aur "
            "'git config --global user.email \"tum@email.com\"' chalao.",
        )
    if name and email:
        return _check(
            "git", "Git installed + configured hai", "ok",
            f"{name} <{email}>",
        )
    return _check(
        "git", "Git installed + configured hai", "fail",
        "Git hai, lekin naam/email set nahi hai.",
        "Terminal me ye chalao: git config --global user.name \"Tumhara Naam\" "
        "aur git config --global user.email \"tum@email.com\"",
    )


def check_chromium():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _check(
            "chromium", "Playwright Chromium installed hai", "fail",
            "Playwright package nahi mila.",
            "setup dobara chalao (setup.bat ya bash setup.sh).",
        )
    try:
        with sync_playwright() as p:
            exe = Path(p.chromium.executable_path)
    except Exception:  # noqa: BLE001 — executable_path raises when missing
        return _check(
            "chromium", "Playwright Chromium installed hai", "fail",
            "Chromium browser download nahi hua.",
            "Terminal me (venv active) ye chalao: playwright install chromium",
        )
    if exe.exists():
        return _check(
            "chromium", "Playwright Chromium installed hai", "ok",
            "Browser ready hai.",
        )
    return _check(
        "chromium", "Playwright Chromium installed hai", "fail",
        "Chromium browser download nahi hua.",
        "Terminal me (venv active) ye chalao: playwright install chromium",
    )


def check_messaging(platform: str):
    """WhatsApp / Instagram auto-reply readiness. Not configured at all
    is a "skip" (messaging is optional — no setup failure). Partially
    configured is a "fail" with a hint, because the user clearly started
    the setup and something is missing. The ON/OFF state comes from the
    SQLite control table (v0.7) — the user flips it by talking to Satyam
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
        setup_hint = ("MESSAGING_SETUP.md me steps hain: Meta app me WhatsApp "
                      "product add karo, phir chat me bolo 'WhatsApp ke "
                      "messages dekhna' — secure box me token + IDs daal do "
                      "(ya .env me haath se).")
    else:
        enabled = messaging_store.get_platform_enabled("instagram")
        token = settings.instagram_token
        target = settings.instagram_page_id
        target_name = "page ID"
        verify = settings.instagram_verify_token
        secret = settings.instagram_app_secret
        label = "Instagram auto-reply"
        setup_hint = ("MESSAGING_SETUP.md me steps hain: Instagram ko Business "
                      "/Creator banao, Facebook Page se link karo, phir chat "
                      "me bolo 'Instagram ke messages dekhna' — secure box me "
                      "token + IDs daal do (ya .env me haath se).")

    check_id = f"{platform}_autoreply"
    if not enabled:
        return _check(check_id, label, "skip",
                      "Auto-reply band hai — chat me bolo "
                      f"'{platform.capitalize()} ke messages dekhna' toh "
                      "chalu ho jayega.")
    missing = [name for name, v in (("token", token),
                                    (target_name, target),
                                    ("verify token", verify)) if not v]
    if len(missing) == 3:
        return _check(check_id, label, "skip",
                      "Set up nahi hai — chaaho toh MESSAGING_SETUP.md se set karo.")
    if missing:
        return _check(
            check_id, label, "fail",
            f"Adhoora setup hai — ye missing hai: {', '.join(missing)}.",
            setup_hint,
        )
    detail = "Ready hai — aane wale DMs ka jawab apne aap jayega."
    if not secret:
        detail += (" (App secret set nahi hai — webhook signature check nahi "
                   "hoga. Secure box me daal lo, zyada safe rahega.)")
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
            "gmail", "Gmail connected hai", "ok",
            "token.json ready hai — Satyam emails padh sakta hai.",
        )
    if has_client_secret():
        return _check(
            "gmail", "Gmail connected hai", "fail",
            "client_secret.json hai, lekin one-time auth nahi hua.",
            "Terminal me (project folder, venv active) ye chalao: "
            "python -m backend.app.gmail.auth — Google ka consent screen "
            "khulega, ek baar Allow karo. Steps GMAIL_SETUP.md me hain.",
        )
    return _check(
        "gmail", "Gmail connected hai", "skip",
        "Gmail set up nahi hai — chaaho toh GMAIL_SETUP.md se set karo "
        "(emails padhna + email OTP auto-fill ke liye).",
    )


def check_workspace_writable():
    try:
        settings.workspace_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=settings.workspace_dir, delete=True
        ) as f:
            f.write(b"ok")
        return _check(
            "workspace", "Workspace likhne layak hai", "ok",
            str(settings.workspace_dir),
        )
    except Exception as e:  # noqa: BLE001
        return _check(
            "workspace", "Workspace likhne layak hai", "fail",
            f"Workspace me likh nahi paya: {e}",
            "Project folder ki permissions check karo, ya folder ko kisi aur "
            "jagah (jaise Desktop) copy karke chalao.",
        )


# ---------------------------------------------------------------------------
def run_all_checks() -> dict:
    """Run every check. Never raises — a broken check reports 'fail'."""
    checks = []
    try:
        ollama = check_ollama_reachable()
    except Exception:  # noqa: BLE001 — safety net, should not happen
        ollama = _check("ollama_reachable", "Ollama chal raha hai", "fail",
                        "Check hi nahi chal paya.",
                        "Ollama app kholo ya 'ollama serve' chalao.")
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
                                 "Check hi nahi chal paya.",
                                 "Server restart karke dobara try karo."))
    try:
        checks.insert(1, check_ollama_model(ollama_ok))
    except Exception:  # noqa: BLE001
        checks.insert(1, _check("ollama_model", "Ollama model", "fail",
                                "Check hi nahi chal paya.",
                                "Ollama restart karo."))

    failed = [c for c in checks if c["status"] == "fail"]
    return {
        "all_ok": not failed,
        "provider": settings.model_provider,
        "checks": checks,
    }
