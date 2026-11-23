"""Satyam server — FastAPI backend + single-page chat UI.

One command to run (from the project root, venv active):
    python run.py

Then open http://127.0.0.1:8000 — the chat UI is served by this same server,
no separate frontend build step needed.

API:
  GET  /health                  backend + model status (always public)
  GET  /health/detailed         setup checks (Ollama, Gemini, git, browser…)
  GET  /config                  active provider/model/approval mode (no secrets)
  GET  /settings                current settings (Gemini key masked)
  POST /settings                save settings to .env, applied live, no restart
  POST /chat        {"message"} start a task, returns {"task_id"}
  GET  /chat/history        saved chat transcript (v0.9 — the chat
                            survives closing and reopening the app)
  GET  /tasks/{id}              live task state (steps + pending approval)
  GET  /tasks                   recent tasks
  POST /tasks/{id}/approve {"approve": true|false}   (ask mode only)
  POST /tasks/{id}/stop         ask a running task to stop
  GET  /memory                  saved facts
  GET  /messaging/pending       outstanding secure-box credential requests
  POST /messaging/credentials   save a messaging token/ID from the secure box
  GET  /webhook/whatsapp        Meta's WhatsApp webhook verification
  POST /webhook/whatsapp        inbound WhatsApp messages (auto-reply)
  GET  /webhook/instagram       Meta's Instagram webhook verification
  POST /webhook/instagram       inbound Instagram DMs (auto-reply)

API TOKEN (cloud servers only): set API_TOKEN in .env and every API
endpoint except /health requires `Authorization: Bearer <token>`. This
only stops strangers from using YOUR server — it never restricts what
the agent itself does. When API_TOKEN is empty (laptop use), everything
works exactly as before, no token needed.

The /webhook/* endpoints are deliberately NOT behind the API token —
Meta's servers call them and can't carry it. Their auth is Meta's own:
the verify token (GET handshake) and the HMAC-SHA256 app-secret
signature (POST body).

Every error the UI can see is a short Hinglish message — full tracebacks
go to the server log only, never to the user.
"""
import logging
import secrets
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from . import brain, health, memory
from .agent import redact_otp_text, run_task, task_store
from .approvals import approvals
from .config import (MESSAGING_CREDENTIAL_KEYS, mask_secret,
                     save_messaging_credentials, save_settings, settings)
from .messaging import store as messaging_store
from .messaging import webhooks as messaging_webhooks
from .tools import messaging_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("satyam.server")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Satyam", version=settings.app_version)

# Local app: the UI and API live on the same origin, but CORS open makes
# phone-on-same-WiFi access painless too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Paths that need the API token when one is set. /health stays public so
# uptime checks and the Oracle keep-alive cron work without a token. The
# static UI files are public too — the UI is useless without the token,
# because every API call behind it is protected.
_PROTECTED_PREFIXES = ("/chat", "/tasks", "/settings", "/memory",
                       "/health/detailed", "/config", "/messaging")


class _ApiTokenMiddleware(BaseHTTPMiddleware):
    """Bearer-token gate, active only when API_TOKEN is set in .env.

    This is a lock on the server's front door, not a rule on the agent:
    with the right token, everything works exactly as it does on the
    laptop — no approvals, no blocks, no restrictions on what the agent
    does. With no token configured, this middleware does nothing at all.
    """

    async def dispatch(self, request, call_next):
        token = settings.api_token
        path = request.url.path
        if token and any(path.startswith(p) for p in _PROTECTED_PREFIXES):
            auth = request.headers.get("Authorization", "")
            ok = auth.startswith("Bearer ") and secrets.compare_digest(
                auth[len("Bearer "):], token
            )
            if not ok:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "API token galat ya missing hai — "
                                       "Settings me sahi server token daalo."},
                )
        return await call_next(request)


app.add_middleware(_ApiTokenMiddleware)

