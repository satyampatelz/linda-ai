"""Smoke tests for Linda v0.11.0.

Run (venv active, from the project root):
    python tests/smoke_test.py

Covers, without touching any real service:
  * memory (write/read/list/task log)
  * approvals in auto mode AND ask mode (approve + reject)
  * files tool, including sandbox-escape rejection
  * github tool against a LOCAL temp repo (init/commit, no remote push)
  * the agent planner loop with a stubbed brain (no LLM needed)
  * task stop (running task stops cleanly at the next checkpoint)
  * brain error handling when Ollama is unreachable
  * brain retry: one retry on a transient 500, none on a permanent 404
  * kaggle tool's no-credentials error (no real API call)
  * browser tool headless launch (skipped if Chromium is not installed)
  * settings endpoints: read, write + live apply, key masking, validation
  * health endpoint: check structure + Hinglish hints on failures
  * API token auth: protected endpoints need Bearer when set, open when
    unset, /health always public
  * PWA voice wiring (v0.4): mic button + auto-speak toggle in the UI,
    Web Speech APIs in app.js, service-worker cache bumped, /health
    reports the new version
  * v0.5 interface redesign: demo chips removed, all icons are custom
    hand-drawn SVG paths (no Material Icons, no icon fonts, no emoji),
    in the PWA and the Flutter app
  * v0.6 messaging (official Meta APIs, mock payloads only — no live
    Meta calls): webhook verification handshake, HMAC-SHA256 signature
    check, webhook parsers (text kept, statuses/echoes/images ignored),
    auto-reply engine with a stub brain + stub sender (reply, dedupe,
    24h window, rate limit, platform off, unconfigured), end-to-end
    webhook POST incl. double-delivery dedupe
  * v0.7 chat-controlled messaging + in-chat secure box: set_messaging
    enables/disables + persists (SQLite), missing-token blocker with a
    pending secure-box request, Settings UI has no messaging fields
    anywhere, POST /messaging/credentials saves to .env (masked only,
    auto-enables when complete, 400 on bad values), GET
    /messaging/pending lists outstanding requests, secure-box UI wired
    in the PWA + Flutter chat
  * v0.8 Gmail + browser upgrades (stubbed Gmail service — no live
    Google calls): message search/parsing (plain + multipart + HTML
    fallback), OTP extraction (several formats, no-match, year
    rejection), OTP time-window (fresh found, stale ignored),
    not-configured behaviour (clear setup message, no crash), Gmail
    tools + system prompt + Internshala site profile, browser
    persistent profile (cookie survives close/relaunch), form filling
    against a local test page, OTP auto-fill against a local test page
    (single field + multi-box, code never echoed back)
  * v0.8.1 SMS OTP ask-and-fill: a user-provided code fills the OTP
    field on a local test page (single field + multi-box, Gmail never
    consulted, page still open across the ask gap), the code is never
    stored anywhere (redaction helper, step args, task store, DB log),
    and the system prompt asks the user for the SMS code instead of
    telling him to fill it himself
  * v0.8.2 welcome + composer: the welcome message is English in both
    the PWA and the Flutter app (no fixed Hinglish greeting — the
    brain auto-adapts to the user's language from their first
    message), and the PWA composer snaps back to a single line
    immediately after sending (Playwright, against a live server)
  * v0.8.3 clean chat screen: the welcome bubble is the greeting ONLY
    (no capabilities paragraph, no first-time hints), the composer
    placeholder and all chat-visible toasts/hints are short clean
    English, and the model subtitle is gone from the header (brain
    info lives in the Status panel) — in both the PWA and Flutter
  * v0.9 desktop icon + chat history: the chat transcript is saved
    in SQLite (user messages + agent replies, oldest first, capped
    at 200 with pruning), GET /chat/history serves it (API-token
    protected like the other /chat routes), one-time codes are never
    persisted in it (checked through the real POST /chat + task
    finish paths), both apps load it on start and render it below
    the welcome bubble (Playwright check against a live server),
    and the Windows desktop launcher is shipped and well-formed
    (Linda.bat reads server.txt, starts the local server only for
    local URLs, waits on /health, opens an app-mode window with a
    Chrome/Edge fallback; create-shortcut.ps1 builds the Desktop
    shortcut with the multi-size S-logo .ico + -AutoStart flag)

  * v0.11 in-chat browser panel with Take control: control state
    transitions, live_state shape, panel input forwarding (click/type/
    key/scroll into a stub page), /browser/state + /browser/control +
    /browser/input endpoints (input rejected with 409 while the agent
    has control), and the panel wiring in the PWA + Flutter app

Exit code 0 = all passed (skips are fine, they print SKIP).
"""
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Point all runtime state at temp dirs BEFORE importing the app.
TMP = Path(tempfile.mkdtemp(prefix="linda-test-"))
os.environ["DATA_DIR"] = str(TMP / "data")
os.environ["WORKSPACE_DIR"] = str(TMP / "workspace")
os.environ["APPROVAL_MODE"] = "auto"
os.environ["BROWSER_HEADLESS"] = "true"
# Settings writes go to a temp .env, never the project's real one.
os.environ["LINDA_ENV_FILE"] = str(TMP / ".env")
# Fake key (test placeholder, not a real credential) for the masking test.
os.environ["GEMINI_API_KEY"] = "AIzaFakeTestKey1234567890abcdef"

from backend.app import agent, brain, memory  # noqa: E402
from backend.app.approvals import ApprovalManager  # noqa: E402
from backend.app.tools import files_tool, github_tool  # noqa: E402

PASSED, FAILED, SKIPPED = [], [], []


class _Skipped(Exception):
    pass


def check(name, fn):
    try:
        fn()
    except _Skipped as e:
        SKIPPED.append(name)
        print(f"SKIP  {name}: {e}")
    except Exception as e:  # noqa: BLE001
        FAILED.append(name)
        print(f"FAIL  {name}: {e}")
    else:
        PASSED.append(name)
        print(f"PASS  {name}")


def skip(name, reason):
    raise _Skipped(reason)


# ---------------------------------------------------------------------------
def test_memory():
    memory.remember("github_username", "satyampatelz")
    assert memory.recall("github_username") == "satyampatelz"
    assert memory.recall("no_such_key") is None
    assert ("github_username", "satyampatelz") in memory.list_memories()
    memory.log_task("t1", "test task", "ok", "done")
    assert any(t["id"] == "t1" for t in memory.recent_tasks())


def test_approvals_auto():
    mgr = ApprovalManager(mode="auto")
    assert mgr.request("task1", "github_push", "push to origin") is True


def test_approvals_ask_approve():
    mgr = ApprovalManager(mode="ask")

    def decide_later():
        time.sleep(0.3)
        pending = mgr.pending_for_task("task1")
        assert pending is not None
        assert mgr.decide(pending["id"], True) is True

    threading.Thread(target=decide_later, daemon=True).start()
    assert mgr.request("task1", "github_push", "push to origin", timeout=5) is True


def test_approvals_ask_reject():
    mgr = ApprovalManager(mode="ask")

    def decide_later():
        time.sleep(0.3)
        pending = mgr.pending_for_task("task1")
        assert mgr.decide(pending["id"], False) is True

    threading.Thread(target=decide_later, daemon=True).start()
    assert mgr.request("task1", "kaggle_submit", "submit csv", timeout=5) is False


def test_files():
    result = files_tool.files_write("a/b.txt", "hello world")
    assert "Wrote" in result and "b.txt" in result, result
    assert files_tool.files_read("a/b.txt") == "hello world"
    assert "b.txt" in files_tool.files_list("a")
    files_tool.files_mkdir("a/sub")
    assert "sub" in files_tool.files_list("a")
    assert "delete" in files_tool.files_delete("a/b.txt")
    try:
        files_tool.files_write("../escape.txt", "x")
    except ValueError:
        pass  # expected: sandbox escape refused
    else:
        raise AssertionError("sandbox escape was NOT refused")
    assert not (TMP / "escape.txt").exists()


def test_github_local():
    repo = TMP / "repo"
    github_tool.github_init(str(repo))
    subprocess.run(["git", "config", "user.email", "test@test.local"],
                   cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"],
                   cwd=repo, check=True)
    (repo / "hello.py").write_text("print('hi')\n")
    out = github_tool.github_add_commit(str(repo), "first commit")
    assert "first commit" in out or "1 file changed" in out
    log = subprocess.run(["git", "log", "--oneline"], cwd=repo,
                         capture_output=True, text=True, check=True).stdout
    assert "first commit" in log
    status = github_tool.github_status(str(repo))
    assert "hello.py" not in status  # working tree clean after commit


def test_agent_loop_with_stub_brain():
    script = [
        '{"thought": "test file likhta hoon", "action": "files_write",'
        ' "args": {"path": "stub/hello.txt", "content": "hello from stub"}}',
        '{"thought": "ho gaya", "action": "finish",'
        ' "answer": "Stub task complete."}',
    ]
    calls = {"n": 0}

    def stub_chat(messages, temperature=0.2, timeout=180):
        calls["n"] += 1
        return script[min(calls["n"] - 1, len(script) - 1)]

    original = brain.chat
    brain.chat = stub_chat
    try:
        task_id = agent.task_store.create("stub task")
        agent.run_task(task_id, "stub task: ek file likho")
        task = agent.task_store.get(task_id)
        assert task["status"] == "done", task
        assert task["result"] == "Stub task complete."
        assert (TMP / "workspace" / "stub" / "hello.txt").read_text() == "hello from stub"
        assert len(task["steps"]) == 2
    finally:
        brain.chat = original


def test_brain_ollama_unreachable():
    from backend.app.config import settings
    original_url = settings.ollama_url
    original_provider = settings.model_provider
    settings.model_provider = "ollama"
    settings.ollama_url = "http://127.0.0.1:9"  # closed port
    try:
        brain.chat([{"role": "user", "content": "hi"}], timeout=10)
    except brain.BrainError as e:
        assert "Ollama" in str(e), str(e)
    else:
        raise AssertionError("BrainError was NOT raised for unreachable Ollama")
    finally:
        settings.ollama_url = original_url
        settings.model_provider = original_provider


def test_kaggle_no_creds():
    kaggle_dir = Path.home() / ".kaggle"
    if ((kaggle_dir / "kaggle.json").exists()
            or (kaggle_dir / "access_token").exists()
            or os.getenv("KAGGLE_API_TOKEN")):
        skip("kaggle_no_creds", "real Kaggle credentials exist on this machine")
        return
    from backend.app.tools import kaggle_tool
    try:
        kaggle_tool.kaggle_list_competitions()
    except RuntimeError as e:
        assert "Kaggle" in str(e), str(e)
    else:
        raise AssertionError("kaggle tool did not raise without credentials")


def test_browser_headless():
    from backend.app.tools import browser_tool
    try:
        browser_tool.browser_open("data:text/html,<h1>Hi Linda</h1><p>test page</p>")
        text = browser_tool.browser_read()
        assert "Hi Linda" in text, text[:200]
        browser_tool.browser_close()
    except Exception as e:  # noqa: BLE001
        if "Executable doesn't exist" in str(e) or "launch" in str(e).lower():
            skip("browser_headless", f"Chromium not installed/launchable here: {e}")
            return
        raise


# --- v0.3: API token auth (cloud servers only) ---
def test_system_prompt_auto_language():
    """The agent auto-adapts its reply language: same language/script as
    the user's message, English default. No language setting exists."""
    from backend.app.agent import SYSTEM_PROMPT
    assert "same language and script the user used" in SYSTEM_PROMPT
    assert "from their very first message" in SYSTEM_PROMPT
    assert "default to English when unclear" in SYSTEM_PROMPT
    # And there is genuinely no language option in Settings.
    from backend.app.config import SETTABLE_KEYS, settings
    assert "language" not in SETTABLE_KEYS
    assert "language" not in settings.public_dict()


def test_agent_tool_discipline():
    """v0.10.3: the agent must not invent files or repos — the prompt
    forces write-before-run, bans invented repo URLs, tells it to stop
    after two failed approaches, and mirrors the user's language;
    run_python's missing-file error tells it to write the file first;
    git never prompts for credentials."""
    from backend.app.agent import SYSTEM_PROMPT
    for want in ("Never run a file you have not written or seen",
                 "Never invent a repo URL",
                 "If two different approaches to the same step both fail",
                 "Hinglish in, Hinglish out"):
        assert want in SYSTEM_PROMPT, f"prompt missing: {want}"
    from backend.app.tools import code_run
    try:
        code_run.run_python("definitely_not_a_real_file_xyz.py")
    except FileNotFoundError as e:
        assert "Write it first with files_write" in str(e), str(e)
    else:
        raise AssertionError("run_python did not raise on a missing file")
    src = (ROOT / "backend" / "app" / "tools"
           / "github_tool.py").read_text()
    assert "GIT_TERMINAL_PROMPT" in src, "git calls must be non-interactive"


