"""Linda configuration — everything comes from environment variables / .env.

No secrets are ever hardcoded here. The Settings screen in the app writes
changes to .env and applies them live (no restart needed for any setting
the UI offers). .env itself is git-ignored; copy .env.example to .env if
you prefer editing the file by hand.
"""
import os
from pathlib import Path

from dotenv import load_dotenv, set_key

# Project root: linda-ai/ (this file lives at backend/app/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Where settings live. LINDA_ENV_FILE lets tests point at a temp file.
ENV_PATH = Path(os.getenv("LINDA_ENV_FILE", str(BASE_DIR / ".env")))


def _heal_env_encoding() -> None:
    """Re-encode a legacy-encoded .env to UTF-8, if needed.

    Older builds on Windows could write .env in the locale codec
    (cp1252) — Path.write_text() without an encoding does that — and
    python-dotenv reads UTF-8, so load_dotenv would raise
    UnicodeDecodeError and the app would not start. Heal once, quietly;
    never block startup on this.
    """
    try:
        if ENV_PATH.exists():
            ENV_PATH.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = ENV_PATH.read_text(encoding="cp1252")
            ENV_PATH.write_text(text, encoding="utf-8")
        except Exception:  # noqa: BLE001 — startup must not die on this
            pass


_heal_env_encoding()
load_dotenv(ENV_PATH)

# Keys the Settings UI may change, with their .env names.
# NOTE: WhatsApp/Instagram tokens and IDs are deliberately NOT here
# (v0.7) — they come only from .env, and auto-reply is switched ON/OFF
# by talking to Linda in chat, never from Settings.
SETTABLE_KEYS = {
    "model_provider": "MODEL_PROVIDER",
    "ollama_model": "OLLAMA_MODEL",
    "gemini_api_key": "GEMINI_API_KEY",
    "gemini_model": "GEMINI_MODEL",
    "approval_mode": "APPROVAL_MODE",
    "browser_headless": "BROWSER_HEADLESS",
    "max_agent_steps": "MAX_AGENT_STEPS",
}