# Meta webhooks (WhatsApp + Instagram auto-reply) — public by design,
# authenticated by Meta's verify token + app-secret signature.
app.include_router(messaging_webhooks.router)


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError):
    # Turn FastAPI's technical 422 into one plain Hinglish message.
    problems = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err.get("loc", []) if p != "body")
        msg = err.get("msg", "")
        # Our own validators already write Hinglish ("Value error, <text>");
        # keep that text verbatim.
        if err.get("type") == "value_error" and msg.startswith("Value error, "):
            problems.append(msg[len("Value error, "):])
        elif field == "max_agent_steps":
            problems.append("Max steps 1 se 50 ke beech hona chahiye.")
        elif field:
            problems.append(f"'{field}' galat hai.")
    detail = " ".join(problems) or "Input galat hai — values dobara check karo."
    return JSONResponse(status_code=400, content={"detail": detail})


@app.exception_handler(Exception)
async def _unhandled_error(request: Request, exc: Exception):
    # Full details server-side only; the user gets one clean Hinglish line.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Server me achanak error aaya. Dobara try karo; "
                           "agar baar-baar ho toh server restart karo."},
    )


class ChatRequest(BaseModel):
    message: str


class ApproveRequest(BaseModel):
    approve: bool


class SettingsRequest(BaseModel):
    """Partial update — only the fields present are changed. Sending
    gemini_api_key as "" clears the stored key; omitting it keeps it."""

    model_provider: str | None = None
    ollama_model: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    approval_mode: str | None = None
    browser_headless: bool | None = None
    max_agent_steps: int | None = Field(default=None, ge=1, le=50)
    # No messaging fields (v0.7): WhatsApp/Instagram tokens live in .env
    # only, and auto-reply is switched ON/OFF by talking to Satyam in
    # chat — Settings has nothing to do with messaging any more.

    @field_validator("model_provider")
    @classmethod
    def _check_provider(cls, v):
        if v is not None and v.strip().lower() not in ("ollama", "gemini"):
            raise ValueError("model_provider 'ollama' ya 'gemini' hona chahiye.")
        return v.strip().lower() if v is not None else None

    @field_validator("approval_mode")
    @classmethod
    def _check_approval(cls, v):
        if v is not None and v.strip().lower() not in ("auto", "ask"):
            raise ValueError("approval_mode 'auto' ya 'ask' hona chahiye.")
        return v.strip().lower() if v is not None else None

    @field_validator("ollama_model", "gemini_model")
    @classmethod
    def _check_model_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v or len(v) > 120:
                raise ValueError("Model ka naam khaali ya bahut lamba hai.")
            if any(ch.isspace() for ch in v):
                raise ValueError("Model ke naam me space nahi ho sakta.")
        return v

    @field_validator("gemini_api_key")
    @classmethod
    def _check_key(cls, v):
        if v is not None:
            v = v.strip()
            if v and (len(v) < 10 or any(ch.isspace() for ch in v)):
                raise ValueError("Gemini key galat lag rahi hai — poori key "
                                 "paste karo (aistudio.google.com se milti hai).")
        return v


class MessagingCredentialsRequest(BaseModel):
    """One secure-box submission: the platform + the credential fields
    the user filled in. Only non-empty values are saved; anything
    omitted keeps its current value. Values are never logged and never
    echoed back in full — the response carries masked previews only.
    Validation lives in the endpoint (not Pydantic validators) so bad
    values come back as a 400 with a plain Hinglish message, like
    /settings does, instead of a 422 with a list."""

    platform: str
    values: dict = {}


@app.on_event("startup")
def _startup():
    memory.init_db()
    messaging_store.init_db()


@app.get("/health")
def health_basic():
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.app_version,
        "provider": settings.model_provider,
        "model": (
            settings.gemini_model
            if settings.model_provider == "gemini"
            else settings.ollama_model
        ),
        "brain": brain.describe(),
        "approval_mode": settings.approval_mode,
        "browser_headless": settings.browser_headless,
    }