def test_api_token_auth():
    """Token set -> protected endpoints need Bearer, /health stays open.
    Token unset -> everything open, exactly like before."""
    from backend.app.config import settings
    client = _client()
    original = settings.api_token
    try:
        # Baseline: no token configured — everything open.
        settings.api_token = ""
        assert client.get("/health").status_code == 200
        assert client.get("/settings").status_code == 200
        assert client.get("/memory").status_code == 200
        assert client.get("/tasks").status_code == 200

        # Token set: /health still public, the rest need the token.
        settings.api_token = "test-token-abc123"
        assert client.get("/health").status_code == 200
        for path in ("/settings", "/memory", "/tasks", "/config",
                     "/health/detailed"):
            resp = client.get(path)
            assert resp.status_code == 401, f"{path} -> {resp.status_code}"
            assert "token" in resp.json()["detail"].lower(), resp.text
        resp = client.post("/chat", json={"message": "hi"})
        assert resp.status_code == 401, resp.text
        # Wrong token is still rejected.
        resp = client.get("/settings",
                          headers={"Authorization": "Bearer nope-wrong"})
        assert resp.status_code == 401, resp.text
        # Right token: everything works.
        headers = {"Authorization": "Bearer test-token-abc123"}
        assert client.get("/settings", headers=headers).status_code == 200
        assert client.get("/memory", headers=headers).status_code == 200
        assert client.get("/tasks", headers=headers).status_code == 200
        assert client.get("/health/detailed", headers=headers).status_code == 200
        # Static UI files stay public (the UI is useless without the token).
        assert client.get("/").status_code == 200
        assert client.get("/style.css").status_code == 200
    finally:
        settings.api_token = original


# --- v0.4: PWA voice wiring (static checks — no mic needed here) ---
# --- v0.5: interface redesign guards (chips gone, custom icons only) ---
def test_pwa_voice_wiring():
    """The v0.4 voice UI is wired into the shipped PWA: mic button +
    listening hint + auto-speak toggle in index.html, Web Speech APIs
    in app.js, service-worker cache bumped so installed PWAs pick it
    up, and /health reports 0.8.3. Plus the v0.5 redesign guards: the
    demo chips are gone, and every icon is a custom hand-drawn SVG
    path — no Material Icons, no icon fonts, no emoji anywhere."""
    static = ROOT / "backend" / "static"
    html = (static / "index.html").read_text()
    for want in ('id="micBtn"', 'id="listenHint"', 'id="setAutoSpeak"'):
        assert want in html, f"index.html missing {want}"
    js = (static / "app.js").read_text()
    for want in ("SpeechRecognition", "speechSynthesis",
                 "Listening…", "autoSpeakEnabled"):
        assert want in js, f"app.js missing {want}"
    sw = (static / "sw.js").read_text()
    assert "linda-shell-v22" in sw, "service worker cache not bumped to v22"
    # The Flutter app declares the voice packages.
    pubspec = (ROOT / "mobile_app" / "pubspec.yaml").read_text()
    assert "speech_to_text:" in pubspec, "pubspec missing speech_to_text"
    assert "flutter_tts:" in pubspec, "pubspec missing flutter_tts"
    manifest = (ROOT / "mobile_app" / "android" / "app" / "src" / "main"
                / "AndroidManifest.xml").read_text()
    assert "RECORD_AUDIO" in manifest, "AndroidManifest missing RECORD_AUDIO"
    # /health reports the new version.
    client = _client()
    resp = client.get("/health")
    assert resp.status_code == 200, resp.text
    assert resp.json()["version"] == "0.11.0", resp.text

    # --- v0.5: demo chips removed (PWA + Flutter) ---
    for gone in ("demoChips", 'class="chip"', "DemoChips", "_DemoChips"):
        assert gone not in html, f"index.html still has {gone}"
        assert gone not in js, f"app.js still has {gone}"
    dart = "".join(
        p.read_text() for p in (ROOT / "mobile_app" / "lib").rglob("*.dart")
    )
    assert "_DemoChips" not in dart, "Flutter still has _DemoChips"

    # --- v0.5: no emoji / old glyph icons in the UI ---
    css = (static / "style.css").read_text()
    for ch in ("👋", "🐙", "🌐", "🔊", "⚙️", "👇", "➤", "■", "✕", "⚠"):
        assert ch not in html, f"index.html still has {ch!r}"
        assert ch not in js, f"app.js still has {ch!r}"
        assert ch not in css, f"style.css still has {ch!r}"
        assert ch not in dart, f"Flutter lib still has {ch!r}"

    # --- v0.5: no Material icon paths / Material Icons anywhere ---
    for gone in ("M12 14c1.66", "M3 9v6h4l5 5V4"):  # old Material mic/speaker
        assert gone not in html, f"index.html still has Material path {gone}"
        assert gone not in js, f"app.js still has Material path {gone}"
    assert "Icons." not in dart, "Flutter lib still uses Material Icons.*"
    assert "LindaGradientIcon" not in dart, "old gradient-icon widget left"

    # --- v0.5: the custom icon set is present in both apps ---
    # PWA inlines the orbit-mic ring + the speaker EQ bars.
    assert "A8.6 7 -18" in html, "index.html missing the custom orbit-mic"
    assert 'x="17.9" y="7.6"' in js, "app.js missing the custom speaker bars"
    # Flutter ships the same paths as SVG assets + renders them.
    icons_dir = ROOT / "mobile_app" / "assets" / "icons"
    for name in ("mic", "speaker", "send", "stop", "gear", "close", "pulse",
                 "chat", "tasks", "list", "refresh", "check", "error", "skip",
                 "lock"):  # lock added in v0.7 for the secure-box card
        f = icons_dir / f"{name}.svg"
        assert f.is_file(), f"missing Flutter icon asset {f}"
        assert "<svg" in f.read_text(), f"{f} is not an SVG"
    assert "flutter_svg:" in pubspec, "pubspec missing flutter_svg"
    assert "LindaIcon" in dart, "Flutter LindaIcon widget missing"
    assert "assets/icons/" in pubspec, "pubspec missing icons asset dir"


# --- v0.2: settings + health endpoints (FastAPI TestClient, in-process) ---
def _client():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)


def test_health_endpoint():
    client = _client()
    resp = client.get("/health/detailed")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "checks" in data and "all_ok" in data
    by_id = {c["id"]: c for c in data["checks"]}
    for want in ("ollama_reachable", "ollama_model", "gemini_key",
                 "git", "chromium", "workspace"):
        assert want in by_id, f"missing check {want}: {list(by_id)}"
    for c in data["checks"]:
        assert c["status"] in ("ok", "fail", "skip"), c
        assert c["label"] and isinstance(c["label"], str)
        if c["status"] == "fail":
            assert c["hint"], f"failed check {c['id']} has no fix hint"
    # Known ground truths in this VM: no Ollama, workspace is writable.
    assert by_id["ollama_reachable"]["status"] == "fail", by_id["ollama_reachable"]
    assert by_id["workspace"]["status"] == "ok", by_id["workspace"]
    assert data["all_ok"] is False  # Ollama is down, so not everything is ok


def test_settings_masking():
    from backend.app.config import settings
    client = _client()
    resp = client.get("/settings")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # The full key must never appear anywhere in the response.
    assert settings.gemini_api_key, "test setup: fake key missing"
    assert settings.gemini_api_key not in resp.text, "FULL KEY LEAKED in /settings"
    assert "gemini_api_key" not in data, "raw key field present in /settings"
    masked = data["gemini_api_key_masked"]
    assert masked.startswith("AIza") and masked.endswith("cdef"), masked
    assert "•" in masked, masked
    assert data["gemini_key_set"] is True


def test_settings_write_and_validate():
    from backend.app.config import settings
    client = _client()
    env_file = Path(os.environ["LINDA_ENV_FILE"])

    # Valid write: provider + approval + steps, applied live, persisted.
    resp = client.post("/settings", json={
        "model_provider": "gemini",
        "approval_mode": "ask",
        "max_agent_steps": 7,
        "browser_headless": False,
    })
    assert resp.status_code == 200, resp.text
    assert settings.model_provider == "gemini"
    assert settings.approval_mode == "ask"
    assert settings.max_steps == 7
    assert settings.browser_headless is False
    assert env_file.exists()
    from dotenv import dotenv_values
    saved = dotenv_values(str(env_file))
    assert saved.get("MODEL_PROVIDER") == "gemini", saved
    assert saved.get("APPROVAL_MODE") == "ask", saved
    assert saved.get("MAX_AGENT_STEPS") == "7", saved

    # Key update via API is stored (masked on read, never echoed).
    resp = client.post("/settings", json={
        "gemini_api_key": "AIzaAnotherFakeKey999988887777",
    })
    assert resp.status_code == 200, resp.text
    assert settings.gemini_api_key == "AIzaAnotherFakeKey999988887777"
    assert "AIzaAnotherFakeKey999988887777" not in client.get("/settings").text

    # Restore the test baseline (ollama/auto/15/headless) for later tests.
    resp = client.post("/settings", json={
        "model_provider": "ollama",
        "approval_mode": "auto",
        "max_agent_steps": 15,
        "browser_headless": True,
        "gemini_api_key": "AIzaFakeTestKey1234567890abcdef",
    })
    assert resp.status_code == 200, resp.text
    assert settings.model_provider == "ollama"
    assert settings.approval_mode == "auto"

    # Validation: each bad value is a 400 with an English message.
    for bad in ({"model_provider": "claude"},
                {"approval_mode": "maybe"},
                {"max_agent_steps": 99},
                {"max_agent_steps": 0},
                {"gemini_api_key": "short"},
                {"ollama_model": "has space"}):
        resp = client.post("/settings", json=bad)
        assert resp.status_code == 400, f"{bad} -> {resp.status_code} {resp.text}"
        assert resp.json()["detail"], resp.text


def test_task_stop():
    client = _client()
    step1_done = threading.Event()
    release = threading.Event()
    calls = {"n": 0}

    def stub_chat(messages, temperature=0.2, timeout=180):
        calls["n"] += 1
        if calls["n"] == 1:
            step1_done.set()
            return ('{"thought": "t", "action": "files_write", '
                    '"args": {"path": "stop/x.txt", "content": "x"}}')
        release.wait(timeout=15)
        return '{"thought": "t", "action": "finish", "answer": "done"}'

    original = brain.chat
    brain.chat = stub_chat
    try:
        resp = client.post("/chat", json={"message": "stop test task"})
        assert resp.status_code == 200, resp.text
        task_id = resp.json()["task_id"]
        assert step1_done.wait(timeout=10), "agent never started step 1"
        time.sleep(0.5)  # let the loop reach step 2 (blocked in the brain call)
        resp = client.post(f"/tasks/{task_id}/stop")
        assert resp.status_code == 200, resp.text
        release.set()
        task = None
        for _ in range(50):
            task = client.get(f"/tasks/{task_id}").json()
            if task["status"] in ("stopped", "done", "error"):
                break
            time.sleep(0.2)
        assert task is not None and task["status"] == "stopped", task
        assert "Task stopped" in (task["result"] or ""), task
        # Stopping an already-finished task is a clean 400, not a crash.
        resp = client.post(f"/tasks/{task_id}/stop")
        assert resp.status_code == 400, resp.text
        # Unknown task id is a clean 404.
        assert client.post("/tasks/nope123/stop").status_code == 404
    finally:
        brain.chat = original
        release.set()


