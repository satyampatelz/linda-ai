"""Satyam agent — the planner loop.

Flow: user instruction -> LLM plans ONE step (a JSON tool call) -> the tool
runs -> the result goes back to the LLM -> repeat until the LLM says
"finish" or MAX_AGENT_STEPS is reached. Every step is logged live so the
UI can show what the agent is doing.

The LLM speaks JSON only:
  {"thought": "...", "action": "tool_name", "args": {...}}
  {"thought": "...", "action": "finish", "answer": "..."}

External actions (git push/clone, Kaggle submit) pass through the approval
gate — in auto mode (default) they run immediately; in ask mode the loop
pauses for a one-click decision in the UI.
"""
import json
import logging
import re
import threading
import uuid
from datetime import datetime, timezone

from . import brain, memory
from .approvals import EXTERNAL_ACTIONS, approvals
from .config import settings
from .tools import (browser_tool, code_run, files_tool, github_tool,
                    gmail_tool, kaggle_tool, messaging_tool)

logger = logging.getLogger("satyam.agent")

MAX_OBSERVATION_CHARS = 3000
MAX_PARSE_FAILURES = 3

# ---------------------------------------------------------------------------
# Tool registry — the agent only knows the tools listed here.
# ---------------------------------------------------------------------------
TOOL_SPECS = [
    # Files (workspace sandbox)
    {"name": "files_list", "fn": files_tool.files_list,
     "desc": 'List files/folders in the workspace. args: {"path": "rel/path"} (default ".")'},
    {"name": "files_read", "fn": files_tool.files_read,
     "desc": 'Read a text file. args: {"path": "rel/path.txt"}'},
    {"name": "files_write", "fn": files_tool.files_write,
     "desc": 'Write/create a text file (creates folders). args: {"path": "rel/path", "content": "..."}'},
    {"name": "files_mkdir", "fn": files_tool.files_mkdir,
     "desc": 'Create a folder. args: {"path": "rel/path"}'},
    {"name": "files_delete", "fn": files_tool.files_delete,
     "desc": 'Delete a file or folder. args: {"path": "rel/path"}'},
    # Code execution
    {"name": "run_python", "fn": code_run.run_python,
     "desc": 'Run a workspace Python file, get stdout/stderr. args: {"path": "rel/script.py"}'},
    # Git / GitHub
    {"name": "github_init", "fn": github_tool.github_init,
     "desc": 'Init a git repo in a folder. args: {"path": "workspace/rel/path or absolute path"}'},
    {"name": "github_status", "fn": github_tool.github_status,
     "desc": 'git status of a repo. args: {"path": "..."}'},
    {"name": "github_remote_add", "fn": github_tool.github_remote_add,
     "desc": 'Add/update a git remote. args: {"path": "...", "url": "https://github.com/user/repo.git"}'},
    {"name": "github_add_commit", "fn": github_tool.github_add_commit,
     "desc": 'Stage all + commit. args: {"path": "...", "message": "commit message"}'},
    {"name": "github_push", "fn": github_tool.github_push,
     "desc": 'Push to a remote (uses your saved git credentials). args: {"path": "...", "remote": "origin", "branch": "main"}'},
    {"name": "github_clone", "fn": github_tool.github_clone,
     "desc": 'Clone a repo. args: {"url": "https://github.com/...", "path": "local folder"}'},
    # Browser (visible Chromium)
    {"name": "browser_open", "fn": browser_tool.browser_open,
     "desc": 'Open a URL in the visible browser. args: {"url": "https://..."}'},
    {"name": "browser_read", "fn": browser_tool.browser_read,
     "desc": 'Read the current page text + first 30 links. args: {}'},
    {"name": "browser_click", "fn": browser_tool.browser_click,
     "desc": 'Click a CSS selector or text=... args: {"selector": "text=Login"}'},
    {"name": "browser_type", "fn": browser_tool.browser_type,
     "desc": 'Type into a field. args: {"selector": "input[name=q]", "text": "..."}'},
    {"name": "browser_press", "fn": browser_tool.browser_press,
     "desc": 'Press a key. args: {"key": "Enter"}'},
    {"name": "browser_scroll", "fn": browser_tool.browser_scroll,
     "desc": 'Scroll the page down. args: {}'},
    {"name": "browser_screenshot", "fn": browser_tool.browser_screenshot,
     "desc": 'Save a screenshot to workspace/screenshots/. args: {"name": "shot.png"}'},
    {"name": "browser_fill_form", "fn": browser_tool.browser_fill_form,
     "desc": 'Open a page, fill a whole form, submit it. args: {"url": "https://...", "fields": [{"label": "Name", "value": "..."}, {"name": "email", "value": "..."}], "submit": true}'},
    {"name": "browser_fill_otp", "fn": browser_tool.browser_fill_otp,
     "desc": 'Fill the OTP on the current page. Email OTP: args {"sender": "Internshala", "minutes": 10} (reads Gmail). SMS OTP the user just typed in chat: args {"code": "482916"} (fills it directly, never stored).'},
    {"name": "browser_close", "fn": browser_tool.browser_close,
     "desc": 'Close the browser. args: {}'},
    # Gmail (read-only, official Gmail API + OAuth)
    {"name": "read_gmail", "fn": gmail_tool.read_gmail,
     "desc": 'Search/read emails. args: {"query": "from:internshala" or "internship" or "" for newest inbox mail, "max_results": 5}'},
    {"name": "find_otp", "fn": gmail_tool.find_otp,
     "desc": 'Find the OTP code in a recent email from a site/sender. args: {"sender": "Internshala", "minutes": 10}'},
    # Kaggle (official API, user's own kaggle.json)
    {"name": "kaggle_list_competitions", "fn": kaggle_tool.kaggle_list_competitions,
     "desc": 'List Kaggle competitions. args: {"search": "optional term"}'},
    {"name": "kaggle_list_datasets", "fn": kaggle_tool.kaggle_list_datasets,
     "desc": 'List Kaggle datasets. args: {"search": "optional term"}'},
    {"name": "kaggle_download_competition", "fn": kaggle_tool.kaggle_download_competition,
     "desc": 'Download competition data to workspace. args: {"competition": "titanic", "path": "kaggle_data"}'},
    {"name": "kaggle_download_dataset", "fn": kaggle_tool.kaggle_download_dataset,
     "desc": 'Download a dataset to workspace. args: {"dataset": "owner/name", "path": "kaggle_data"}'},
    {"name": "kaggle_submit", "fn": kaggle_tool.kaggle_submit,
     "desc": 'Submit a CSV to a competition. args: {"competition": "titanic", "file": "rel/submission.csv", "message": "note"}'},
    # Memory
    {"name": "memory_remember", "fn": memory.remember,
     "desc": 'Save a fact for later. args: {"key": "github_username", "value": "..."}'},
    {"name": "memory_recall", "fn": lambda key: memory.recall(key) or "(yaad nahi hai)",
     "desc": 'Recall a saved fact. args: {"key": "github_username"}'},
    # Messaging — WhatsApp / Instagram auto-reply, controlled from chat
    {"name": "set_messaging", "fn": messaging_tool.set_messaging,
     "desc": 'Turn WhatsApp/Instagram auto-reply ON or OFF. args: {"platform": "whatsapp" or "instagram", "enabled": true or false}'},
    {"name": "get_messaging_status", "fn": messaging_tool.get_messaging_status,
     "desc": 'Check whether WhatsApp/Instagram auto-reply is ON or OFF and configured. args: {}'},
]