@app.get("/health/detailed")
def health_detailed():
    return health.run_all_checks()


@app.get("/config")
def config():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "provider": settings.model_provider,
        "brain": brain.describe(),
        "approval_mode": settings.approval_mode,
        "browser_headless": settings.browser_headless,
        "workspace": str(settings.workspace_dir),
    }


@app.get("/settings")
def get_settings():
    # The Gemini key is masked here — the full key is never sent to the UI.
    return settings.public_dict()


@app.post("/settings")
def update_settings(req: SettingsRequest):
    values = req.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="Badalne ko kuch nahi mila.")
    try:
        save_settings(values)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to save settings")
        raise HTTPException(
            status_code=500,
            detail="Settings save nahi ho payi — .env file likhne me problem hai.",
        )
    logger.info("Settings updated: %s", sorted(values))
    return {
        "ok": True,
        "message": "Settings save ho gaye — bina restart ke lagu ho gaye.",
        "settings": settings.public_dict(),
    }


@app.post("/chat")
def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message khaali hai.")
    # The task list stores the message — mask any one-time code in it
    # (e.g. an SMS OTP the user just typed). The running task still gets
    # the original message: the agent needs the digits to fill the form.
    task_id = task_store.create(redact_otp_text(message))
    # The chat transcript (v0.9): the user's message is saved so the
    # chat survives closing and reopening the app. The agent's reply
    # is saved by the agent loop when the task finishes (agent.py).
    # Redacted first — a one-time code is never persisted.
    try:
        memory.log_message("user", redact_otp_text(message))
    except Exception:  # noqa: BLE001 — transcript is a bonus, not the task
        logger.warning("Could not save user message to chat history",
                       exc_info=True)
    thread = threading.Thread(
        target=run_task, args=(task_id, message), daemon=True
    )
    thread.start()
    return {"task_id": task_id}


@app.get("/chat/history")
def chat_history():
    """The saved chat transcript, oldest first — what the UI renders
    when the app opens, so the user gets their same chat back (v0.9).
    Only user messages + agent replies, never tool internals; capped
    at the newest 200 messages."""
    return {"messages": memory.recent_messages()}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nahi mila.")
    task["pending_approval"] = approvals.pending_for_task(task_id)
    return task


@app.get("/tasks")
def list_tasks():
    return {"tasks": task_store.list_recent()}


@app.post("/tasks/{task_id}/approve")
def approve_task(task_id: str, req: ApproveRequest):
    pending = approvals.pending_for_task(task_id)
    if not pending:
        raise HTTPException(
            status_code=404, detail="Is task ke liye koi pending approval nahi hai."
        )
    approvals.decide(pending["id"], req.approve)
    return {"ok": True, "approved": req.approve}