def test_brain_retry():
    import json as _json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from backend.app.config import settings

    state = {"n": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            state["n"] += 1
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            if state["n"] == 1:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"boom")
                return
            body = _json.dumps({"message": {"content": "retry-ok"}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    orig_url, orig_provider = settings.ollama_url, settings.model_provider
    settings.model_provider = "ollama"
    settings.ollama_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        # Transient 500: retried once, then succeeds.
        out = brain.chat([{"role": "user", "content": "hi"}], timeout=10)
        assert out == "retry-ok", out
        assert state["n"] == 2, state
    finally:
        settings.ollama_url, settings.model_provider = orig_url, orig_provider
        server.shutdown()


def test_brain_no_retry_on_permanent_error():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from backend.app.config import settings

    state = {"n": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            state["n"] += 1
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    orig_url, orig_provider = settings.ollama_url, settings.model_provider
    settings.model_provider = "ollama"
    settings.ollama_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        try:
            brain.chat([{"role": "user", "content": "hi"}], timeout=10)
        except brain.BrainError as e:
            assert "not found" in str(e), str(e)
        else:
            raise AssertionError("BrainError was NOT raised for 404")
        # Permanent error: exactly one call, no retry.
        assert state["n"] == 1, state
    finally:
        settings.ollama_url, settings.model_provider = orig_url, orig_provider
        server.shutdown()


# --- Gemini empty replies + browser live view (27 Nov fixes) ---
def test_gemini_reply_extraction():
    """Gemini 200-responses come in shapes the old code crashed on:
    thought parts first (Gemini 3 thinking models), no candidates,
    safety blocks. _gemini_reply_text must handle all of them — an
    unparseable reply used to kill the whole task mid-way."""
    f = brain._gemini_reply_text
    text, problem = f({"candidates": [{"content": {"parts": [{"text": "hello"}]}}]})
    assert (text, problem) == ("hello", None), (text, problem)
    # Thought part first: reply text is in the later part, thought excluded.
    text, problem = f({"candidates": [{"content": {"parts": [
        {"thought": True, "text": "thinking out loud"},
        {"text": "the answer"},
    ]}}]})
    assert (text, problem) == ("the answer", None), (text, problem)
    # Multi-part text joins.
    text, _ = f({"candidates": [{"content": {"parts": [{"text": "a"}, {"text": "b"}]}}]})
    assert text == "ab", text
    # No candidates at all -> empty (retryable).
    text, problem = f({})
    assert text is None and problem == "empty", (text, problem)
    # Prompt blocked by the safety filter -> blocked (not retryable).
    text, problem = f({"promptFeedback": {"blockReason": "SAFETY"}})
    assert text is None and problem.startswith("blocked"), (text, problem)
    # Candidate stopped for SAFETY with no parts -> blocked.
    text, problem = f({"candidates": [{"finishReason": "SAFETY"}]})
    assert text is None and problem.startswith("blocked"), (text, problem)
    # Thinking model spent its budget on thought parts -> empty, with the
    # finish reason named so the cause is visible in the error/log.
    text, problem = f({"candidates": [{
        "finishReason": "MAX_TOKENS",
        "content": {"parts": [{"thought": True, "text": "long thinking..."}]},
    }]})
    assert text is None, (text, problem)
    assert problem == "empty (finishReason: MAX_TOKENS)", problem


def test_gemini_empty_reply_retried():
    """A 200 with an empty body (free-tier glitch) is retried once inside
    _chat_gemini instead of killing the task — the bug that stopped the
    IITM-login task right after the browser opened the page."""
    import json as _json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from backend.app.config import settings

    state = {"n": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            state["n"] += 1
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            if state["n"] == 1:
                body = b"{}"  # 200 but no candidates — the empty reply
            else:
                body = _json.dumps({"candidates": [
                    {"content": {"parts": [{"text": "gemini-ok"}]}}
                ]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    orig = (brain.GEMINI_API_URL, settings.model_provider,
            settings.gemini_api_key, settings.gemini_model)
    brain.GEMINI_API_URL = f"http://127.0.0.1:{server.server_address[1]}"
    settings.model_provider = "gemini"
    settings.gemini_api_key = "test-key"
    settings.gemini_model = "gemini-test-model"
    try:
        out = brain.chat([{"role": "user", "content": "hi"}], timeout=10)
        assert out == "gemini-ok", out
        assert state["n"] == 2, state  # empty once, retried, then answered
    finally:
        (brain.GEMINI_API_URL, settings.model_provider,
         settings.gemini_api_key, settings.gemini_model) = orig
        server.shutdown()


def test_gemini_empty_reply_gives_up_cleanly():
    """If Gemini keeps returning empty replies, the task fails with a
    clear transient BrainError (after retries) — never a crash."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from backend.app.config import settings

    state = {"n": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            state["n"] += 1
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            body = b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    orig = (brain.GEMINI_API_URL, settings.model_provider,
            settings.gemini_api_key, settings.gemini_model)
    brain.GEMINI_API_URL = f"http://127.0.0.1:{server.server_address[1]}"
    settings.model_provider = "gemini"
    settings.gemini_api_key = "test-key"
    settings.gemini_model = "gemini-test-model"
    try:
        try:
            brain.chat([{"role": "user", "content": "hi"}], timeout=10)
        except brain.BrainError as e:
            assert "empty" in str(e), str(e)
            assert "every model" in str(e), str(e)
            assert e.transient, "empty-reply error should be transient"
        else:
            raise AssertionError("BrainError was NOT raised for empty replies")
        # Per _chat_gemini call: 3 candidate models x 2 tries each (plain
        # prompt, then nudged prompt) = 6; brain.chat retries the whole
        # call once for transient errors -> 12 POSTs before giving up.
        assert state["n"] == 12, state
    finally:
        (brain.GEMINI_API_URL, settings.model_provider,
         settings.gemini_api_key, settings.gemini_model) = orig
        server.shutdown()


def test_browser_live_view():
    """The in-chat browser live view: live_shot_url() is silent when no
    browser is open, and /browser/shot serves the latest screenshot
    (404 until the first browser step captures one)."""
    from backend.app.config import settings
    from backend.app.tools import browser_tool

    browser_tool.browser_close()
    assert browser_tool.live_shot_url() == ""

    client = _client()
    shots = settings.workspace_dir / "screenshots"
    live = shots / "live.png"
    shots.mkdir(parents=True, exist_ok=True)
    backup = live.read_bytes() if live.exists() else None
    try:
        if live.exists():
            live.unlink()
        resp = client.get("/browser/shot")
        assert resp.status_code == 404, resp.text
        live.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        resp = client.get("/browser/shot")
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith("image/png")
        assert resp.content.startswith(b"\x89PNG")
    finally:
        if backup is None:
            live.unlink(missing_ok=True)
        else:
            live.write_bytes(backup)


def test_browser_tool_arg_aliases():
    """Small models guess arg names ("link" for "url"). The browser tool
    wrappers accept the common aliases and, when a required arg is truly
    missing, raise a ValueError that tells the model the correct usage —
    instead of a bare TypeError that wastes the step."""
    from backend.app.tools import browser_tool

    for fn, want in ((browser_tool.browser_open, "url"),
                     (browser_tool.browser_click, "selector"),
                     (browser_tool.browser_type, "selector"),
                     (browser_tool.browser_press, "key")):
        try:
            fn()
        except ValueError as e:
            assert want in str(e), (fn.__name__, str(e))
        else:
            raise AssertionError(f"{fn.__name__}() should need args")


def test_pwa_browser_live_wiring():
    """The browser live view is wired into the shipped PWA + Flutter app:
    live card + lightbox in index.html, updateBrowserLive in app.js,
    styles in style.css, and the Flutter step card shows the shot."""
    static = ROOT / "backend" / "static"
    html = (static / "index.html").read_text()
    for want in ('id="browserLive"', 'id="browserLiveImg"', 'id="shotLightbox"'):
        assert want in html, f"index.html missing {want}"
    js = (static / "app.js").read_text()
    assert "updateBrowserLive" in js, "app.js missing updateBrowserLive"
    assert "steps[j].shot" in js, "app.js does not read step shots"
    css = (static / "style.css").read_text()
    assert ".browser-live" in css, "style.css missing .browser-live"
    dart = "".join(
        p.read_text() for p in (ROOT / "mobile_app" / "lib").rglob("*.dart")
    )
    assert "fetchShot" in dart, "Flutter missing fetchShot"
    assert "step.shot" in dart, "Flutter step card does not show the shot"


# --- v0.11: in-chat browser panel with Take control ---
class _FakeMouse:
    def __init__(self, calls):
        self.calls = calls

    def click(self, x, y):
        self.calls.append(("click", x, y))

    def wheel(self, dx, dy):
        self.calls.append(("wheel", dx, dy))


class _FakeKeyboard:
    def __init__(self, calls):
        self.calls = calls

    def type(self, text):
        self.calls.append(("type", text))

    def press(self, key):
        self.calls.append(("press", key))


class _FakePage:
    """Minimal stand-in for a Playwright page (panel input tests) —
    records mouse/keyboard calls, no real browser needed."""

    def __init__(self):
        self.calls = []
        self.mouse = _FakeMouse(self.calls)
        self.keyboard = _FakeKeyboard(self.calls)
        self.url = "https://example.com/login"

    def title(self):
        return "Example Login"

    def wait_for_timeout(self, ms):
        pass

    def screenshot(self, path=None):
        Path(path).write_bytes(b"\x89PNG\r\n\x1a\nfake")


def test_browser_control_state():
    """Take control / give back flips the flag, and live_state() has the
    panel's shape (open/url/title/user_controlled) with no browser open."""
    from backend.app.tools import browser_tool

    session = browser_tool.BrowserSession()
    assert session.is_user_controlled() is False
    state = session.live_state()
    assert set(state) == {"open", "url", "title", "user_controlled"}, state
    assert state["open"] is False and state["url"] == "" and state["title"] == ""
    assert state["user_controlled"] is False

    state = session.take_control()
    assert session.is_user_controlled() is True
    assert state["user_controlled"] is True

    state = session.release_control()
    assert session.is_user_controlled() is False
    assert state["user_controlled"] is False


def test_browser_user_input_forwarding():
    """Panel input (click/type/key/scroll) reaches the page in the
    1280x800 viewport space, and live_state reports the open page."""
    from backend.app.config import settings
    from backend.app.tools import browser_tool

    shots = settings.workspace_dir / "screenshots"
    live = shots / "live.png"
    shots.mkdir(parents=True, exist_ok=True)
    backup = live.read_bytes() if live.exists() else None
    try:
        session = browser_tool.BrowserSession()
        fake = _FakePage()
        session._page = fake

        session.user_click(100, 200)
        session.user_type("hello")
        session.user_key("Enter")
        session.user_scroll(300)
        assert ("click", 100.0, 200.0) in fake.calls, fake.calls
        assert ("type", "hello") in fake.calls, fake.calls
        assert ("press", "Enter") in fake.calls, fake.calls
        assert ("wheel", 0, 300.0) in fake.calls, fake.calls

        state = session.live_state()
        assert state["open"] is True
        assert state["url"] == "https://example.com/login"
        assert state["title"] == "Example Login"

        # The module-level dispatcher routes by type and rejects junk.
        browser_tool.browser._page = fake
        try:
            browser_tool.user_input("click", x=5, y=6)
            assert ("click", 5.0, 6.0) in fake.calls, fake.calls
            try:
                browser_tool.user_input("teleport")
            except ValueError:
                pass
            else:
                raise AssertionError("user_input should reject unknown types")
        finally:
            browser_tool.browser._page = None
    finally:
        if backup is None:
            live.unlink(missing_ok=True)
        else:
            live.write_bytes(backup)


def test_browser_panel_endpoints():
    """/browser/state shape, /browser/control take+release, and
    /browser/input rejected (409) while the agent has control."""
    from backend.app.tools import browser_tool

    browser_tool.browser_close()
    client = _client()
    fake = _FakePage()
    try:
        resp = client.get("/browser/state")
        assert resp.status_code == 200, resp.text
        state = resp.json()
        assert set(state) == {"open", "url", "title", "user_controlled"}, state
        assert state["user_controlled"] is False

        # Input without control -> 409, and nothing reaches the page.
        browser_tool.browser._page = fake
        resp = client.post("/browser/input",
                           json={"type": "click", "x": 10, "y": 20})
        assert resp.status_code == 409, resp.text
        assert fake.calls == [], fake.calls

        # Take control -> input is forwarded.
        resp = client.post("/browser/control", json={"action": "take"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["user_controlled"] is True
        resp = client.post("/browser/input",
                           json={"type": "click", "x": 10, "y": 20})
        assert resp.status_code == 200, resp.text
        assert ("click", 10.0, 20.0) in fake.calls, fake.calls
        resp = client.post("/browser/input",
                           json={"type": "type", "text": "hi"})
        assert resp.status_code == 200, resp.text
        assert ("type", "hi") in fake.calls, fake.calls

        # Give back -> input rejected again.
        resp = client.post("/browser/control", json={"action": "release"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["user_controlled"] is False
        resp = client.post("/browser/input", json={"type": "key", "key": "Enter"})
        assert resp.status_code == 409, resp.text

        # Bad action -> 400 with a plain message.
        resp = client.post("/browser/control", json={"action": "steal"})
        assert resp.status_code == 400, resp.text
    finally:
        browser_tool.browser_close()


def test_pwa_browser_panel_wiring():
    """The interactive panel is wired into the shipped PWA + Flutter
    app: URL bar, Take control button and typing row in index.html,
    state/control/input calls in app.js, control glow in style.css,
    and the Flutter panel with the same endpoints."""
    static = ROOT / "backend" / "static"
    html = (static / "index.html").read_text()
    for want in ('id="browserLiveUrl"', 'id="browserLiveStatus"',
                 'id="browserControlBtn"', 'id="browserTypeRow"',
                 "Take control"):
        assert want in html, f"index.html missing {want}"
    js = (static / "app.js").read_text()
    for want in ("/browser/state", "/browser/control", "/browser/input",
                 "Give back to Linda", "You have control"):
        assert want in js, f"app.js missing {want}"
    css = (static / "style.css").read_text()
    assert ".browser-live.controlled" in css, "style.css missing control glow"
    dart = "".join(
        p.read_text() for p in (ROOT / "mobile_app" / "lib").rglob("*.dart")
    )
    for want in ("BrowserState", "browserControl", "browserInput",
                 "Take control", "Give back to Linda"):
        assert want in dart, f"Flutter missing {want}"


# --- v0.6: messaging (official Meta APIs, mock payloads only) ---
def test_messaging_webhook_verification():
    """Meta's GET handshake: correct verify token -> challenge echoed
    as plain text; wrong token / wrong mode / no token configured
    -> 403."""
    from backend.app.config import settings
    client = _client()
    orig_wa = settings.whatsapp_verify_token
    orig_ig = settings.instagram_verify_token
    try:
        settings.whatsapp_verify_token = "test-verify-token-wa"
        settings.instagram_verify_token = "test-verify-token-ig"
        resp = client.get("/webhook/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token-wa",
            "hub.challenge": "CHALLENGE123",
        })
        assert resp.status_code == 200 and resp.text == "CHALLENGE123", resp.text
        resp = client.get("/webhook/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token-ig",
            "hub.challenge": "IGCHALLENGE9",
        })
        assert resp.status_code == 200 and resp.text == "IGCHALLENGE9", resp.text
        # Wrong token -> 403.
        resp = client.get("/webhook/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "nope-wrong",
            "hub.challenge": "CHALLENGE123",
        })
        assert resp.status_code == 403, resp.text
        # Wrong mode -> 403.
        resp = client.get("/webhook/whatsapp", params={
            "hub.mode": "unsubscribe",
            "hub.verify_token": "test-verify-token-wa",
            "hub.challenge": "CHALLENGE123",
        })
        assert resp.status_code == 403, resp.text
        # No verify token configured -> 403 (can't verify without one).
        settings.whatsapp_verify_token = ""
        resp = client.get("/webhook/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token-wa",
            "hub.challenge": "CHALLENGE123",
        })
        assert resp.status_code == 403, resp.text
    finally:
        settings.whatsapp_verify_token = orig_wa
        settings.instagram_verify_token = orig_ig


def test_messaging_signature_and_parse():
    """HMAC-SHA256 signature: valid passes, bad/missing fails, empty
    secret fails. Parsers keep text messages and ignore statuses,
    echoes, images and malformed input."""
    import hashlib
    import hmac

    from backend.app.messaging import instagram, signature, whatsapp
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    secret = "test-app-secret-123"
    good = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256).hexdigest()
    assert signature.verify_signature(body, good, secret) is True
    assert signature.verify_signature(body, "sha256=" + "0" * 64,
                                      secret) is False
    assert signature.verify_signature(body, None, secret) is False
    assert signature.verify_signature(body, "not-a-signature",
                                      secret) is False
    assert signature.verify_signature(body, good, "") is False

    # WhatsApp: text kept, image + statuses ignored.
    payload = {"object": "whatsapp_business_account", "entry": [
        {"id": "123", "changes": [{"field": "messages", "value": {
            "messaging_product": "whatsapp",
            "metadata": {"phone_number_id": "999"},
            "messages": [
                {"from": "919999999999", "id": "wamid.text1",
                 "timestamp": "1700000000", "type": "text",
                 "text": {"body": "hello bhai"}},
                {"from": "919999999999", "id": "wamid.img1",
                 "timestamp": "1700000001", "type": "image",
                 "image": {"id": "x"}},
            ],
            "statuses": [{"id": "wamid.text1", "status": "delivered"}],
        }}]}]}
    parsed = whatsapp.parse_webhook(payload)
    assert len(parsed) == 1, parsed
    assert parsed[0]["message_id"] == "wamid.text1"
    assert parsed[0]["contact_id"] == "919999999999"
    assert parsed[0]["text"] == "hello bhai"
    assert parsed[0]["timestamp"] == 1700000000.0
    assert whatsapp.parse_webhook({}) == []
    # A message without an id is dropped (dedupe needs the id).
    no_id = {
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "91", "id": "", "timestamp": "1",
                        "type": "text", "text": {"body": "no id"},
                    }],
                },
            }],
        }],
    }
    assert whatsapp.parse_webhook(no_id) == []

    # Instagram: text kept, echo + delivery ignored, ms -> seconds.
    ig = {"object": "instagram", "entry": [{"id": "ig1", "messaging": [
        {"sender": {"id": "USER1"}, "recipient": {"id": "PAGE1"},
         "timestamp": 1700000000000,
         "message": {"mid": "m.text1", "text": "namaste"}},
        {"sender": {"id": "PAGE1"}, "recipient": {"id": "USER1"},
         "timestamp": 1700000001000,
         "message": {"mid": "m.echo1", "text": "echo", "is_echo": True}},
        {"sender": {"id": "USER1"}, "recipient": {"id": "PAGE1"},
         "timestamp": 1700000002000,
         "delivery": {"mids": ["m.text1"]}},
    ]}]}
    parsed = instagram.parse_webhook(ig)
    assert len(parsed) == 1, parsed
    assert parsed[0]["message_id"] == "m.text1"
    assert parsed[0]["contact_id"] == "USER1"
    assert parsed[0]["timestamp"] == 1700000000.0
    assert instagram.parse_webhook({}) == []