TOOLS = {spec["name"]: spec for spec in TOOL_SPECS}


def _tool_list_text() -> str:
    return "\n".join(f"- {s['name']}: {s['desc']}" for s in TOOL_SPECS)


SYSTEM_PROMPT = f"""You are Satyam, an autonomous personal agent running on the user's own laptop.
You DO tasks, not just talk about them. Plan, use tools, verify results, then report.

HOW YOU WORK — reply with ONLY a JSON object, nothing else, no markdown:
  {{"thought": "short plan for this step", "action": "tool_name", "args": {{...}}}}
When the task is fully done, reply:
  {{"thought": "done because ...", "action": "finish", "answer": "short summary of what was done, with file paths / links"}}

RULES
- One action per reply. Wait for the observation before the next step.
- Never invent tool results — only use what the observation actually says.
- If a tool fails, read the error, fix the cause, and retry differently (max 2 retries per step).
- For multi-part tasks, break them into steps and do them in order.
- File paths for files_write/files_read/run_python are relative to the workspace folder.
- For GitHub: write the code first, then github_init, github_add_commit, github_remote_add (only if the user gave a repo URL), then github_push.
- For browser tasks: browser_open, then browser_read to see the page, then click/type based on what you actually see. If a task names a site (e.g. "Internshala check karo"), first read site-profiles.yaml with files_read — it has plain-word notes (login URL, where things live) for known sites. If a CAPTCHA appears, stop and tell the user in your finish answer — they solve it in the visible browser, then tell you to continue. OTPs are different: EMAIL OTPs — read the code from Gmail (find_otp) and fill it yourself (browser_fill_otp) — never ask the user for an email OTP. SMS OTPs — Gmail me nahi milega, isliye user se chat me code maango (finish answer me bas: "SMS pe aaya OTP bhejo"), browser band mat karo (OTP wala page khula rahega), aur jab user code bheje toh browser_fill_otp me code de ke khud bhar do, phir task continue karo. Code ko kabhi apne jawab me dobara mat likho, aur kabhi memory me save mat karo.
- If the user only asked a question (no task), answer directly with a finish action — no tools needed.
- Keep answers short.
- Reply in the same language and script the user used in their message — from their very first message, no matter what language they start in; default to English when unclear.

MESSAGING (WhatsApp / Instagram auto-reply)
- The user controls WhatsApp/Instagram auto-reply by TALKING to you in chat — there is no Settings UI for it, and tokens/IDs live in .env only (never ask the user to paste a token or secret in chat).
- To START auto-reply on a platform, the user says things like: "ab se Instagram ke messages dekhna", "Instagram ka reply on kar do", "WhatsApp on karo", "start replying to my WhatsApp messages". Call set_messaging with platform "whatsapp" or "instagram" and enabled true.
- To STOP it: "WhatsApp band kar do", "Instagram ka reply band kar do", "stop replying on WhatsApp". Call set_messaging with enabled false.
- To check the status ("WhatsApp reply on hai?"): call get_messaging_status.
- After set_messaging, relay its result as your finish answer in plain words, once — then just do it. If it says a token is missing, tell the user once that a secure box has appeared below in this chat to paste it in — never ask for the token as a chat message, and do not keep asking.
- Once a platform is ON, incoming DMs get replies automatically — never ask the user what to reply to anyone.

GMAIL (read-only — you read mail, never send/delete/modify)
- The user asks things like: "mere Gmail me kya aaya hai?", "Internshala ka mail dikhao", "show me my recent emails", "kya koi naya mail hai?". Call read_gmail (empty query = newest inbox mail; "from:internshala" narrows to a sender). Summarize what matters — sender, subject, the point of the mail.
- If read_gmail says Gmail is not set up, tell the user once in plain words (one-time setup: GMAIL_SETUP.md, run "python -m backend.app.gmail.auth") and stop — do not keep asking.
- OTP: when a site asks for an OTP during a browser task, FIRST check Gmail — call find_otp with the site name ("Internshala"), then browser_fill_otp to fill it. EMAIL OTPs are fully automatic this way — never ask the user for one. If Gmail me koi OTP email nahi mila, it is probably an SMS OTP: finish with ONE short message asking for it ("SMS pe aaya OTP bhejo") and do NOT close the browser — the OTP page stays open in the persistent browser session. When the user replies with the code, fill it yourself with browser_fill_otp and the code (args: {{"code": "482916"}}), then continue the task (click Verify/Submit). If the user's message is just a 4–8 digit code, treat it as the SMS OTP you asked for: check the page with browser_read, fill the code, continue. NEVER repeat the code in your answer, never save it with memory_remember, never write it to a file — use it once for the fill and forget it.

BROWSER — FORMS + GOOGLE SIGN-IN
- The browser keeps a persistent profile: once the user has signed in to Google once in the agent's browser, "Sign in with Google" / "Login with Google" buttons on sites work without re-typing anything — just click them. If Google asks to sign in again, tell the user once to sign in himself in the visible browser (first time only), then continue.
- To fill a form ("ye form bhar do", "is site pe apply kar do"): use browser_fill_form with the page URL and a list of fields — each field needs a "value" and a "label", "name", or "placeholder" to find it. After submitting, browser_read the result page and report what happened (success / error / next step).
- Never invent form values the user did not give you — if a field needs information you do not have, fill what you know and tell the user what is still empty.

YOUR TOOLS
{_tool_list_text()}
"""