def _int_env(name: str, default: int) -> int:
    """Read an int from the environment, falling back safely on junk."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def mask_secret(value: str) -> str:
    """Mask a secret for display: 'AIza••••••••3f9a'. Empty stays empty."""
    if not value:
        return ""
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}{'•' * 8}{value[-4:]}"


def _default_data_dir() -> Path:
    """Where chat history + task history live when DATA_DIR isn't set.

    An existing app-folder database wins (older installs keep their
    history exactly where it is). Otherwise use a stable per-user home
    (~/.linda/data) so re-downloading the app into a fresh folder
    doesn't look like a brand-new user with no chat history.
    """
    legacy = BASE_DIR / "data"
    if (legacy / "satyam.db").exists():
        return legacy
    return Path.home() / ".linda" / "data"


class Settings:
    app_name = "Linda"
    app_version = "0.10.3"

    # Class-level defaults (also used before __init__ runs). Live values
    # always live on the instance — refresh() updates instance attributes,
    # so direct assignment (tests, one-off overrides) and refresh() can
    # never disagree about which value is current.
    model_provider = "ollama"
    ollama_url = "http://127.0.0.1:11434"
    ollama_model = "qwen2.5:3b"
    gemini_api_key = ""
    gemini_model = "gemini-2.5-flash"
    approval_mode = "auto"
    browser_headless = False
    max_steps = 15
    host = "127.0.0.1"
    port = 8000
    # Server API token (env API_TOKEN). Empty = no auth (laptop use).
    # Set on the cloud server so strangers can't use YOUR agent — this is
    # not a restriction on the agent itself, only a lock on the front door.
    # Never settable from the Settings UI (that would defeat the point).
    api_token = ""
    # WhatsApp / Instagram auto-reply (v0.6) — official Meta APIs only.
    # Tokens/IDs are env-only (v0.7): they come from .env, never from the
    # Settings UI, never from chat. The ON/OFF switch lives in SQLite
    # (messaging.store) and is flipped by chat commands, not by .env.
    whatsapp_token = ""
    whatsapp_phone_number_id = ""
    whatsapp_verify_token = ""
    whatsapp_app_secret = ""
    instagram_token = ""
    instagram_page_id = ""
    instagram_verify_token = ""
    instagram_app_secret = ""

    def __init__(self):
        # --- Brain / model router ---------------------------------------
        # "ollama" = local model on your own laptop (free, private, no key).
        # "gemini" = Google Gemini free-tier API (needs GEMINI_API_KEY, no card).
        self.refresh()
        # --- Paths (server-level, not in the Settings UI) ---------------
        self.workspace_dir = Path(
            os.getenv("WORKSPACE_DIR", str(BASE_DIR / "workspace"))
        ).resolve()
        self.data_dir = Path(
            os.getenv("DATA_DIR", str(_default_data_dir()))
        ).resolve()
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = _int_env("PORT", 8000)

    def refresh(self):
        """Re-read .env and update all settings live. No restart needed.

        The .env file is the source of truth for the Settings UI, so it
        overrides process env vars here. Keys absent from .env keep their
        current (environment) values.
        """
        load_dotenv(ENV_PATH, override=True)
        self.model_provider = os.getenv("MODEL_PROVIDER", "ollama").strip().lower()
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        # Free-tier model (verified Nov 2026). If Google ever rejects this id,
        # try gemini-3.8-flash or gemini-3.5-flash-lite — both also have a free tier.
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        # "auto" (default): every action runs immediately, no prompts.
        # "ask": external actions (git push/clone, Kaggle submit) pause and
        # wait for a one-click Approve/Reject in the UI. Nothing else is
        # ever blocked.
        self.approval_mode = os.getenv("APPROVAL_MODE", "auto").strip().lower()
        # Headed (visible) by default so you can watch the agent work.
        self.browser_headless = (
            os.getenv("BROWSER_HEADLESS", "false").strip().lower() == "true"
        )
        self.max_steps = _int_env("MAX_AGENT_STEPS", 15)
        # Server API token — env-only, never in the Settings UI.
        self.api_token = os.getenv("API_TOKEN", "").strip()
        # WhatsApp / Instagram auto-reply (v0.6). Tokens/secrets are
        # env-only (v0.7) — read from .env, never settable from the UI.
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN", "").strip()
        self.whatsapp_phone_number_id = os.getenv(
            "WHATSAPP_PHONE_NUMBER_ID", "").strip()
        self.whatsapp_verify_token = os.getenv(
            "WHATSAPP_VERIFY_TOKEN", "").strip()
        self.whatsapp_app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip()
        self.instagram_token = os.getenv("INSTAGRAM_TOKEN", "").strip()
        self.instagram_page_id = os.getenv("INSTAGRAM_PAGE_ID", "").strip()
        self.instagram_verify_token = os.getenv(
            "INSTAGRAM_VERIFY_TOKEN", "").strip()
        self.instagram_app_secret = os.getenv("INSTAGRAM_APP_SECRET", "").strip()

    def public_dict(self) -> dict:
        """Settings safe to send to the UI — secrets are masked.

        No messaging fields (v0.7): messaging is controlled from chat,
        and its tokens live in .env only — the Settings UI shows neither.
        """
        return {
            "model_provider": self.model_provider,
            "ollama_url": self.ollama_url,
            "ollama_model": self.ollama_model,
            "gemini_api_key_masked": mask_secret(self.gemini_api_key),
            "gemini_key_set": bool(self.gemini_api_key),
            "gemini_model": self.gemini_model,
            "approval_mode": self.approval_mode,
            "browser_headless": self.browser_headless,
            "max_agent_steps": self.max_steps,
        }


settings = Settings()
settings.workspace_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)


def _ensure_env_file(header: str) -> None:
    """Make sure .env exists and is readable as UTF-8.

    On Windows, Path.write_text() without an encoding uses the locale
    codec (cp1252), which turns the em dash in the header into a byte
    python-dotenv (UTF-8) cannot read back — the Settings save then
    fails with "problem writing the .env file". Always write UTF-8,
    and heal a .env an older build already wrote in a legacy encoding
    by re-encoding it once.
    """
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ENV_PATH.exists():
        ENV_PATH.write_text(header, encoding="utf-8")
        return
    _heal_env_encoding()


def save_settings(values: dict) -> None:
    """Persist validated settings to .env (creating it if needed) and
    apply them live. Only keys in SETTABLE_KEYS are written; everything
    else in .env (comments, HOST/PORT, etc.) is left untouched.

    `values` uses the UI field names (e.g. "model_provider"); a value of
    None means "leave this key alone". An empty string for gemini_api_key
    clears the key.
    """
    _ensure_env_file("# Linda settings — created by the Settings screen.\n")
    for field, env_key in SETTABLE_KEYS.items():
        if field not in values or values[field] is None:
            continue
        value = values[field]
        if isinstance(value, bool):
            value = "true" if value else "false"
        set_key(str(ENV_PATH), env_key, str(value))
    settings.refresh()


# --- Messaging credentials (v0.7, secure box) -------------------------------
# Field names the secure-box endpoint accepts, mapped to .env keys.
# These are deliberately NOT in SETTABLE_KEYS: the Settings UI can never
# write them — only the in-chat secure box (or editing .env by hand).
MESSAGING_CREDENTIAL_KEYS = {
    "whatsapp": {
        "token": "WHATSAPP_TOKEN",
        "target_id": "WHATSAPP_PHONE_NUMBER_ID",
        "verify_token": "WHATSAPP_VERIFY_TOKEN",
        "app_secret": "WHATSAPP_APP_SECRET",
    },
    "instagram": {
        "token": "INSTAGRAM_TOKEN",
        "target_id": "INSTAGRAM_PAGE_ID",
        "verify_token": "INSTAGRAM_VERIFY_TOKEN",
        "app_secret": "INSTAGRAM_APP_SECRET",
    },
}


def save_messaging_credentials(platform: str, values: dict) -> list:
    """Persist messaging credentials from the secure box to .env and
    apply them live. `values` maps field names ("token", "target_id",
    "verify_token", "app_secret") to values; empty/None values are
    skipped (existing values stay). Returns the list of fields actually
    saved. Values are NEVER logged — only field names leave this
    function."""
    mapping = MESSAGING_CREDENTIAL_KEYS.get(platform, {})
    _ensure_env_file("# Linda settings — created by the secure box.\n")
    saved = []
    for field, env_key in mapping.items():
        value = values.get(field)
        if value is None:
            continue
        value = str(value).strip()
        if not value:
            continue
        set_key(str(ENV_PATH), env_key, value)
        saved.append(field)
    settings.refresh()
    return saved