def test_messaging_autoreply_engine():
    """The engine with a stub brain + stub sender (no live calls):
    fresh message -> replied; same id again -> duplicate (one send);
    25h-old message -> outside window; platform OFF / unconfigured ->
    skipped; 30 replies in the last hour -> rate-limited; Instagram
    path works the same way."""
    import time

    from backend.app.config import settings
    from backend.app.messaging import autoreply, store

    orig = (settings.whatsapp_token, settings.whatsapp_phone_number_id)
    orig_enabled = store.get_platform_enabled("whatsapp")
    sent = []

    def stub_chat(messages, temperature=0.2, timeout=180):
        # Persona prompt present, history passed through.
        assert messages[0]["role"] == "system"
        assert "same language and script" in messages[0]["content"]
        assert messages[-1]["role"] == "user"
        return "Haan bhai, ho jayega!"

    def stub_send(platform, contact_id, text):
        sent.append((platform, contact_id, text))
        return "sent-id-1"

    try:
        store.set_platform_enabled("whatsapp", True)  # v0.7: store, not settings
        settings.whatsapp_token = "fake-test-token-1234567890"
        settings.whatsapp_phone_number_id = "999888777666555"
        now = time.time()

        # 1. Fresh message -> replied, history records both turns.
        out = autoreply.handle_incoming(
            "whatsapp", "wamid.e1", "919999999999", "hello", now,
            chat_fn=stub_chat, send_fn=stub_send)
        assert out["action"] == "replied", out
        assert len(sent) == 1 and sent[0][2] == "Haan bhai, ho jayega!"
        hist = store.get_history("whatsapp", "919999999999")
        assert [h["role"] for h in hist] == ["user", "assistant"], hist

        # 2. Same message id again -> duplicate, no second send.
        out = autoreply.handle_incoming(
            "whatsapp", "wamid.e1", "919999999999", "hello", now,
            chat_fn=stub_chat, send_fn=stub_send)
        assert out == {"action": "skipped", "reason": "duplicate"}, out
        assert len(sent) == 1

        # 3. 25h-old message -> outside window, no send.
        out = autoreply.handle_incoming(
            "whatsapp", "wamid.e2", "918888888888", "old hello",
            now - 25 * 3600, chat_fn=stub_chat, send_fn=stub_send)
        assert out["reason"] == "outside_24h_window", out
        assert len(sent) == 1

        # 4. Platform OFF -> skipped, no send.
        store.set_platform_enabled("whatsapp", False)
        out = autoreply.handle_incoming(
            "whatsapp", "wamid.e3", "919999999999", "hello?", now,
            chat_fn=stub_chat, send_fn=stub_send)
        assert out["reason"] == "platform_off_or_unconfigured", out
        assert len(sent) == 1
        store.set_platform_enabled("whatsapp", True)

        # 5. Unconfigured (no token) -> skipped, no send.
        settings.whatsapp_token = ""
        out = autoreply.handle_incoming(
            "whatsapp", "wamid.e4", "919999999999", "hello?", now,
            chat_fn=stub_chat, send_fn=stub_send)
        assert out["reason"] == "platform_off_or_unconfigured", out
        assert len(sent) == 1
        settings.whatsapp_token = "fake-test-token-1234567890"

        # 6. Rate limit: 30 replies in the last hour -> 31st skipped.
        for i in range(30):
            store.record_message("whatsapp", "917777777777", "assistant",
                                 f"r{i}")
        out = autoreply.handle_incoming(
            "whatsapp", "wamid.e5", "917777777777", "hello?", now,
            chat_fn=stub_chat, send_fn=stub_send)
        assert out["reason"] == "rate_limited", out
        assert len(sent) == 1

        # 7. Instagram path works the same way.
        orig_ig = (settings.instagram_token, settings.instagram_page_id)
        orig_ig_enabled = store.get_platform_enabled("instagram")
        try:
            store.set_platform_enabled("instagram", True)
            settings.instagram_token = "fake-ig-token-1234567890"
            settings.instagram_page_id = "111222333444555"
            out = autoreply.handle_incoming(
                "instagram", "m.e1", "IGUSER1", "hi", now,
                chat_fn=stub_chat, send_fn=stub_send)
            assert out["action"] == "replied", out
            assert sent[-1][0] == "instagram"
        finally:
            (settings.instagram_token,
             settings.instagram_page_id) = orig_ig
            store.set_platform_enabled("instagram", orig_ig_enabled)
    finally:
        (settings.whatsapp_token,
         settings.whatsapp_phone_number_id) = orig
        store.set_platform_enabled("whatsapp", orig_enabled)


def test_messaging_webhook_end_to_end():
    """Full path with mock payloads: POST a WhatsApp webhook (valid
    signature) -> 200 and exactly one send; POST the same payload again
    -> still one send (dedupe through the real path); bad signature ->
    403 and no send; no app secret configured -> accepted (with a
    warning, like the real server behaves). Brain + send are stubbed —
    no live Meta call."""
    import hashlib
    import hmac
    import json as _json
    import time

    from backend.app.config import settings
    from backend.app.messaging import autoreply, store, webhooks, whatsapp

    client = _client()
    orig = (settings.whatsapp_token,
            settings.whatsapp_phone_number_id, settings.whatsapp_app_secret)
    orig_enabled = store.get_platform_enabled("whatsapp")
    sent = []
    orig_dispatch = webhooks._dispatch
    orig_send = whatsapp.send_text
    orig_chat = brain.chat

    def sync_dispatch(platform, message):
        autoreply.handle_incoming(
            platform, message["message_id"], message["contact_id"],
            message["text"], message["timestamp"])

    def stub_send(to, text, token, phone_number_id, timeout=30):
        sent.append((to, text))
        return "wamid.sent1"

    def stub_chat(messages, temperature=0.2, timeout=180):
        return "Bilkul, kar deta hoon!"

    try:
        store.set_platform_enabled("whatsapp", True)  # v0.7: store, not settings
        settings.whatsapp_token = "fake-test-token-1234567890"
        settings.whatsapp_phone_number_id = "999888777666555"
        settings.whatsapp_app_secret = "test-app-secret-123"
        webhooks._dispatch = sync_dispatch
        whatsapp.send_text = stub_send
        brain.chat = stub_chat

        payload = {"object": "whatsapp_business_account", "entry": [
            {"id": "123", "changes": [{"field": "messages", "value": {
                "messaging_product": "whatsapp",
                "messages": [
                    {"from": "916666666666", "id": "wamid.e2e1",
                     "timestamp": str(int(time.time())), "type": "text",
                     "text": {"body": "bhai kal milte hain?"}},
                ],
            }}]}]}
        raw = _json.dumps(payload).encode()
        good_sig = "sha256=" + hmac.new(
            b"test-app-secret-123", raw, hashlib.sha256).hexdigest()

        # Valid signature -> 200, one send.
        resp = client.post("/webhook/whatsapp", content=raw, headers={
            "X-Hub-Signature-256": good_sig,
            "Content-Type": "application/json",
        })
        assert resp.status_code == 200, resp.text
        assert len(sent) == 1, sent
        assert sent[0][0] == "916666666666"
        assert sent[0][1] == "Bilkul, kar deta hoon!"

        # Same delivery again (Meta redelivery) -> 200, still one send.
        resp = client.post("/webhook/whatsapp", content=raw, headers={
            "X-Hub-Signature-256": good_sig,
            "Content-Type": "application/json",
        })
        assert resp.status_code == 200, resp.text
        assert len(sent) == 1, sent

        # Bad signature -> 403, no send.
        resp = client.post("/webhook/whatsapp", content=raw, headers={
            "X-Hub-Signature-256": "sha256=" + "0" * 64,
            "Content-Type": "application/json",
        })
        assert resp.status_code == 403, resp.text
        assert len(sent) == 1, sent

        # No app secret configured -> accepted (warning only).
        settings.whatsapp_app_secret = ""
        payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = \
            "wamid.e2e2"
        raw2 = _json.dumps(payload).encode()
        resp = client.post("/webhook/whatsapp", content=raw2, headers={
            "Content-Type": "application/json",
        })
        assert resp.status_code == 200, resp.text
        assert len(sent) == 2, sent
    finally:
        (settings.whatsapp_token, settings.whatsapp_phone_number_id,
         settings.whatsapp_app_secret) = orig
        store.set_platform_enabled("whatsapp", orig_enabled)
        webhooks._dispatch = orig_dispatch
        whatsapp.send_text = orig_send
        brain.chat = orig_chat