# ---------------------------------------------------------------------------
# One-time-code redaction — an SMS OTP the user types in chat is used once
# for the fill and NEVER stored: not in memory, not in the task DB, not in
# logs, not in the step history the UI shows. The LLM still sees the
# original message (it needs the digits to fill the form), but every
# persistence boundary below runs through these helpers first.
# ---------------------------------------------------------------------------
_OTP_DIGITS_RE = re.compile(r"\b\d{4,8}\b")
_BARE_OTP_RE = re.compile(
    r"^\s*(?:otp|code|verification code|ओटीपी)?\s*[:\-]?\s*(\d{4,8})\s*$",
    re.IGNORECASE,
)
_OTP_WORD_RE = re.compile(r"\b(otp|code|ओटीपी)\b", re.IGNORECASE)
_CODE_MASK = "••••••"


def redact_otp_text(text: str) -> str:
    """Mask a one-time code in text that is about to be stored (task
    history, DB log, step result). Only touches messages that ARE
    (essentially) just a code, or that mention otp/code next to a
    4–8 digit run — normal messages with numbers pass through unchanged."""
    if not text:
        return text
    stripped = text.strip()
    if _BARE_OTP_RE.match(stripped) or _OTP_WORD_RE.search(stripped):
        return _OTP_DIGITS_RE.sub(_CODE_MASK, stripped)
    return text