@app.post("/tasks/{task_id}/stop")
def stop_task(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nahi mila.")
    if task["status"] not in ("running", "waiting_approval"):
        raise HTTPException(
            status_code=400,
            detail="Ye task pehle se khatam ho chuka hai — rokne ko kuch nahi hai.",
        )
    # Wake the loop up if it is sitting on an approval, then flag the stop.
    approvals.cancel_for_task(task_id)
    task_store.request_stop(task_id)
    return {"ok": True, "message": "Task roka ja raha hai — current step "
                                   "khatam hote hi ruk jayega."}


@app.get("/memory")
def list_memory():
    return {"memories": [{"key": k, "value": v} for k, v in memory.list_memories()]}


@app.get("/messaging/pending")
def messaging_pending():
    """Outstanding secure-box credential requests — what the chat UI
    shows a masked input card for. Recomputed live: a field that got
    filled (secure box or .env by hand) drops out, and a fully
    satisfied request is cleared. Only field NAMES leave the server."""
    pending = []
    for req in messaging_store.get_pending_credentials():
        platform = req["platform"]
        still = [f for f in req["fields"]
                 if f in messaging_tool.missing_fields(platform)]
        if still:
            pending.append({"platform": platform, "fields": still})
        else:
            messaging_store.clear_pending_credential(platform)
    return {"pending": pending}


@app.post("/messaging/credentials")
def save_messaging_credentials_endpoint(req: MessagingCredentialsRequest):
    """Save messaging credentials from the in-chat secure box. Values go
    to .env (same pattern as the Gemini key) and apply live. The moment
    a platform has its token + target id, auto-reply switches ON by
    itself — the user pastes once and it just starts. The response
    never contains a full secret, only masked previews."""
    platform = (req.platform or "").strip().lower()
    if platform not in ("whatsapp", "instagram"):
        raise HTTPException(
            status_code=400,
            detail="Platform 'whatsapp' ya 'instagram' hona chahiye.",
        )
    if not isinstance(req.values, dict):
        raise HTTPException(status_code=400,
                            detail="Values ek object hona chahiye.")
    for field, value in req.values.items():
        if field not in ("token", "target_id", "verify_token", "app_secret"):
            raise HTTPException(
                status_code=400, detail=f"Unknown credential field: {field}.")
        if value is None:
            continue
        value = str(value).strip()
        if not value:
            continue
        if field == "target_id":
            if len(value) > 120 or any(ch.isspace() for ch in value):
                raise HTTPException(
                    status_code=400,
                    detail="ID galat lag raha hai — Meta dashboard se "
                           "poora ID copy-paste karo.")
        elif len(value) < 10 or any(ch.isspace() for ch in value):
            raise HTTPException(
                status_code=400,
                detail="Token/secret galat lag raha hai — poora value "
                       "paste karo (Meta dashboard se milta hai).")
    req.platform = platform
    values = {k: str(v).strip() for k, v in (req.values or {}).items()
              if v is not None and str(v).strip()}
    # Only fields this platform actually has (unknown keys are dropped).
    allowed = MESSAGING_CREDENTIAL_KEYS.get(req.platform, {})
    values = {k: v for k, v in values.items() if k in allowed}
    if not values:
        raise HTTPException(
            status_code=400,
            detail="Kuch daalo toh — saare fields khaali hain.",
        )
    try:
        saved = save_messaging_credentials(req.platform, values)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to save messaging credentials")
        raise HTTPException(
            status_code=500,
            detail="Save nahi ho paya — .env file likhne me problem hai.",
        )
    # Field names only in the log — never values.
    logger.info("Messaging credentials saved: %s %s", req.platform, saved)
    result = messaging_tool.complete_setup(req.platform)
    name = "WhatsApp" if req.platform == "whatsapp" else "Instagram"
    if result["enabled"] and not result["still_missing"]:
        message = (f"Ho gaya — {name} ka auto-reply chalu ho gaya. Ab se "
                   f"aane wale messages ka reply main khud dunga.")
    elif result["enabled"]:
        if "verify_token" in result["still_missing"]:
            message = (f"Save ho gaya aur {name} ka auto-reply chalu ho gaya "
                       f"— bas verify token baki hai, wo bhi daal do toh "
                       f"webhook chalega (warna message aayega hi nahi).")
        else:
            message = (f"Save ho gaya aur {name} ka auto-reply chalu ho gaya. "
                       f"(App secret abhi baki hai — optional hai, webhook "
                       f"signature check ke liye hota hai.)")
    else:
        missing = ", ".join(result["still_missing"]) or "kuch fields"
        message = (f"Save ho gaya — abhi bhi {missing} baki hai. Wo bhi "
                   f"daal do, phir auto-reply chalu ho jayega.")
    return {
        "ok": True,
        "platform": req.platform,
        "saved": saved,
        "masked": {f: mask_secret(values[f]) for f in saved},
        "enabled": result["enabled"],
        "still_missing": result["still_missing"],
        "message": message,
    }


# Serve the chat UI (index.html, app.js, style.css, PWA files) at /.
# Mounted last so API routes above take precedence.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