def test_messaging_chat_control():
    """v0.7: messaging is controlled from chat, not Settings.
    (a) set_messaging("instagram", True) with a configured token+page
    persists + enables; set_messaging(..., False) disables; status
    reports it. (b) enabling without a token returns the one-time
    secure-box blocker, does NOT enable, and records a pending
    request. (c) the Settings UI has no messaging fields anywhere
    (PWA modal, PWA JS, Flutter settings screen, GET /settings);
    POST /settings with a whatsapp_token is ignored. The secure-box
    UI is wired in the PWA + Flutter chat, and the system prompt
    tells the brain about chat control."""
    from backend.app.agent import SYSTEM_PROMPT
    from backend.app.config import settings
    from backend.app.messaging import store
    from backend.app.tools import messaging_tool

    client = _client()
    orig = (settings.instagram_token, settings.instagram_page_id,
            settings.instagram_verify_token, settings.instagram_app_secret,
            settings.whatsapp_token, settings.whatsapp_phone_number_id,
            settings.whatsapp_verify_token, settings.whatsapp_app_secret)
    orig_ig = store.get_platform_enabled("instagram")
    orig_wa = store.get_platform_enabled("whatsapp")
    try:
        # --- (a) enable with everything configured -> clean confirm ---
        settings.instagram_token = "EAAFakeIGToken1234567890"
        settings.instagram_page_id = "111222333444555"
        settings.instagram_verify_token = "fake-verify-ig-1"
        settings.instagram_app_secret = "fake-secret-ig-12345"
        msg = messaging_tool.set_messaging("instagram", True)
        assert msg.startswith("Done"), msg
        assert "without asking you" in msg, msg
        assert store.get_platform_enabled("instagram") is True
        status = messaging_tool.get_messaging_status()
        assert "Instagram: ON" in status, status
        # Aliases work too (small local models vary).
        msg = messaging_tool.set_messaging("insta", False)
        assert "is now off" in msg, msg
        assert store.get_platform_enabled("instagram") is False
        assert "Instagram: OFF" in messaging_tool.get_messaging_status()

        # --- (a2) enable with verify token missing -> still enables,
        # but records a pending request for the webhook fields. ---
        settings.instagram_verify_token = ""
        settings.instagram_app_secret = ""
        msg = messaging_tool.set_messaging("instagram", True)
        assert "Done" in msg and "verify token" in msg, msg
        assert store.get_platform_enabled("instagram") is True
        pending = store.get_pending_credential("instagram")
        assert pending is not None and "verify_token" in pending, pending
        store.clear_pending_credential("instagram")
        messaging_tool.set_messaging("instagram", False)

        # --- (b) enable without a token -> blocker, not enabled,
        # pending request recorded for the secure box. ---
        settings.whatsapp_token = ""
        settings.whatsapp_phone_number_id = ""
        settings.whatsapp_verify_token = ""
        settings.whatsapp_app_secret = ""
        msg = messaging_tool.set_messaging("whatsapp", True)
        assert "WHATSAPP_TOKEN" in msg, msg
        assert "WHATSAPP_PHONE_NUMBER_ID" in msg, msg
        assert "secure box" in msg, msg
        assert "Never type a token in a chat message" in msg, msg
        assert store.get_platform_enabled("whatsapp") is False
        pending = store.get_pending_credential("whatsapp")
        assert pending is not None, "no pending secure-box request"
        assert "token" in pending and "target_id" in pending, pending
        # Unknown platform -> plain-language nudge, no crash.
        msg = messaging_tool.set_messaging("telegram", True)
        assert "Couldn't understand the platform" in msg, msg

        # --- (c) Settings has no messaging fields anywhere. ---
        static = ROOT / "backend" / "static"
        html = (static / "index.html").read_text()
        js = (static / "app.js").read_text()
        css = (static / "style.css").read_text()
        # Field identifiers from the removed v0.6 Settings section.
        gone_ids = ("setWhatsapp", "setInstagram", "msgWhatsapp",
                    "msgInstagram", "whatsapp_enabled",
                    "instagram_enabled", "whatsapp_token",
                    "instagram_token", "whatsapp_phone_number_id",
                    "instagram_page_id")
        for text, where in ((html, "index.html"), (js, "app.js")):
            for gone in gone_ids:
                assert gone not in text, f"{where} still has {gone}"
        dart_settings = (ROOT / "mobile_app" / "lib" / "screens"
                         / "settings_screen.dart").read_text()
        for gone in ("whatsapp_token", "instagram_token", "whatsappEnabled",
                     "instagramEnabled", "_waTokenCtrl", "_igTokenCtrl"):
            assert gone not in dart_settings, \
                f"Flutter settings still has {gone}"
        data = client.get("/settings").json()
        leaked = [k for k in data
                  if k.startswith(("whatsapp_", "instagram_"))]
        assert not leaked, f"GET /settings still has messaging keys: {leaked}"
        # POST /settings with a messaging key is ignored: the unknown
        # key is dropped, nothing is saved (400 = "nothing to change").
        resp = client.post("/settings", json={
            "whatsapp_token": "EAAIgnoredToken1234567890"})
        assert resp.status_code == 400, resp.text
        assert "Nothing to change" in resp.json()["detail"], resp.text
        assert settings.whatsapp_token == "", settings.whatsapp_token

        # --- secure-box UI wiring (PWA + Flutter chat) ---
        for want in ("secure-card", "checkMessagingPending",
                     "/messaging/pending", "/messaging/credentials"):
            assert want in js, f"app.js missing {want}"
        assert ".secure-card" in css, "style.css missing .secure-card"
        dart_chat = (ROOT / "mobile_app" / "lib" / "screens"
                     / "chat_screen.dart").read_text()
        assert "_SecureCredentialCard" in dart_chat
        assert "getMessagingPending" in dart_chat
        dart_api = (ROOT / "mobile_app" / "lib" / "api.dart").read_text()
        assert "saveMessagingCredentials" in dart_api
        assert "MessagingPending" in dart_api
        icons_dir = ROOT / "mobile_app" / "assets" / "icons"
        assert (icons_dir / "lock.svg").is_file(), "missing lock icon"
        # The system prompt tells the brain about chat control.
        assert "set_messaging" in SYSTEM_PROMPT
        assert "secure box" in SYSTEM_PROMPT.lower()
    finally:
        (settings.instagram_token, settings.instagram_page_id,
         settings.instagram_verify_token, settings.instagram_app_secret,
         settings.whatsapp_token, settings.whatsapp_phone_number_id,
         settings.whatsapp_verify_token, settings.whatsapp_app_secret) = orig
        store.set_platform_enabled("instagram", orig_ig)
        store.set_platform_enabled("whatsapp", orig_wa)
        store.clear_pending_credential("instagram")
        store.clear_pending_credential("whatsapp")


def test_messaging_secure_credentials():
    """v0.7 secure box: POST /messaging/credentials saves to .env,
    returns masked previews only (full values never in the response),
    auto-enables when token+id are complete; bad values are 400s.
    GET /messaging/pending lists the request after a failed enable
    and is empty once everything is saved."""
    from dotenv import dotenv_values

    from backend.app.config import settings
    from backend.app.messaging import store
    from backend.app.tools import messaging_tool

    client = _client()
    env_file = Path(os.environ["LINDA_ENV_FILE"])
    orig = (settings.whatsapp_token, settings.whatsapp_phone_number_id,
            settings.whatsapp_verify_token, settings.whatsapp_app_secret)
    orig_enabled = store.get_platform_enabled("whatsapp")
    try:
        settings.whatsapp_token = ""
        settings.whatsapp_phone_number_id = ""
        settings.whatsapp_verify_token = ""
        settings.whatsapp_app_secret = ""
        store.set_platform_enabled("whatsapp", False)
        store.clear_pending_credential("whatsapp")

        # A failed enable (no token) makes /messaging/pending list it.
        messaging_tool.set_messaging("whatsapp", True)
        resp = client.get("/messaging/pending")
        assert resp.status_code == 200, resp.text
        pending = resp.json()["pending"]
        assert len(pending) == 1, pending
        assert pending[0]["platform"] == "whatsapp"
        assert "token" in pending[0]["fields"]
        assert "target_id" in pending[0]["fields"]

        # Bad values -> 400 with an English message, nothing saved.
        for bad in ({"token": "short"},
                    {"token": "has space in it"},
                    {"target_id": "has space"},
                    {"verify_token": "x"},
                    {"platform": "telegram"}):
            if "platform" in bad:
                payload = {"platform": "telegram",
                           "values": {"token": "x" * 20}}
            else:
                payload = {"platform": "whatsapp", "values": bad}
            resp = client.post("/messaging/credentials", json=payload)
            assert resp.status_code == 400, \
                f"{bad} -> {resp.status_code} {resp.text}"
            assert resp.json()["detail"], resp.text
        assert settings.whatsapp_token == ""

        # Save token+id+verify via the secure box -> auto-enabled.
        resp = client.post("/messaging/credentials", json={
            "platform": "whatsapp",
            "values": {
                "token": "EAAFakeSecureBoxToken1234567890",
                "target_id": "999888777666555",
                "verify_token": "fake-verify-secure-1",
            }})
        assert resp.status_code == 200, resp.text
        body = resp.text
        assert "EAAFakeSecureBoxToken1234567890" not in body, "TOKEN LEAKED"
        assert "fake-verify-secure-1" not in body, "VERIFY TOKEN LEAKED"
        data = resp.json()
        assert data["enabled"] is True, data
        assert data["still_missing"] == ["app_secret"], data
        assert data["saved"] == ["token", "target_id", "verify_token"], data
        masked = data["masked"]["token"]
        assert masked.startswith("EAAF"), masked
        assert masked.endswith("7890"), masked
        assert "•" in masked, masked
        assert settings.whatsapp_token == "EAAFakeSecureBoxToken1234567890"
        assert settings.whatsapp_phone_number_id == "999888777666555"
        assert store.get_platform_enabled("whatsapp") is True
        saved = dotenv_values(str(env_file))
        assert saved.get("WHATSAPP_TOKEN") == \
            "EAAFakeSecureBoxToken1234567890", saved
        assert saved.get("WHATSAPP_PHONE_NUMBER_ID") == "999888777666555"

        # Pending now lists only the optional app_secret (still missing).
        resp = client.get("/messaging/pending")
        pending = resp.json()["pending"]
        assert len(pending) == 1, pending
        assert pending[0]["fields"] == ["app_secret"], pending

        # Save the last field -> pending is empty.
        resp = client.post("/messaging/credentials", json={
            "platform": "whatsapp",
            "values": {"app_secret": "fake-app-secret-secure-12345"}})
        assert resp.status_code == 200, resp.text
        assert "fake-app-secret-secure-12345" not in resp.text
        assert resp.json()["still_missing"] == [], resp.text
        resp = client.get("/messaging/pending")
        assert resp.json()["pending"] == [], resp.text
    finally:
        (settings.whatsapp_token, settings.whatsapp_phone_number_id,
         settings.whatsapp_verify_token,
         settings.whatsapp_app_secret) = orig
        store.set_platform_enabled("whatsapp", orig_enabled)
        store.clear_pending_credential("whatsapp")


# --- v0.8: Gmail (stubbed service — no live Google calls) ---
import base64  # noqa: E402
from datetime import datetime, timezone  # noqa: E402


def _b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def _raw_msg(mid, sender, subject, body, ms, kind="plain"):
    """Build a Gmail API messages.get payload. kind: 'plain' (single
    text/plain part), 'multipart' (plain + html — plain must win),
    'html' (html only — must be stripped to text)."""
    headers = [
        {"name": "From", "value": sender},
        {"name": "Subject", "value": subject},
        {"name": "Date", "value": "Mon, 23 Nov 2026 10:00:00 +0530"},
    ]
    if kind == "plain":
        payload = {"mimeType": "text/plain", "headers": headers,
                   "body": {"data": _b64(body)}}
    elif kind == "multipart":
        payload = {
            "mimeType": "multipart/alternative", "headers": headers,
            "parts": [
                {"mimeType": "text/plain", "body": {"data": _b64(body)}},
                {"mimeType": "text/html",
                 "body": {"data": _b64(f"<p>{body}</p>")}},
            ],
        }
    else:  # html only
        payload = {"mimeType": "text/html", "headers": headers,
                   "body": {"data": _b64(f"<div><p>{body}</p></div>")}}
    return {"id": mid, "snippet": body[:60], "internalDate": str(ms),
            "payload": payload, "_from": sender}


class _FakeExecute:
    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class _FakeMessages:
    """Mimics users().messages() — list + get, with a from: filter."""

    def __init__(self, messages):
        self._messages = messages

    def list(self, userId=None, q=None, maxResults=None):
        ids = list(self._messages)
        if q and q.startswith("from:"):
            sender = q[5:].strip().lower()
            ids = [i for i in ids
                   if sender in self._messages[i].get("_from", "").lower()]
        return _FakeExecute(
            {"messages": [{"id": i} for i in ids[: maxResults or 5]]})

    def get(self, userId=None, id=None, format=None):
        return _FakeExecute(self._messages[id])


class _FakeUsers:
    def __init__(self, messages):
        self._m = _FakeMessages(messages)

    def messages(self):
        return self._m


class _FakeGmailService:
    def __init__(self, messages):
        self._u = _FakeUsers(messages)

    def users(self):
        return self._u


def test_gmail_stub_search_and_parse():
    """Stubbed Gmail service: search + parse (plain, multipart, HTML
    fallback, headers, received_at)."""
    from backend.app.gmail import client as gmail_client

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    msgs = {
        "m1": _raw_msg("m1", "Internshala <noreply@internshala.com>",
                       "New internship matches", "Hi Linda, 3 new matches.",
                       now_ms),
        "m2": _raw_msg("m2", "Friend <friend@example.com>",
                       "Hello", "Plain body wins.", now_ms, "multipart"),
        "m3": _raw_msg("m3", "Shop <hi@shop.example>",
                       "Your order", "Order confirmed, thanks!",
                       now_ms, "html"),
    }
    service = _FakeGmailService(msgs)
    found = gmail_client.search_messages(service, "from:internshala")
    assert len(found) == 1, found
    assert found[0]["sender"].startswith("Internshala"), found[0]
    assert found[0]["subject"] == "New internship matches"
    assert "3 new matches" in found[0]["body"], found[0]
    assert found[0]["received_at"] is not None

    all_msgs = gmail_client.search_messages(service, "", max_results=5)
    assert len(all_msgs) == 3, all_msgs
    by_id = {m["id"]: m for m in all_msgs}
    assert by_id["m2"]["body"] == "Plain body wins.", by_id["m2"]
    assert by_id["m3"]["body"] == "Order confirmed, thanks!", by_id["m3"]
    assert "<" not in by_id["m3"]["body"], by_id["m3"]