def _redact_args(action: str, args: dict) -> dict:
    """Mask one-time codes in tool args before they are stored or
    logged. Only browser_fill_otp ever carries a code."""
    if action == "browser_fill_otp" and isinstance(args, dict) \
            and "code" in args:
        masked = dict(args)
        masked["code"] = _CODE_MASK
        return masked
    return args


def _redact_step(step: dict) -> dict:
    """Strip one-time codes from a step before it is stored — the UI
    shows steps live, so a code must never appear there."""
    step = dict(step)
    step["args"] = _redact_args(step.get("action", ""), step.get("args") or {})
    if step.get("action") == "finish":
        step["result"] = redact_otp_text(step.get("result") or "")
    return step


# ---------------------------------------------------------------------------
# Task store — in-memory, live state the UI polls.
# ---------------------------------------------------------------------------
class TaskStore:
    def __init__(self):
        self._tasks = {}
        self._stop_requested = set()
        self._lock = threading.Lock()

    def create(self, message: str) -> str:
        task_id = uuid.uuid4().hex[:10]
        with self._lock:
            self._tasks[task_id] = {
                "id": task_id,
                "message": message,
                "status": "running",  # running | waiting_approval | done | error | stopped
                "steps": [],
                "result": None,
                "error": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        return task_id

    def request_stop(self, task_id: str) -> bool:
        """Ask a running task to stop at the next checkpoint. Returns False
        if the task does not exist or is already finished."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task["status"] not in ("running", "waiting_approval"):
                return False
            self._stop_requested.add(task_id)
            return True

    def stop_requested(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._stop_requested

    def stop(self, task_id: str, message: str):
        """Mark a task stopped (called by the agent loop itself)."""
        existed = False
        with self._lock:
            self._stop_requested.discard(task_id)
            if task_id in self._tasks:
                existed = True
                self._tasks[task_id]["status"] = "stopped"
                self._tasks[task_id]["result"] = message
        # The stop message is what the user sees in the chat bubble —
        # save it to the transcript (v0.9: the chat survives reopening).
        if existed:
            _save_agent_message(message)

    def get(self, task_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
            return dict(task) if task else None

    def list_recent(self, limit: int = 20):
        with self._lock:
            tasks = sorted(
                self._tasks.values(),
                key=lambda t: t["created_at"],
                reverse=True,
            )
            return [dict(t) for t in tasks[:limit]]

    def add_step(self, task_id: str, step: dict):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["steps"].append(_redact_step(step))

    def set_status(self, task_id: str, status: str):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = status

    def finish(self, task_id: str, result=None, error=None):
        existed = False
        with self._lock:
            self._stop_requested.discard(task_id)
            if task_id in self._tasks:
                existed = True
                self._tasks[task_id]["status"] = "error" if error else "done"
                self._tasks[task_id]["result"] = result
                self._tasks[task_id]["error"] = error
        # The final reply is what the user sees in the chat bubble —
        # save exactly that text to the transcript (v0.9: the chat
        # survives reopening the app). Errors show as "Error: ..." in
        # the UI, so that is what gets saved.
        if existed:
            _save_agent_message(
                f"Error: {error}" if error else (result or "Done."))


def _save_agent_message(text: str):
    """Save the agent's final reply to the chat transcript. The text is
    redacted first — a one-time code must never be persisted, even if
    the model echoed one back (it is told not to, but this is the
    safety net). Failures here must never break the task itself."""
    try:
        memory.log_message("agent", redact_otp_text(text or ""))
    except Exception:  # noqa: BLE001 — transcript is a bonus, not the task
        logger.warning("Could not save agent reply to chat history",
                       exc_info=True)


task_store = TaskStore()


# ---------------------------------------------------------------------------
# JSON extraction — small local models sometimes wrap JSON in text/fences.
# ---------------------------------------------------------------------------
def extract_json(text: str):
    """Pull the first JSON object out of model output. Returns dict or None."""
    s = text.strip()
    if "```" in s:
        s = re.sub(r"```(?:json)?\s*", "", s)
        s = s.replace("```", "").strip()
    try:
        parsed = json.loads(s)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    # Fall back to the first balanced {...} block.
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(s[start:i + 1])
                    return parsed if isinstance(parsed, dict) else None
                except json.JSONDecodeError:
                    return None
    return None


# ---------------------------------------------------------------------------
# The planner loop — runs in a background thread per task.
# ---------------------------------------------------------------------------
def run_task(task_id: str, user_message: str):
    """Execute one user instruction. Updates task_store as it goes.

    The loop can never hang: every brain call has a timeout, every step is
    bounded by MAX_AGENT_STEPS, a Stop request is honoured at the next
    checkpoint, and any unexpected error finishes the task with a clean
    Hinglish message (full details go to the server log only).
    """
    try:
        _run_task_inner(task_id, user_message)
    except Exception:  # noqa: BLE001 — last-resort safety net
        logger.exception("Unexpected error in task %s", task_id)
        task = task_store.get(task_id)
        if task and task["status"] in ("running", "waiting_approval"):
            task_store.finish(
                task_id,
                error="Kuch unexpected ho gaya — task ruk gaya. "
                      "Dobara try karo; agar baar-baar ho toh server restart karo.",
            )
            # The task message is logged to the DB — redact any OTP code
            # the user may have typed in it.
            memory.log_task(task_id, redact_otp_text(user_message), "", "error")


def _stop_now(task_id: str, user_message: str) -> bool:
    """If a stop was requested, finish the task as stopped. Returns True
    if the loop should exit."""
    if not task_store.stop_requested(task_id):
        return False
    msg = "Task rok diya gaya — ab tak ke steps upar dikh rahe hain."
    task_store.stop(task_id, msg)
    memory.log_task(task_id, redact_otp_text(user_message), msg, "stopped")
    return True


def _run_task_inner(task_id: str, user_message: str):
    # What gets logged to the DB: the user's message with any OTP code
    # masked (the LLM still gets the original — it needs the digits).
    log_message = redact_otp_text(user_message)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    parse_failures = 0

    for step_no in range(1, settings.max_steps + 1):
        if _stop_now(task_id, user_message):
            return
        try:
            raw = brain.chat(messages)
        except brain.BrainError as e:
            task_store.finish(task_id, error=str(e))
            memory.log_task(task_id, log_message, "", "error")
            return
        except Exception:  # noqa: BLE001 — never leave a task stuck
            logger.exception("Brain call failed in task %s", task_id)
            task_store.finish(
                task_id,
                error="Model se baat karte waqt achanak error aaya. "
                      "Dobara try karo; agar baar-baar ho toh Status panel me "
                      "brain check karo.",
            )
            memory.log_task(task_id, log_message, "", "error")
            return
        if _stop_now(task_id, user_message):
            return

        parsed = extract_json(raw)
        if not parsed or "action" not in parsed:
            parse_failures += 1
            if parse_failures >= MAX_PARSE_FAILURES:
                # Model won't do JSON — treat its raw text as the answer.
                task_store.finish(task_id, result=raw.strip())
                memory.log_task(task_id, log_message,
                                redact_otp_text(raw.strip()), "done")
                return
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": ("Observation: tumhara jawab valid JSON nahi tha. "
                            "Reply with ONLY a JSON object like "
                            '{"thought": "...", "action": "tool_name", "args": {...}} '
                            "or {\"action\": \"finish\", \"answer\": \"...\"}."),
            })
            continue
        parse_failures = 0

        thought = parsed.get("thought", "")
        action = parsed.get("action", "")
        args = parsed.get("args") or {}

        if action == "finish":
            answer = parsed.get("answer", "Ho gaya.")
            task_store.add_step(task_id, {
                "n": step_no, "thought": thought,
                "action": "finish", "args": {}, "result": answer,
            })
            task_store.finish(task_id, result=answer)
            memory.log_task(task_id, log_message,
                            redact_otp_text(answer), "done")
            return

        spec = TOOLS.get(action)
        if spec is None:
            observation = (
                f"Unknown tool '{action}'. Available tools: "
                + ", ".join(TOOLS)
            )
            task_store.add_step(task_id, {
                "n": step_no, "thought": thought, "action": action,
                "args": args, "result": observation,
            })
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        # Approval gate for external actions (instant in auto mode).
        if action in EXTERNAL_ACTIONS:
            detail = f"{action} {json.dumps(args, ensure_ascii=False)}"
            task_store.set_status(task_id, "waiting_approval")
            allowed = approvals.request(task_id, action, detail)
            task_store.set_status(task_id, "running")
            if _stop_now(task_id, user_message):
                return
            if not allowed:
                observation = (
                    "User ne is action ko approve nahi kiya. "
                    "Bina iske aage badho, ya finish me user ko batao."
                )
                task_store.add_step(task_id, {
                    "n": step_no, "thought": thought, "action": action,
                    "args": args, "result": "Rejected (no approval)",
                })
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                continue

        # Run the tool.
        try:
            result = spec["fn"](**args)
            result = "" if result is None else str(result)
        except TypeError as e:
            logger.warning("Bad tool call %s %s: %s",
                           action, _redact_args(action, args), e)
            result = f"Tool call galat tha ({action}). Args dobara check karo."
        except Exception as e:  # noqa: BLE001 — tool errors become observations
            logger.warning("Tool %s failed: %s", action, e)
            result = f"Tool error ({action}): {e}"

        task_store.add_step(task_id, {
            "n": step_no, "thought": thought, "action": action,
            "args": args, "result": result[:MAX_OBSERVATION_CHARS],
        })
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": f"Observation: {result[:MAX_OBSERVATION_CHARS]}",
        })
        if _stop_now(task_id, user_message):
            return

    # Ran out of steps.
    answer = (
        f"Task {settings.max_steps} steps me poora nahi hua. "
        "Ab tak ke steps upar dikh rahe hain — mujhe 'aage badho' bolo toh continue karunga."
    )
    task_store.finish(task_id, result=answer)
    memory.log_task(task_id, log_message, answer, "stopped")