def test_gmail_otp_extraction():
    """OTP extraction across formats, plus the no-match and year cases."""
    from backend.app.gmail.otp import extract_otp

    cases = [
        ("Your OTP is 482916. It expires in 10 minutes.", "482916"),
        ("Your verification code is 12345678", "12345678"),
        ("aapka OTP: 7392", "7392"),
        ("Use 552134 as your login code.", "552134"),
        ("Your one-time password is 884210. Do not share it.", "884210"),
        ("Your Internshala verification code is 90210", "90210"),
    ]
    for text, want in cases:
        assert extract_otp(text) == want, (text, extract_otp(text))
    # No plausible code at all.
    assert extract_otp("Hello! Your order shipped. Thanks!") is None
    assert extract_otp("") is None
    # A year is never an OTP, even near the word "code".
    assert extract_otp("Your code for 2024 is ready.") is None
    # Long numbers (order ids) are not grabbed by the fallback.
    assert extract_otp("Order 123456789012 confirmed.") is None


def test_gmail_find_otp_window():
    """find_otp_code: fresh email found, stale email ignored, no-match
    returns None. Time is injected so the test is deterministic."""
    from backend.app.gmail.otp import find_otp_code

    now = datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc)
    now_ms = int(now.timestamp() * 1000)
    fresh_ms = now_ms - 2 * 60 * 1000       # 2 minutes ago
    stale_ms = now_ms - 30 * 60 * 1000      # 30 minutes ago
    msgs = {
        "old": _raw_msg("old", "Internshala <noreply@internshala.com>",
                        "Your OTP", "Your OTP is 111111.", stale_ms),
        "new": _raw_msg("new", "Internshala <noreply@internshala.com>",
                        "Your OTP", "Your OTP is 482916.", fresh_ms),
    }
    service = _FakeGmailService(msgs)
    found = find_otp_code(service, "internshala", minutes=10, now=now)
    assert found is not None, "fresh OTP not found"
    assert found["code"] == "482916", found

    # Only the stale one exists -> nothing (never a stale OTP).
    service2 = _FakeGmailService({"old": msgs["old"]})
    assert find_otp_code(service2, "internshala", minutes=10,
                         now=now) is None
    # No OTP in the mail at all -> None.
    msgs3 = {"n": _raw_msg("n", "Internshala <noreply@internshala.com>",
                           "Newsletter", "This week's internships.",
                           fresh_ms)}
    assert find_otp_code(_FakeGmailService(msgs3), "internshala",
                         minutes=10, now=now) is None


def test_gmail_not_configured():
    """Without token.json / client_secret.json, the Gmail tools return a
    clear setup message — never a crash, never a traceback in chat."""
    from backend.app.tools import gmail_tool

    # The test env points DATA_DIR at a temp dir (no token.json), and the
    # real project has no client_secret.json checked in.
    result = gmail_tool.read_gmail("in:inbox")
    assert "GMAIL_SETUP.md" in result, result
    assert "Traceback" not in result
    result = gmail_tool.find_otp("Internshala")
    assert "GMAIL_SETUP.md" in result, result
    assert gmail_tool.get_otp_code("Internshala") is None


def test_gmail_tools_and_prompt():
    """Gmail + form tools are registered, the system prompt documents
    Gmail/OTP/Google sign-in, and the Internshala site profile exists."""
    from backend.app.agent import SYSTEM_PROMPT, TOOLS

    for name in ("read_gmail", "find_otp", "browser_fill_form",
                 "browser_fill_otp"):
        assert name in TOOLS, f"tool {name} not registered"
    assert "GMAIL (read-only" in SYSTEM_PROMPT
    assert "GOOGLE SIGN-IN" in SYSTEM_PROMPT
    assert "browser_fill_otp" in SYSTEM_PROMPT
    assert "site-profiles.yaml" in SYSTEM_PROMPT
    import yaml
    profiles = yaml.safe_load((ROOT / "site-profiles.yaml").read_text())
    assert "internshala" in profiles, profiles
    assert profiles["internshala"]["login_url"].startswith("https://")
    assert "My Applications" in profiles["internshala"]["notes"]


# --- v0.8: browser upgrades (persistent profile, form fill, OTP fill) ---
def _skip_if_no_chromium(e):
    if "Executable doesn't exist" in str(e) or "launch" in str(e).lower():
        skip("browser test", f"Chromium not installed/launchable here: {e}")
        return True
    return False


def test_browser_persistent_profile():
    """A cookie set in the persistent profile survives close + relaunch
    (this is what keeps Google signed in across restarts)."""
    from backend.app.tools import browser_tool

    try:
        browser_tool.browser_open("data:text/html,<h1>first</h1>")
        ctx = browser_tool.browser._context
        assert ctx is not None
        # A cookie needs a future expiry to be written to disk — session
        # cookies (no expires) live in memory only and never persist.
        expires = int(time.time()) + 86400
        ctx.add_cookies([{"name": "linda-persist-test", "value": "yes",
                          "domain": "example.com", "path": "/",
                          "expires": expires}])
        profile_dir = browser_tool.browser.profile_dir
        assert profile_dir.is_dir(), profile_dir
        browser_tool.browser_close()

        browser_tool.browser_open("data:text/html,<h1>second</h1>")
        cookies = browser_tool.browser._context.cookies("https://example.com")
        assert any(c["name"] == "linda-persist-test" and c["value"] == "yes"
                   for c in cookies), cookies
    except Exception as e:  # noqa: BLE001
        if _skip_if_no_chromium(e):
            return
        raise
    finally:
        try:
            browser_tool.browser_close()
        except Exception:  # noqa: BLE001 — close is best-effort in tests
            pass


_FORM_HTML = """<!doctype html><html><body>
<form id="f" onsubmit="document.getElementById('out').textContent =
 'Submitted: name=' + document.querySelector('[name=name]').value +
 ' email=' + document.querySelector('[name=email]').value +
 ' city=' + document.querySelector('[name=city]').value +
 ' msg=' + document.querySelector('[name=msg]').value; return false;">
<label>Full Name <input name="name" type="text"></label><br>
<label>Email Address <input name="email" type="email"></label><br>
<label>City <select name="city"><option value="">--</option>
<option value="Patna">Patna</option><option value="Delhi">Delhi</option>
</select></label><br>
<label>Message <textarea name="msg"></textarea></label><br>
<button type="submit">Submit</button>
</form>
<div id="out"></div>
</body></html>"""

_OTP_HTML = """<!doctype html><html><body>
<form><label>Enter OTP <input name="otp" inputmode="numeric"></label></form>
<div id="boxes">
<input maxlength="1"><input maxlength="1"><input maxlength="1">
<input maxlength="1"><input maxlength="1"><input maxlength="1">
</div>
</body></html>"""


def test_browser_fill_form():
    """Fill + submit a LOCAL test form (no network): label, name, select
    and textarea fields, then verify the submitted values."""
    from backend.app.tools import browser_tool

    page_path = TMP / "form.html"
    page_path.write_text(_FORM_HTML)
    try:
        result = browser_tool.browser_fill_form(
            page_path.as_uri(),
            [{"label": "Full Name", "value": "Satyam Patel"},
             {"name": "email", "value": "test@test.local"},
             {"label": "City", "value": "Patna", "type": "select"},
             {"name": "msg", "value": "hello world"}],
            submit=True)
        assert "Full Name" in result and "email" in result, result
        assert "Skip hue" not in result, result
        text = browser_tool.browser_read()
        assert ("Submitted: name=Satyam Patel email=test@test.local "
                "city=Patna msg=hello world") in text, text[:500]
    except Exception as e:  # noqa: BLE001
        if _skip_if_no_chromium(e):
            return
        raise
    finally:
        try:
            browser_tool.browser_close()
        except Exception:  # noqa: BLE001 — close is best-effort in tests
            pass


def test_browser_fill_otp_stub():
    """OTP auto-fill against a LOCAL test page, with the Gmail lookup
    stubbed (no live Google call): single field + multi-box, and the
    code is never echoed back in the result."""
    from backend.app.tools import browser_tool, gmail_tool

    page_path = TMP / "otp.html"
    page_path.write_text(_OTP_HTML)
    original = gmail_tool.get_otp_code
    gmail_tool.get_otp_code = lambda sender, minutes=10: "482916"
    try:
        browser_tool.browser_open(page_path.as_uri())
        result = browser_tool.browser_fill_otp("TestSite")
        assert "OTP filled" in result, result
        assert "482916" not in result, "OTP code leaked into the result"
        page = browser_tool.browser._page
        assert page.input_value('input[name="otp"]') == "482916"
        # Multi-box: remove the single field, the boxes get the digits.
        page.evaluate(
            "document.querySelector('input[name=otp]').remove()")
        result = browser_tool.browser_fill_otp("TestSite")
        assert "OTP filled" in result, result
        values = page.eval_on_selector_all(
            '#boxes input', "els => els.map(e => e.value).join('')")
        assert values == "482916", values
    except Exception as e:  # noqa: BLE001
        if _skip_if_no_chromium(e):
            return
        raise
    finally:
        gmail_tool.get_otp_code = original
        try:
            browser_tool.browser_close()
        except Exception:  # noqa: BLE001 — close is best-effort in tests
            pass


# --- v0.8.1: SMS OTP ask-and-fill ---
def test_browser_fill_otp_user_code():
    """A USER-PROVIDED code (SMS OTP) fills the OTP field on a LOCAL
    test page: single field + multi-box, Gmail never consulted, the
    code never echoed back, and the page is still open across the
    ask-and-reply gap (no reopen needed). Also covers the invalid-code
    message and the new Gmail-miss guidance."""
    from backend.app.tools import browser_tool, gmail_tool

    page_path = TMP / "otp_user.html"
    page_path.write_text(_OTP_HTML)
    original = gmail_tool.get_otp_code

    def _must_not_be_called(sender, minutes=10):
        raise AssertionError("Gmail consulted for a user-provided code")

    gmail_tool.get_otp_code = _must_not_be_called
    try:
        browser_tool.browser_open(page_path.as_uri())
        page_before = browser_tool.browser._page
        # The "ask gap": the agent asked in chat, the user replies later.
        # The next turn just reads the page — the OTP page must still be
        # there, same page object, no reopen.
        text = browser_tool.browser_read()
        assert "Enter OTP" in text, text[:300]
        assert browser_tool.browser._page is page_before
        assert browser_tool.browser._page.url == page_path.as_uri()

        result = browser_tool.browser_fill_otp(code="739284")
        assert "OTP filled" in result, result
        assert "739284" not in result, "user code leaked into the result"
        page = browser_tool.browser._page
        assert page.input_value('input[name="otp"]') == "739284"

        # Multi-box: remove the single field, the boxes get the digits.
        page.evaluate(
            "document.querySelector('input[name=otp]').remove()")
        result = browser_tool.browser_fill_otp(code="7392")
        assert "OTP filled" in result, result
        assert "7392" not in result, "user code leaked into the result"
        values = page.eval_on_selector_all(
            '#boxes input', "els => els.map(e => e.value).join('')")
        assert values == "7392", values

        # An invalid code is refused cleanly, never echoed, never filled.
        result = browser_tool.browser_fill_otp(code="abc")
        assert "doesn't look right" in result, result
        assert "abc" not in result, result

        # Gmail-miss guidance (no code given, no email OTP found): the
        # agent must ASK the user — never "fill it yourself".
        gmail_tool.get_otp_code = lambda sender, minutes=10: None
        result = browser_tool.browser_fill_otp("TestSite")
        assert "in the user's language" in result, result
        assert "don't close the browser" in result, result
        assert "khud bharna hoga" not in result, result
    except Exception as e:  # noqa: BLE001
        if _skip_if_no_chromium(e):
            return
        raise
    finally:
        gmail_tool.get_otp_code = original
        try:
            browser_tool.browser_close()
        except Exception:  # noqa: BLE001 — close is best-effort in tests
            pass


def test_otp_code_redaction():
    """A one-time code the user types is used once and never stored:
    the redact helper masks bare-code messages, step args are masked
    in the task store, and the DB task log carries no code even when
    the agent's finish answer echoes it."""
    from backend.app.agent import redact_otp_text, task_store

    assert "482916" not in redact_otp_text("482916")
    assert "••••••" in redact_otp_text("482916")
    assert "482916" not in redact_otp_text("otp 482916")
    assert "482916" not in redact_otp_text("OTP: 482916")
    # Normal messages pass through untouched.
    assert redact_otp_text("mere Gmail me kya aaya hai?") == \
        "mere Gmail me kya aaya hai?"
    assert redact_otp_text("order 1234 shipped, total 500") == \
        "order 1234 shipped, total 500"

    # Step args: the code is masked in the stored step, and the
    # caller's dict is not mutated.
    task_id = task_store.create("redaction probe")
    args = {"code": "482916"}
    task_store.add_step(task_id, {
        "n": 1, "thought": "fill", "action": "browser_fill_otp",
        "args": args, "result": "OTP bhar diya (6-digit code).",
    })
    stored = task_store.get(task_id)["steps"][0]
    assert stored["args"]["code"] == "••••••", stored["args"]
    assert args["code"] == "482916", "caller args were mutated"
    # A finish answer that echoes the code is masked in the step too.
    task_store.add_step(task_id, {
        "n": 2, "thought": "done", "action": "finish", "args": {},
        "result": "OTP 482916 bhar diya.",
    })
    stored = task_store.get(task_id)["steps"][1]
    assert "482916" not in stored["result"], stored["result"]

    # DB log: run a stub-brain task whose message IS the code and whose
    # finish answer echoes it — neither may reach the tasks table.
    script = ['{"thought": "done", "action": "finish", '
              '"answer": "OTP 482916 bhar diya."}']
    calls = {"n": 0}

    def stub_chat(messages, temperature=0.2, timeout=180):
        calls["n"] += 1
        return script[0]

    original = brain.chat
    brain.chat = stub_chat
    try:
        task_id2 = task_store.create(redact_otp_text("482916"))
        agent.run_task(task_id2, "482916")
        task = task_store.get(task_id2)
        assert task["status"] == "done", task
        assert "482916" not in task["message"], task["message"]
        for row in memory.recent_tasks(limit=5):
            assert "482916" not in (row["task"] or ""), row
            assert "482916" not in (row["result"] or ""), row
    finally:
        brain.chat = original


def test_sms_otp_prompt():
    """The system prompt tells the agent to ASK the user for an SMS OTP
    and fill it itself — the old 'fill it yourself in the visible
    browser' wording is gone from the prompt and the OTP code paths."""
    from backend.app.agent import SYSTEM_PROMPT, TOOLS

    # Ask-and-fill wording is present — the agent asks in the user's
    # own language (no hardcoded phrase in any one language).
    assert "whatever language the user is chatting in" in SYSTEM_PROMPT
    assert "SMS pe aaya OTP bhejo" not in SYSTEM_PROMPT
    assert '"code": "482916"' in SYSTEM_PROMPT
    assert "do NOT close the browser" in SYSTEM_PROMPT
    assert "never ask the user for an email OTP" in SYSTEM_PROMPT
    # The tool advertises the code argument.
    assert '"code"' in TOOLS["browser_fill_otp"]["desc"]
    # The old wording is gone — nowhere does the agent tell the user
    # to fill an SMS OTP himself any more.
    for gone in ("fill those himself", "khud bharna hoga",
                 "tell the user to fill"):
        assert gone not in SYSTEM_PROMPT, f"prompt still has {gone!r}"
    for path in ("backend/app/tools/browser_tool.py",
                 "backend/app/tools/gmail_tool.py"):
        src = (ROOT / path).read_text()
        assert "khud bharna hoga" not in src, f"{path} still has it"
        assert "fill those himself" not in src, f"{path} still has it"


# --- v0.8.2: English welcome + composer snap-back ---
# (v0.8.3: the welcome bubble is now the greeting ONLY — the
# capabilities paragraph and first-time hints were removed.)
def test_welcome_message_english():
    """The welcome message is plain English in BOTH the PWA and the
    Flutter app — the app must not greet a first-time user in a fixed
    Hinglish greeting. The brain still auto-adapts: it answers in
    whatever language/script the user chats in, from their first
    message. No language setting exists anywhere. v0.8.3: the bubble
    holds ONLY the greeting — no capabilities paragraph, no hints."""
    import re
    from backend.app.agent import SYSTEM_PROMPT

    expected = ("Hey! I'm Linda — your personal AI agent. "
                "Just tell me what you need, and I'll get it done.")

    # PWA: the welcome bubble holds exactly the greeting.
    html = (ROOT / "backend" / "static" / "index.html").read_text()
    m = re.search(r'bubble-welcome">(.*?)</div>', html, re.DOTALL)
    assert m, "welcome bubble not found in index.html"
    bubble = re.sub(r"<[^>]+>", "", m.group(1))
    bubble = re.sub(r"\s+", " ", bubble).strip()
    assert bubble == expected, f"welcome bubble is not the greeting only: {bubble!r}"
    for gone in ("Namaste", "Main Linda hoon", "tumhara",
                 "Mujhe koi kaam bolo", "writing code, pushing to GitHub",
                 "First time here?"):
        assert gone not in bubble, f"welcome bubble still has {gone!r}"

    # Flutter: the initial chat message. (Dart escapes the apostrophe
    # as \' in the source, so normalize before matching.)
    dart = (ROOT / "mobile_app" / "lib" / "screens"
            / "chat_screen.dart").read_text().replace("\\'", "'")
    assert "Hey! I'm Linda" in dart, "Flutter welcome is not English"
    assert "Just tell me what you need, and I'll get it done." in dart
    for gone in ("Namaste", "Main Linda hoon",
                 "writing code, pushing to GitHub",
                 "researching the web and making Excel sheets",
                 "Kaggle work — anything"):
        assert gone not in dart, f"Flutter welcome still has {gone!r}"

    # The brain auto-adapts from the very first message, and there is
    # still no language setting to pick from.
    assert "from their very first message" in SYSTEM_PROMPT
    assert "same language and script the user used" in SYSTEM_PROMPT
    assert "default to English when unclear" in SYSTEM_PROMPT
    from backend.app.config import SETTABLE_KEYS, settings
    assert "language" not in SETTABLE_KEYS
    assert "language" not in settings.public_dict()


# --- v0.8.3: clean chat screen ---
def test_chat_ui_english_and_clean():
    """The chat screen is fresh and clean in BOTH the PWA and Flutter:
    the composer placeholder and every chat-visible toast/hint is
    short clean English, and the header has no model subtitle (brain
    info lives in the Status panel). The Settings/Status modals keep
    their Hinglish fix hints — they are separate screens, not chat."""
    html = (ROOT / "backend" / "static" / "index.html").read_text()
    js = (ROOT / "backend" / "static" / "app.js").read_text()
    chat_dart = (ROOT / "mobile_app" / "lib" / "screens"
                 / "chat_screen.dart").read_text().replace("\\'", "'")
    main_dart = (ROOT / "mobile_app" / "lib" / "main.dart").read_text()
    voice_dart = (ROOT / "mobile_app" / "lib" / "voice.dart").read_text()
    api_dart = (ROOT / "mobile_app" / "lib" / "api.dart").read_text()

    # English placeholder in all three composer spots.
    for name, text in (("index.html", html), ("app.js", js),
                       ("chat_screen.dart", chat_dart)):
        assert "Tell Linda what to do…" in text, f"{name} lacks the English placeholder"

    # English listening hint + steps empty state, both apps.
    assert "Listening… speak — tap the mic again to stop" in html
    assert "Listening… speak — tap the mic again to stop" in chat_dart
    assert "Your agent's steps will appear here live." in html
    assert "Your agent's steps will appear here live." in chat_dart

    # No Hinglish chat strings left in any chat UI file.
    gone = (
        "Linda ko koi kaam bolo", "Sun raha hoon", "Bol ke likho",
        "Task roko", "Approval chahiye", "Kaam ho raha hai",
        "kuch galat ho gaya", "Yahan agent ke steps live dikhenge",
        "dekhne ke liye dabao", "Save karo — auto-reply chalu karo",
        "Kuch daalo toh", "khaali chhod sakte ho",
        "Voice input shuru nahi ho paya", "Mic ki permission nahi mili",
        "Server se connect nahi ho raha", "Task shuru nahi ho paya",
        "Task rok diya gaya", "Settings save ho gaye",
        "Credentials save ho gaye", "setup theek hai",
        "Token yahin paste karo", "Ho gaya.",
    )
    for name, text in (("index.html", html), ("app.js", js),
                       ("chat_screen.dart", chat_dart),
                       ("main.dart", main_dart), ("voice.dart", voice_dart),
                       ("api.dart", api_dart)):
        for g in gone:
            assert g not in text, f"{name} still has chat Hinglish {g!r}"

    # No model subtitle anywhere in the header code.
    for name, text in (("index.html", html), ("app.js", js),
                       ("main.dart", main_dart)):
        assert "statusLine" not in text, f"{name} still has a statusLine"
    assert 'id="statusLine"' not in html
    assert 'h.brain + " • "' not in js
    assert "approval_mode'] ?? ''} mode" not in main_dart
    assert "Connecting…" not in html and "Connecting…" not in main_dart


def test_pwa_composer_resets():
    """Typing two lines grows the PWA composer; sending snaps it back
    to a single line immediately (Playwright, live server)."""
    import socket
    import urllib.request

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        skip("composer test", f"Playwright not installed here: {e}")

    # A free port, so the test never collides with a real server.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    env = dict(os.environ)
    env["PORT"] = str(port)
    proc = subprocess.Popen(
        [sys.executable, "run.py"], cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f"http://127.0.0.1:{port}"
        deadline = time.time() + 30
        while True:
            try:
                urllib.request.urlopen(base + "/health", timeout=1)
                break
            except Exception:  # noqa: BLE001 — server not up yet
                if time.time() > deadline:
                    raise AssertionError("test server did not come up")
                time.sleep(0.5)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(
                    viewport={"width": 390, "height": 844})
                page.goto(base + "/", wait_until="networkidle")
                page.wait_for_timeout(800)
                # The health modal auto-pops when Ollama is down (VM).
                if page.locator("#healthModal:not(.hidden)").count():
                    page.locator("#healthClose").click()
                    page.wait_for_timeout(300)
                ta = page.locator("#input")
                h_single = ta.evaluate("el => el.offsetHeight")
                ta.click()
                ta.type("a long message that wraps across two lines"
                        " for sure in this narrow view", delay=5)
                ta.press("Shift+Enter")
                ta.type("plus a second line", delay=5)
                page.wait_for_timeout(300)
                h_grown = ta.evaluate("el => el.offsetHeight")
                assert h_grown > h_single, (h_single, h_grown)
                page.locator("#sendBtn").click()
                page.wait_for_timeout(200)
                assert ta.evaluate("el => el.value") == ""
                h_after = ta.evaluate("el => el.offsetHeight")
                assert h_after == h_single, (h_single, h_after)
                browser.close()
        except Exception as e:  # noqa: BLE001
            if _skip_if_no_chromium(e):
                return
            raise
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


# --- v0.9: chat history persists + desktop launcher ---
def test_chat_history_store():
    """Message store round-trip: save, read back, history comes back
    in chat order (oldest first); the table prunes past 200 messages."""
    from backend.app import memory as mem

    mem.log_message("user", "history-probe-user-1")
    mem.log_message("agent", "history-probe-agent-1")
    mem.log_message("user", "history-probe-user-2")
    msgs = mem.recent_messages()
    texts = [m["text"] for m in msgs]
    i1 = texts.index("history-probe-user-1")
    i2 = texts.index("history-probe-agent-1")
    i3 = texts.index("history-probe-user-2")
    assert i1 < i2 < i3, "history is not in chat order"
    assert all(m["role"] in ("user", "agent") for m in msgs)
    assert all(m["created_at"] for m in msgs)

    # Cap: flood the table, only the newest 200 survive.
    for i in range(205):
        mem.log_message("user", f"history-flood-{i:03d}")
    msgs = mem.recent_messages()
    assert len(msgs) == 200, len(msgs)
    texts = [m["text"] for m in msgs]
    assert "history-flood-000" not in texts, "oldest message was not pruned"
    assert "history-flood-004" not in texts
    assert "history-flood-005" in texts
    assert texts[-1] == "history-flood-204"
    # The earlier probes were pruned too (older than the flood).
    assert "history-probe-user-1" not in texts


def test_chat_history_endpoint():
    """GET /chat/history returns the saved transcript, oldest first,
    and is protected by the API token like the other /chat routes."""
    from backend.app import memory as mem
    from backend.app.config import settings

    mem.log_message("user", "endpoint-probe-user")
    mem.log_message("agent", "endpoint-probe-agent")
    client = _client()
    original = settings.api_token
    try:
        settings.api_token = ""
        resp = client.get("/chat/history")
        assert resp.status_code == 200, resp.text
        msgs = resp.json()["messages"]
        texts = [m["text"] for m in msgs]
        assert texts.index("endpoint-probe-user") < texts.index(
            "endpoint-probe-agent"), texts[-4:]
        # Token set: no header -> 401, right token -> 200.
        settings.api_token = "test-token-abc123"
        assert client.get("/chat/history").status_code == 401
        resp = client.get(
            "/chat/history",
            headers={"Authorization": "Bearer test-token-abc123"})
        assert resp.status_code == 200, resp.text
        assert "endpoint-probe-agent" in [
            m["text"] for m in resp.json()["messages"]]
    finally:
        settings.api_token = original


def test_chat_history_redaction():
    """A one-time code typed in chat is never persisted in the
    transcript — checked through the real paths: POST /chat (user
    message) and task finish (an agent reply that echoes the code)."""
    from backend.app.agent import task_store

    client = _client()
    # User side: a bare SMS code sent via /chat.
    resp = client.post("/chat", json={"message": "738291"})
    assert resp.status_code == 200, resp.text
    # Agent side: a task whose finish answer echoes a code.
    task_id = task_store.create("redaction probe 2")
    task_store.finish(task_id, result="OTP 482916 bhar diya.")
    msgs = client.get("/chat/history").json()["messages"]
    blob = "\n".join(m["text"] for m in msgs)
    assert "738291" not in blob, "user OTP code persisted in chat history"
    assert "482916" not in blob, "agent-echoed OTP code persisted"
    assert "••••••" in blob, "masked code not found in history"
    # A normal message with numbers is untouched.
    client.post("/chat", json={"message": "order 1234 shipped"})
    msgs = client.get("/chat/history").json()["messages"]
    assert "order 1234 shipped" in [m["text"] for m in msgs]


def test_conversations_store():
    """Side chats: separate transcripts per conversation, auto-title
    from the first user message, newest-active-first listing, and
    delete removes the chat with its messages."""
    from backend.app import memory as mem

    a = mem.create_conversation()
    b = mem.create_conversation()
    assert a != b
    mem.log_message("user", "conv-a first message", conversation_id=a)
    mem.log_message("agent", "conv-a reply", conversation_id=a)
    mem.log_message("user", "conv-b only message", conversation_id=b)

    a_texts = [m["text"] for m in mem.recent_messages(a)]
    b_texts = [m["text"] for m in mem.recent_messages(b)]
    assert a_texts == ["conv-a first message", "conv-a reply"], a_texts
    assert b_texts == ["conv-b only message"], b_texts

    # Auto-title from the first user message.
    assert mem.get_conversation(a)["title"] == "conv-a first message"
    assert mem.get_conversation(b)["title"] == "conv-b only message"

    # Listing: both present with counts; B most recently active first.
    convs = {c["id"]: c for c in mem.list_conversations()}
    assert convs[a]["message_count"] == 2
    assert convs[b]["message_count"] == 1
    assert mem.list_conversations()[0]["id"] == b

    # resolve: bogus id falls back to most recent; valid id passes through.
    assert mem.resolve_conversation(999999) == b
    assert mem.resolve_conversation(a) == a
    assert mem.resolve_conversation(None) == b

    # Delete: chat and its messages are gone.
    assert mem.delete_conversation(a) is True
    assert mem.get_conversation(a) is None
    assert mem.delete_conversation(a) is False
    assert b in {c["id"] for c in mem.list_conversations()}


def test_conversations_migration():
    """A pre-conversations database (messages without conversation_id)
    is migrated on init: orphan messages are grouped into one chat
    titled from the first user message — no history lost, and the
    migration is idempotent."""
    import sqlite3
    from backend.app import memory as mem

    legacy = TMP / "legacy.db"
    conn = sqlite3.connect(legacy)
    conn.execute("""CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL)""")
    conn.execute(
        "INSERT INTO messages(role, text, created_at) VALUES(?,?,?)",
        ("user", "legacy first message here", "2026-01-01T00:00:00+00:00"))
    conn.execute(
        "INSERT INTO messages(role, text, created_at) VALUES(?,?,?)",
        ("agent", "legacy reply", "2026-01-01T00:01:00+00:00"))
    conn.commit()
    conn.close()

    original = mem.DB_PATH
    try:
        mem.DB_PATH = legacy
        mem.init_db()
        convs = mem.list_conversations()
        assert len(convs) == 1, convs
        assert convs[0]["title"] == "legacy first message here", convs
        msgs = mem.recent_messages(convs[0]["id"])
        assert [m["text"] for m in msgs] == [
            "legacy first message here", "legacy reply"], msgs
        # Idempotent: a second init does not create another chat.
        mem.init_db()
        assert len(mem.list_conversations()) == 1
    finally:
        mem.DB_PATH = original


def test_conversations_endpoint():
    """Side-chat endpoints over HTTP: create/list/history/delete, and
    POST /chat keeps the message in the chat it was sent to."""
    client = _client()
    resp = client.post("/conversations")
    assert resp.status_code == 200, resp.text
    cid = resp.json()["id"]

    resp = client.post("/chat", json={
        "message": "endpoint conv probe", "conversation_id": cid})
    assert resp.status_code == 200, resp.text
    assert resp.json()["conversation_id"] == cid

    resp = client.get(f"/chat/history?conversation_id={cid}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["conversation_id"] == cid
    assert "endpoint conv probe" in [
        m["text"] for m in resp.json()["messages"]]

    resp = client.get("/conversations")
    assert resp.status_code == 200, resp.text
    mine = [c for c in resp.json()["conversations"] if c["id"] == cid]
    assert mine and mine[0]["title"] == "endpoint conv probe", mine

    resp = client.delete(f"/conversations/{cid}")
    assert resp.status_code == 200, resp.text
    resp = client.get("/conversations")
    assert cid not in [c["id"] for c in resp.json()["conversations"]]
    assert client.delete(f"/conversations/{cid}").status_code == 404


def test_desktop_launcher():
    """The Windows desktop launcher is shipped and well-formed: the
    .bat reads server.txt, starts the local server only for local
    URLs, waits on /health, and opens an app-mode window (Chrome,
    Edge fallback); the PowerShell script builds the Desktop shortcut
    with the S-logo icon and an -AutoStart flag; the .ico is a real
    multi-size ICO; the guide covers cloud + auto-start + fixes."""
    import struct

    desktop = ROOT / "desktop"
    bat = (desktop / "Linda.bat").read_text()
    for want in ("server.txt", "127.0.0.1", "localhost", "/health",
                 "--app=", "chrome.exe", "msedge.exe",
                 ".venv\\Scripts\\python.exe", "run.py",
                 "goto :local", "goto :open"):
        assert want in bat, f"Linda.bat missing {want!r}"
    ps1 = (desktop / "create-shortcut.ps1").read_text()
    for want in ("WScript.Shell", "CreateShortcut", "Linda.lnk",
                 "linda.ico", "AutoStart", "Startup",
                 'GetFolderPath("Desktop")'):
        assert want in ps1, f"create-shortcut.ps1 missing {want!r}"
    wrapper = (desktop / "create-shortcut.bat").read_text()
    assert "ExecutionPolicy Bypass" in wrapper
    assert "create-shortcut.ps1" in wrapper
    server_txt = (desktop / "server.txt").read_text()
    assert "http://127.0.0.1:8000" in server_txt
    # The .ico is a real multi-size Windows icon — parse the header
    # directly (no PIL dependency in the test venv): 6-byte header,
    # then one 16-byte entry per size (width/height byte, 0 = 256).
    raw = (desktop / "linda.ico").read_bytes()
    reserved, typ, count = struct.unpack("<HHH", raw[:6])
    assert reserved == 0 and typ == 1 and count >= 4, (reserved, typ, count)
    sizes = set()
    for i in range(count):
        w, h = raw[6 + i * 16], raw[6 + i * 16 + 1]
        sizes.add((w or 256, h or 256))
    for want in ((16, 16), (32, 32), (48, 48), (256, 256)):
        assert want in sizes, f"ICO missing size {want}: {sizes}"
    guide = (desktop / "DESKTOP_GUIDE.md").read_text()
    for want in ("create-shortcut.bat", "server.txt", "Auto-start",
                 "Oracle", "Troubleshooting"):
        assert want in guide, f"DESKTOP_GUIDE.md missing {want!r}"


def test_chat_history_ui_wiring():
    """Both apps load the saved transcript on start: the PWA fetches
    /chat/history and renders it below the welcome bubble; the
    Flutter app has the same call and renders it after its welcome."""
    static = ROOT / "backend" / "static"
    js = (static / "app.js").read_text()
    for want in ("/chat/history", "loadChatHistory"):
        assert want in js, f"app.js missing {want}"
    dart_api = (ROOT / "mobile_app" / "lib" / "api.dart").read_text()
    assert "getChatHistory" in dart_api, "api.dart missing getChatHistory"
    assert "ChatHistoryMessage" in dart_api
    dart_chat = (ROOT / "mobile_app" / "lib" / "screens"
                 / "chat_screen.dart").read_text()
    assert "_loadChatHistory" in dart_chat
    assert "getChatHistory" in dart_chat


def test_pwa_chat_history_renders():
    """Seeded chat messages render in the PWA below the welcome
    bubble (Playwright, live server) — this is what the desktop icon
    opens: the same chat, back again."""
    import socket
    import urllib.request
    from backend.app import memory as mem
    from backend.app.agent import task_store

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        skip("history render test", f"Playwright not installed here: {e}")

    # Earlier tests spawn task threads (POST /chat) whose late replies
    # touch whichever conversation is most recent — wait for them to
    # finish so the seeded chat stays the one the app opens.
    deadline = time.time() + 30
    while time.time() < deadline:
        if not any(t["status"] in ("running", "waiting_approval")
                   for t in task_store.list_recent(limit=50)):
            break
        time.sleep(0.25)

    mem.log_message("user", "render-probe-user-msg")
    mem.log_message("agent", "render-probe-agent-reply")

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    env = dict(os.environ)
    env["PORT"] = str(port)
    proc = subprocess.Popen(
        [sys.executable, "run.py"], cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f"http://127.0.0.1:{port}"
        deadline = time.time() + 30
        while True:
            try:
                urllib.request.urlopen(base + "/health", timeout=1)
                break
            except Exception:  # noqa: BLE001 — server not up yet
                if time.time() > deadline:
                    raise AssertionError("test server did not come up")
                time.sleep(0.5)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(
                    viewport={"width": 390, "height": 844})
                page.goto(base + "/", wait_until="networkidle")
                # History loads async (conversations -> history); wait
                # for the seeded message instead of a fixed sleep.
                page.locator("#messages").get_by_text(
                    "render-probe-user-msg").wait_for(timeout=15000)
                # The health modal auto-pops when Ollama is down (VM).
                if page.locator("#healthModal:not(.hidden)").count():
                    page.locator("#healthClose").click()
                    page.wait_for_timeout(300)
                body = page.locator("#messages").inner_text()
                assert "Hey! I'm Linda" in body, "welcome bubble missing"
                assert "render-probe-user-msg" in body, body
                assert "render-probe-agent-reply" in body, body
                # History renders BELOW the welcome bubble.
                assert body.index("Hey! I'm Linda") < body.index(
                    "render-probe-user-msg")
                browser.close()
        except Exception as e:  # noqa: BLE001
            if _skip_if_no_chromium(e):
                return
            raise
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Temp dir: {TMP}")
    check("memory", test_memory)
    check("approvals_auto", test_approvals_auto)
    check("approvals_ask_approve", test_approvals_ask_approve)
    check("approvals_ask_reject", test_approvals_ask_reject)
    check("files_tool", test_files)
    check("github_local", test_github_local)
    check("agent_loop_stub_brain", test_agent_loop_with_stub_brain)
    check("task_stop", test_task_stop)
    check("brain_ollama_unreachable", test_brain_ollama_unreachable)
    check("brain_retry_transient", test_brain_retry)
    check("brain_no_retry_permanent", test_brain_no_retry_on_permanent_error)
    check("gemini_reply_extraction", test_gemini_reply_extraction)
    check("gemini_empty_reply_retried", test_gemini_empty_reply_retried)
    check("gemini_empty_reply_gives_up", test_gemini_empty_reply_gives_up_cleanly)
    check("browser_live_view", test_browser_live_view)
    check("browser_tool_arg_aliases", test_browser_tool_arg_aliases)
    check("pwa_browser_live_wiring", test_pwa_browser_live_wiring)
    check("browser_control_state", test_browser_control_state)
    check("browser_user_input_forwarding", test_browser_user_input_forwarding)
    check("browser_panel_endpoints", test_browser_panel_endpoints)
    check("pwa_browser_panel_wiring", test_pwa_browser_panel_wiring)
    check("kaggle_no_creds", test_kaggle_no_creds)
    check("browser_headless", test_browser_headless)
    check("health_endpoint", test_health_endpoint)
    check("settings_masking", test_settings_masking)
    check("settings_write_and_validate", test_settings_write_and_validate)
    check("api_token_auth", test_api_token_auth)
    check("system_prompt_auto_language", test_system_prompt_auto_language)
    check("pwa_voice_wiring", test_pwa_voice_wiring)
    check("messaging_webhook_verification",
          test_messaging_webhook_verification)
    check("messaging_signature_and_parse",
          test_messaging_signature_and_parse)
    check("messaging_autoreply_engine", test_messaging_autoreply_engine)
    check("messaging_webhook_end_to_end", test_messaging_webhook_end_to_end)
    check("messaging_chat_control", test_messaging_chat_control)
    check("messaging_secure_credentials", test_messaging_secure_credentials)
    check("gmail_stub_search_and_parse", test_gmail_stub_search_and_parse)
    check("gmail_otp_extraction", test_gmail_otp_extraction)
    check("gmail_find_otp_window", test_gmail_find_otp_window)
    check("gmail_not_configured", test_gmail_not_configured)
    check("gmail_tools_and_prompt", test_gmail_tools_and_prompt)
    check("browser_persistent_profile", test_browser_persistent_profile)
    check("browser_fill_form", test_browser_fill_form)
    check("browser_fill_otp_stub", test_browser_fill_otp_stub)
    check("browser_fill_otp_user_code", test_browser_fill_otp_user_code)
    check("otp_code_redaction", test_otp_code_redaction)
    check("sms_otp_prompt", test_sms_otp_prompt)
    check("welcome_message_english", test_welcome_message_english)
    check("chat_ui_english_and_clean", test_chat_ui_english_and_clean)
    check("pwa_composer_resets", test_pwa_composer_resets)
    check("chat_history_store", test_chat_history_store)
    check("chat_history_endpoint", test_chat_history_endpoint)
    check("chat_history_redaction", test_chat_history_redaction)
    check("conversations_store", test_conversations_store)
    check("conversations_migration", test_conversations_migration)
    check("conversations_endpoint", test_conversations_endpoint)
    check("desktop_launcher", test_desktop_launcher)
    check("chat_history_ui_wiring", test_chat_history_ui_wiring)
    check("pwa_chat_history_renders", test_pwa_chat_history_renders)
    check("agent_tool_discipline", test_agent_tool_discipline)

    print()
    print(f"PASSED: {len(PASSED)}  FAILED: {len(FAILED)}  SKIPPED: {len(SKIPPED)}")
    if FAILED:
        print("Failed:", ", ".join(FAILED))
        sys.exit(1)
    print("All smoke tests passed.")
