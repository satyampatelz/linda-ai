# Delivery Notes — Linda v0.10.0

Built 24 Nov 2026. Source: `~/workspace/satyam-ai/` (build workspace directory kept as-is). Zip: `linda-ai-v0.10.zip` (top-level folder `linda-ai/`). APK: **NOT built in this VM — Flutter source only** (same sandbox Gradle block as v0.3; see the v0.3 section below).

## What's new in v0.10.0 (FULL REBRAND — Satyam is now Linda)

The user asked to rename the agent from "Satyam" to "Linda" and picked the **full rebrand**. Branding + version ONLY — all v0.9.1 functionality is untouched.

1. **New 3D "L" icon** — teal gemstone letter L with ornate gold filigree engravings and diamond-cut facets, layered translucent glass panels behind it, floating gold cubes/pyramids/spheres and sparkling gems around it, and the word "Linda" in small elegant gold serif letters below the L (a real 3D render, same teal-glass + gold style as the old S; the user picked this "filigree" design over the wireframe-cage option and asked for the name written in small letters). Applied everywhere from the master `design/icon-final-3d-linda.png` (512x512, rounded corners r=114, converted from the 1600px v5 webp source with PIL): PWA icons (`backend/static/icons/icon-180/192/512.png`), Android launcher icons (all 5 mipmap densities), Flutter asset `mobile_app/assets/icon.png` (512px), desktop `linda.ico` (7 sizes, 16–256px). The 512px master and the .ico's 256px frame were both visually checked — the L is well-formed, "Linda" is spelled correctly, the filigree and floating shapes survive, and the rounded corners cut nothing.
2. **Name change everywhere user-visible** — app display name, PWA manifest (`name`/`short_name`), welcome message ("Hey! I'm Linda — your personal AI agent…"), composer placeholder ("Tell Linda what to do…"), system prompt identity ("You are Linda"), auto-reply persona ("You are Linda, replying…"), FastAPI title, Flutter app title/labels, README + all guides, script echo messages, logger names (`linda.*`), env vars (`LINDA_ENV_FILE`, `LINDA_SERVER_URL`), Docker service/container/volume/network names, localStorage keys (`linda_api_token`, `linda_auto_speak`).
3. **File renames** — `desktop/Satyam.bat` → `desktop/Linda.bat`, `desktop/satyam.ico` → `desktop/linda.ico`, `deploy/satyam.service` → `deploy/linda.service`, Android package `com.satyam.agent` → `com.linda.agent` (kotlin dir + `MainActivity` package + `build.gradle.kts` namespace/applicationId + manifest label), `mobile_app` package name `satyam` → `linda`. Desktop shortcut is now "Linda" (`Linda.lnk`). All references updated (scripts, guides, README, deploy.sh, smoke tests).
4. **Deliberately NOT renamed** — the author's name "Satyam Patel" (license/personal lines, demo git config, test fixtures), the GitHub username "satyampatelz", the local build workspace directory `~/workspace/satyam-ai/`, and the internal SQLite file `data/satyam.db` (kept so existing chat history keeps working on upgrade — it is git-ignored, invisible, and not in the zip). `design/` mockups/screenshots from the Satyam era are unshipped history and were left alone, except the `media-generation-satyam-design-*` files, renamed to `linda-design-*` so the old DELIVERY_NOTES references stay valid.
5. **Versions** — 0.10.0 everywhere (config, `backend/__init__.py`, pubspec 0.10.0+12); service-worker cache bumped to v16 (`linda-shell-v16`). Upgrade: extract the new zip, copy the old `data/` and `workspace/` folders over, run `setup.bat` / `run.bat`; rebuild the APK from `mobile_app/README.md`. One rebrand side effect: the PWA's saved API token / auto-speak setting live under new localStorage keys, so cloud users re-enter the token once in Settings.

## What was tested HERE for v0.10.0 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` (backend, run.py, tests) | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`tests/smoke_test.py`, venv `~/.venvs/satyam`) | ✅ **45/45 passed, 0 failed, 0 skipped** |
| `flutter pub get` + `flutter analyze` | ✅ **"No issues found!"** |
| Live server boot + `/health` | ✅ PASS — `{"app":"Linda","version":"0.10.0",...}`; `/health/detailed` works (Ollama fail expected — Ollama isn't running in the VM); server stopped afterwards, port closed |
| Served UI spot-check (`/`, `/app.js`, `/manifest.json`, `/sw.js`) | ✅ PASS — "Linda" throughout (welcome, placeholder, manifest name/short_name, `linda-shell-v16`); **zero** "Satyam" in served `index.html`/`app.js` |
| Icon verification (PIL) — every generated icon at the right size; `.ico` parses with all 7 sizes; 512 master + .ico 256px frame visually checked | ✅ PASS |
| Final grep for "Satyam"/"satyam" | ✅ Only the deliberate leftovers listed above (author, username, `satyam.db`, workspace dir, unshipped `design/` history, generated `.dart_tool`) |
| Credential scan of zip | ✅ none |

## Caveats

- **No APK built** — same VM sandbox Gradle block as v0.3–v0.9.1 (not attempted). Flutter source is analyze-clean; the user rebuilds on his laptop per `mobile_app/README.md`.
- **No live Google calls or live sites** — all flows verified locally only.
- The `.bat`/`.ps1` launcher files are renamed but their Windows behavior is unchanged — still untested on real Windows (same as v0.9).
- The GitHub repo rename (`satyam-ai` → `linda-ai`) and push are NOT part of this build — handled separately.

---

# Delivery Notes — Linda v0.9.1

Built 23 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.9.1.zip`. APK: **NOT built in this VM — Flutter source only** (same sandbox Gradle block as v0.3; see the v0.3 section below).

## What's new in v0.9.1 (3D app icon — icon-swap release)

Icon-swap release: ONLY the icon artwork + version changed; all v0.9.0 functionality (desktop launcher, chat history, cloud URL support) is untouched. The user rejected the v0.9.0 "Double Orbit" look along with the A5/A6/A7 variants ("bahut ghatiya lag raha" — he wants better overall colour graphics, everything in 3D), then picked the FINAL icon: a **3D teal-glass S with gold rings** (glossy deep-teal glass letter S, thin metallic gold orbiting rings, soft light-blue background — a real 3D render). Applied everywhere from the master `design/icon-final-3d.png` (512x512, rounded corners r=114, converted from the 1600px webp source with PIL): PWA icons (`backend/static/icons/icon-180/192/512.png`), Android launcher icons (all 5 mipmap densities), desktop `linda.ico` (7 sizes, 16–256px). The 512px master and the .ico's 256px frame were both visually checked — the S is well-formed, the gold rings survive, and the rounded corners cut nothing important (the corners are plain background). Versions: 0.9.1 everywhere (config, `backend/__init__.py`, pubspec 0.9.1+11); service-worker cache bumped to v15.

## What was tested HERE for v0.9.1 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — **45 tests** (all v0.9.0 tests; version assertions updated to 0.9.1/v15) | ✅ **45 passed, 0 failed, 0 skipped** |
| `flutter pub get` + `flutter analyze` | ✅ **"No issues found!"** |
| Icon verification (PIL) — every generated icon opens at the right size (PWA 180/192/512, mipmap 48/72/96/144/192); `.ico` parses with all 7 sizes (16–256px); 512px master + .ico 256px frame read visually | ✅ PASS |
| Live server boot (`python run.py`) + `GET /health` (version 0.9.1, auto mode), `/`, `/health/detailed`, sw.js v15 | ✅ PASS — all HTTP 200 |
| Zip verified from extraction | ✅ compileall + 45/45 smoke tests on the extracted copy |
| Credential scan of zip | ✅ none (only known fake test placeholders in smoke_test.py) |

## What's new in v0.9.0 (desktop icon + chat history)

The user asked for the laptop experience to feel like a real app: "ek baar laptop ke screen par kaise bhi karke la le, click kare toh same apna chat sab khule" — a desktop icon, one click, his same chat opens. He also confirmed he wants it to keep working with the laptop OFF via the Oracle cloud VM, so the launcher supports a cloud server URL too. (Discussed first, built only after his go-ahead — "Hh bhai kro", debit card confirmed for Oracle signup.)

1. **Desktop icon + launcher** (`desktop/`): `create-shortcut.bat` (double-click once) runs `create-shortcut.ps1`, which creates a Desktop shortcut named "Linda" with the new **Double Orbit logo** as its icon (`linda.ico`, 7 sizes 16–256px, generated from `design/icon-opt-a4-double.png` with PIL). The shortcut runs `desktop/Linda.bat`: it reads the server URL from `desktop/server.txt` (or `LINDA_SERVER_URL`), and for a LOCAL URL (127.0.0.1/localhost) checks `/health` (curl, PowerShell fallback) — if the server is down it starts it in its own minimized window (`.venv\Scripts\python.exe run.py`) and waits up to ~60s for `/health`. Then it opens the chat in a standalone app-mode browser window (Chrome `--app=`, Edge fallback, default browser last resort). No console window is left hanging. `-AutoStart` flag (via `create-shortcut.bat -AutoStart`) also drops the shortcut in the Windows Startup folder, so the server starts with Windows.
2. **New app icon everywhere** (user picked "Double Orbit" as the FINAL icon — cool sky-to-teal-to-mint gradient, white S, double crossing orbit rings, no dot): the PWA icons (`backend/static/icons/icon-180/192/512.png`), the Android launcher icons (all 5 mipmap densities), and the desktop `.ico` are all generated from `design/icon-opt-a4-double.png`. The in-app header logos are drawn in code (CSS/Dart), not image files, so there was nothing else to replace. (History: the first "Orbit S" option was applied, then rejected by the user — he said it looks copied from Instagram — and fully reverted before this final pick.)
3. **Cloud URL support**: put the Oracle VM URL in `desktop/server.txt` and the launcher skips starting anything local — it just opens the cloud server. Laptop off → work still runs on the VM; the user checks results later from his phone. Guide: `desktop/DESKTOP_GUIDE.md` (Hinglish + English: one-time setup, daily use, cloud URL, auto-start, troubleshooting).
4. **Chat history persists** (backend SQLite `messages` table in `data/satyam.db`): every user message (saved in `POST /chat`) + every agent final reply (saved in `TaskStore.finish`/`stop` — the exact text the bubble shows, errors as "Error: ...") is stored, capped at the newest 200 with automatic pruning. `GET /chat/history` serves the transcript oldest-first; it is API-token protected like the other `/chat` routes. The PWA (`loadChatHistory`) and the Flutter app (`getChatHistory`) both load it on start and render it below the welcome bubble — the welcome always stays on top. Restored agent replies get working speaker buttons; error replies keep their red bubble.
5. **Security**: one-time codes are never persisted — `redact_otp_text` runs on both save paths (user message in `/chat`, agent reply in `finish`/`stop`), and the test verifies it through the real `POST /chat` + task-finish paths, not just the helper.
6. **Versions:** 0.9.0 everywhere (config, `backend/__init__.py`, pubspec 0.9.0+10); service-worker cache bumped to v14.

## What was tested HERE for v0.9.0 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — **45 tests**: all 39 v0.8.3 tests (voice-wiring test updated to v0.9.0/v14) + 6 new v0.9.0 tests (chat-history store round-trip + order + 200-cap pruning; /chat/history endpoint + API-token protection; OTP redaction through the real POST /chat + task-finish paths; desktop launcher static checks incl. ICO header parse; chat-history UI wiring in PWA + Flutter; Playwright check that seeded history renders below the welcome bubble against a live server) | ✅ **45 passed, 0 failed, 0 skipped** |
| `flutter pub get` + `flutter analyze` (Flutter 3.38.1, Dart 3.10.0) | ✅ PASS — **"No issues found!"** |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.9.0, auto mode), `/`, `/chat/history` (seeded messages returned oldest-first), sw.js v14 | ✅ PASS — all HTTP 200 |
| Zip verified from extraction | ✅ compileall + 45/45 smoke tests on the extracted copy |
| No live Google calls, no live sites | ✅ All flows verified locally only |

**Honest caveat — not testable in this VM:** the `.bat` / `.ps1` launcher scripts only run on real Windows. They were checked statically (right commands, paths, fallbacks; the `.ico` header-parsed + PIL-verified), but the user will be the first to run them on his laptop. If anything breaks there, it gets fixed from his screenshot.

---

# Delivery Notes — Linda v0.8.3

Built 23 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.8.3.zip`. APK: **NOT built in this VM — Flutter source only** (same sandbox Gradle block as v0.3; see the v0.3 section below).

## What's new in v0.8.3 (clean chat screen)

Small cleanup release — the user said the chat screen had too much useless text ("chat me bahut faltu ka kuchh likha hua tha"). Now only the welcome message is there — the chat looks completely fresh and clean, in BOTH the PWA and the Flutter app.

1. **Welcome bubble is the greeting ONLY** (PWA `backend/static/index.html` + Flutter `mobile_app/lib/screens/chat_screen.dart`): "Hey! I'm Linda — your personal AI agent. Just tell me what you need, and I'll get it done." The capabilities paragraph ("writing code, pushing to GitHub, researching the web and making Excel sheets, Kaggle work — anything") and the first-time hints paragraph ("First time here? Tap Status above…") are both gone.
2. **Composer placeholder is English now**: "Tell Linda what to do…" (was "Linda ko koi kaam bolo…") — PWA + Flutter, including the listening-state placeholder ("Listening…").
3. **All chat-visible toasts/hints are short clean English**: voice toasts (browser support, mic permission, start failures), the listening pill ("Listening… speak — tap the mic again to stop"), the steps empty state ("Your agent's steps will appear here live."), the working bubble ("Working…"), task fallbacks ("Done." / "Task stopped." / "something went wrong."), the stop toast, the approval card title ("Approval needed"), the secure credential box (note, field hints, button, errors), and the Flutter voice/API error strings. The Settings/Status modals keep their Hinglish fix hints — those are separate screens, not the chat.
4. **Header cleanup**: the model subtitle under the "Linda" title (the "Ollama (qwen2.5:3b) • auto mode" line) is gone — PWA `#statusLine` element + JS wiring removed, Flutter `_statusLine` removed from the AppBar. The brain info still lives in the Status panel; the online/offline pill stays. Dead `.brand-text p` CSS rules removed too.
5. **Versions:** 0.8.3 everywhere (config, `backend/__init__.py`, pubspec 0.8.3+9); service-worker cache bumped to v13.

## What was tested HERE for v0.8.3 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — **39 tests**: all 38 v0.8.2 tests (welcome test updated to the greeting-only bubble, voice-wiring test updated to v0.8.3/v13/English strings) + 1 new v0.8.3 test (English placeholder + listening hint + steps text in both apps, no Hinglish chat strings in any chat UI file, no model subtitle anywhere) | ✅ **39 passed, 0 failed, 0 skipped** |
| `flutter pub get` + `flutter analyze` (Flutter 3.38.1, Dart 3.10.0) | ✅ PASS — **"No issues found!"** (one unused-variable warning from the removed subtitle fixed during the build) |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.8.3, auto mode), `/`, sw.js v13, served welcome greeting-only, placeholder English, no statusLine in DOM | ✅ PASS — all HTTP 200 |
| Clean chat screenshot (headless Chromium, 390×844) — `design/v0.8.3-chat.png` | ✅ Verified visually — only the welcome bubble, composer, and header controls |
| Zip verified from extraction | ✅ compileall + 39/39 smoke tests on the extracted copy |
| No live Google calls, no live sites | ✅ All flows verified locally only |

---

# Delivery Notes — Linda v0.8.2

Built 23 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.8.2.zip`. APK: **NOT built in this VM — Flutter source only** (same sandbox Gradle block as v0.3; see the v0.3 section below).

## What's new in v0.8.2 (English welcome + composer snap-back)

Small fix release — two things the user asked for after watching the demo video.

1. **Welcome message is English now** (PWA `backend/static/index.html` + Flutter `mobile_app/lib/screens/chat_screen.dart`): "Hey! I'm Linda — your personal AI agent. Just tell me what you need, and I'll get it done…" — the app no longer greets a first-time user with a fixed Hinglish greeting. The standing language rule is unchanged: default English, and the brain auto-adapts to whatever language/script the user chats in. The system prompt line was strengthened to say so explicitly — "from their very first message, no matter what language they start in". No language setting or picker was added anywhere (the user rejected that idea in v0.2.1).
2. **Composer snaps back to one line on send** (PWA `backend/static/app.js`): the grow logic is now one shared `autosizeComposer()` function (used by the input listener), and the submit handler drops the inline height entirely (`removeProperty("height")`) after clearing — so no stale two-line height can survive the programmatic clear. Verified live in Chromium: type two lines → send (button and Enter key) → composer is single-line height within 50ms. The Flutter composer (`TextField`, minLines 1 / maxLines 4 + `controller.clear()`) was checked and needs no fix — Flutter sizes the field to its content, so clearing shrinks it on the next frame automatically.
3. **Versions:** 0.8.2 everywhere (config, `backend/__init__.py`, pubspec 0.8.2+8); service-worker cache bumped to v12.

## What was tested HERE for v0.8.2 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — **38 tests**: all 36 v0.8.1 tests + 2 new v0.8.2 tests (welcome is English in PWA + Flutter, no Hinglish greeting, auto-adapt prompt wording, no language setting; Playwright composer check against a live server — two lines typed, send, single-line height after) | ✅ **38 passed, 0 failed, 0 skipped** |
| `flutter pub get` + `flutter analyze` (Flutter 3.38.1, Dart 3.10.0) | ✅ PASS — **"No issues found!"** (chat_screen.dart welcome text changed) |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.8.2, auto mode), `/`, `/health/detailed`, sw.js v12, served welcome English | ✅ PASS — all HTTP 200 |
| Welcome screenshot (headless Chromium, 390×844) | ✅ Verified visually — clean, no clipping |
| Zip verified from extraction | ✅ compileall + 38/38 smoke tests on the extracted copy |
| No live Google calls, no live sites | ✅ All flows verified locally only |

---

# Delivery Notes — Linda v0.8.1

Built 23 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.8.1.zip`. APK: **NOT built in this VM — Flutter source only** (same sandbox Gradle block as v0.3; see the v0.3 section below).

## What's new in v0.8.1 (SMS OTP ask-and-fill)

The user corrected the v0.8 behavior: when a site asks for an **SMS** OTP, the agent must NOT tell him to fill it himself in the visible browser. Instead it ASKS him in chat for the code ("SMS pe aaya OTP bhejo"), and when he replies with the code, it FILLS it into the site itself and continues the task. Email OTPs stay fully automatic (Gmail → fill, never ask). CAPTCHA still needs the user in the visible browser (unchanged).

1. **`browser_fill_otp` now takes an optional `code`** (`backend/app/tools/browser_tool.py`): `browser_fill_otp(code="482916")` fills the user-provided code directly — Gmail is never consulted on that path, the code is validated (4–8 digits) and used once for the fill. Same field-finding as before (autocomplete=one-time-code, name/id/placeholder, multi-box single-char inputs). The code is never echoed in the result, whatever the source. When the Gmail lookup finds no email OTP, the tool now tells the agent the OTP is probably SMS and to ask the user in chat (instead of the old "tumhe khud bharna hoga").
2. **The OTP page stays open between the ask and the reply.** Verified: the browser is a module-level singleton (`browser_tool.browser`) whose page is only closed by the `browser_close` tool — nothing closes it between agent turns, so the OTP page is still there when the code arrives. The system prompt now explicitly says: do NOT close the browser while waiting for the SMS code.
3. **System prompt rewrite** (`backend/app/agent.py`): the old "SMS OTP — tell the user to fill it himself in the visible browser" wording is gone from both places (RULES browser line + GMAIL OTP section). New flow: email OTP → Gmail, never ask; no email OTP found → finish with one short ask ("SMS pe aaya OTP bhejo"), wait; user replies with a 4–8 digit code → treat it as the SMS OTP, check the page (browser_read), fill with `browser_fill_otp(code=...)`, continue (Verify/Submit). Never repeat the code in the answer, never save it.
4. **One-time code handling** (`agent.py` + `main.py`): the code the user types is used immediately for the fill and never stored anywhere — no memory, no task DB, no log, no step history. `redact_otp_text()` masks bare-code messages (and otp/code + digits) at every persistence boundary: `task_store.create` (Tasks list), every `memory.log_task` call (message + answer), `TaskStore.add_step` (masks the `code` arg on `browser_fill_otp` steps and redacts finish answers), and the bad-tool-call log line. The LLM still sees the original message — it needs the digits to fill the form. Also updated the `find_otp` not-found message to steer the agent to ask for the SMS code.
5. **Docs**: `GMAIL_SETUP.md` (SMS OTP row in the chat table + limits bullet rewritten), README (troubleshooting + Limits + v0.8.1 changelog entry). **Versions:** 0.8.1 everywhere (config, `backend/__init__.py`, pubspec 0.8.1+7); service-worker cache bumped to v11. No PWA/Flutter UI changes (everything is chat-driven) — the only mobile_app touch is the version string.

## What was tested HERE for v0.8.1 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — **36 tests**: all 33 v0.8 tests + 3 new v0.8.1 tests (user-provided code fill on a local OTP page — single field + multi-box, Gmail never consulted, page still open across the ask gap; code-never-stored redaction — helper, step args, task store, DB log; system prompt ask-and-fill wording + no "fill it yourself" text) | ✅ **36 passed, 0 failed, 0 skipped** |
| `flutter pub get` + `flutter analyze` (Flutter 3.38.1, Dart 3.10.0) | ✅ PASS — **"No issues found!"** (only the version string in pubspec.yaml changed; no Dart files touched) |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.8.1, auto mode), `/`, `/health/detailed` | ✅ PASS — all HTTP 200 |
| Zip verified from extraction | ✅ compileall + 36/36 smoke tests on the extracted copy |
| No live Google calls, no live sites | ✅ OTP flows verified against local test pages + stubbed Gmail only |

---

# Delivery Notes — Linda v0.8.0

Built 23 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.8.zip`. APK: **NOT built in this VM — Flutter source only** (same sandbox Gradle block as v0.3; see the v0.3 section below).

## What's new in v0.8.0 (Gmail + email OTP auto-fill + Google auto sign-in + form filling)

The user wants Linda to "do everything": read his Gmail, open sites like Internshala and check them, fill any form, auto sign-in with Google, and read OTPs from Gmail and fill them automatically. All of it is in this release — official APIs only, no unofficial libraries, no login automation that fakes a human.

1. **New module `backend/app/gmail/`** — `client.py` (OAuth 2.0, **read-only** scope `gmail.readonly` — the agent can never send/delete/modify mail; token in `data/token.json`, auto-refresh; `client_secret.json` at project root or in `data/`, both git-ignored), `otp.py` (OTP extraction + recent-mail lookup), `auth.py` (one-time CLI: `python -m backend.app.gmail.auth` — local browser consent flow). Message parsing handles plain text, multipart (plain preferred), and HTML-only mail (tags stripped). Nothing here ever launches a browser on its own — without a token, the tools return a clear Hinglish setup message pointing at GMAIL_SETUP.md.
2. **Brain tools `read_gmail` + `find_otp`** (`backend/app/tools/gmail_tool.py`, registered in `agent.py`): `read_gmail` searches/lists mail with Gmail search syntax ("from:internshala", "newer_than:2d", plain words); `find_otp` finds the OTP in a recent email from a site/sender. OTP extraction is keyword-proximity first ("Your OTP is 482916", "aapka code: 7392"), standalone-6-digit fallback, years (1900–2099) and long numbers never matched. **Time window enforced in code**: only emails from the last N minutes (default 10) count — a stale OTP is never used.
3. **Browser upgrades** (`backend/app/tools/browser_tool.py`):
   - **Persistent Chromium profile** (`launch_persistent_context`, `data/browser-profile/`, git-ignored): logins and cookies survive server restarts. Once the user signs in to Google once in the agent's browser, "Sign in with Google" on other sites just works.
   - **`browser_fill_form(url, fields, submit=True)`**: fills a whole form — fields matched by label, name, or placeholder (in that order); text/textarea/select/checkbox supported; submits via the submit button (or Enter fallback) and reports what was filled, what was skipped, and where the page ended up.
   - **`browser_fill_otp(sender, minutes=10)`**: finds the OTP field on the current page (autocomplete=one-time-code, name/id/placeholder match, or multi-box single-char inputs), reads the code from Gmail, fills it. **The code is never echoed back** in the result, logs, or chat.
4. **Internshala site profile** (`site-profiles.yaml`): login URL + where applications/messages live, in plain words (no hardcoded selectors, per the file's own rule). The system prompt now tells the agent to read `site-profiles.yaml` with files_read when a task names a known site — so "Internshala check karo" works out of the box.
5. **System prompt**: new GMAIL section (read/search/OTP, Hinglish + English phrasings) and BROWSER FORMS + GOOGLE SIGN-IN section (persistent login, form filling, never invent form values). The old "CAPTCHA or OTP — stop and tell the user" rule is now precise: CAPTCHA and **SMS** OTPs still need the user; **email** OTPs are read from Gmail and filled by the agent.
6. **Status panel Gmail check** (`health.py`): skip when Gmail is not set up at all (it's optional), fail with a Hinglish hint when client_secret exists but the one-time auth was never done, ok when token.json exists.
7. **Guide `GMAIL_SETUP.md`** (Hinglish + English, non-developer step-by-step): Google Cloud project → enable Gmail API → OAuth consent screen (External, test mode) → readonly scope → download client_secret.json → one-time auth → done. Plus the Google sign-in part (once, in the visible browser; cloud VM: copy `data/browser-profile/` from the laptop). Honest notes: only EMAIL OTPs (no SMS), CAPTCHA stays human, some sites block automation, OTPs expire (10-minute window), one Gmail account only, form values must come from the user.
8. **Versions:** 0.8.0 everywhere (config, `backend/__init__.py`, pubspec 0.8.0+6); service-worker cache bumped to v10. No PWA/Flutter UI changes (everything is chat-driven) — the only mobile_app touch is the version string. README.md capability row + changelog + Limits/Troubleshooting updates (OTP row now says email OTPs auto-fill), `.gitignore` gains `client_secret.json` + `token.json`.

## What was tested HERE for v0.8.0 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| Clean-venv `pip install -r requirements.txt` (fresh venv, incl. new google-api-python-client + google-auth-oauthlib) | ✅ PASS — installs clean, imports ok. (Note: this VM's /tmp is a 512M tmpfs that fills up during pip installs — the clean install needed `TMPDIR` pointed at the main disk. Not a project issue.) |
| Smoke tests (`python tests/smoke_test.py`) — **33 tests**: all 25 v0.7 tests + 8 new v0.8 tests (stubbed Gmail search/parse incl. multipart + HTML fallback, OTP extraction incl. no-match + year rejection, OTP time-window fresh/stale, not-configured behaviour, Gmail tools + system prompt + Internshala profile, persistent-profile cookie survives close/relaunch, form fill + submit on a local test page, OTP auto-fill on a local test page incl. multi-box + code-never-echoed) | ✅ **33 passed, 0 failed, 0 skipped** |
| `flutter pub get` + `flutter analyze` (Flutter 3.38.1, Dart 3.10.0) | ✅ PASS — **"No issues found!"** (only the version string in pubspec.yaml changed; no Dart files touched) |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.8.0, auto mode), `/`, `/health/detailed` (Gmail check present) | ✅ PASS — all HTTP 200 |
| Zip verified from extraction | ✅ compileall + 33/33 smoke tests on the extracted copy |
| No live Google calls | ✅ No credentials exist in this VM — Gmail sends/searches were verified with a stubbed service only; the user must do the Google Cloud setup himself (see GMAIL_SETUP.md) |

---

## What's new in v0.7.0 (Chat-controlled messaging + in-chat secure box)

The user changed how messaging should be controlled: **not from Settings — by talking to Linda in chat.** "Ab se Instagram ke messages dekhna" → auto-reply ON, replies without asking; "WhatsApp band kar do" → OFF. And when a token is missing, he wants a **secure box in the chat** (like Muse's secure vault card) — a masked input card in the conversation, never a plain chat message — instead of `.env` being the only path. `.env` stays as an alternative for advanced users.

1. **Messaging removed from Settings (PWA + Flutter):** the whole messaging section — toggles + token/ID/verify-token/app-secret fields — is gone from the PWA Settings modal and the Flutter Settings screen. Backend config keys stay (tokens still live in `.env`), but Settings has nothing to do with messaging any more. `GET /settings` returns no `whatsapp_*`/`instagram_*` keys; `POST /settings` with a messaging key is ignored.
2. **Brain tool `set_messaging(platform, enabled)` + `get_messaging_status()`** (`backend/app/tools/messaging_tool.py`, registered in `agent.py`): the agent calls it when the user asks in chat to start/stop watching WhatsApp or Instagram. Platform aliases (`wa`, `ig`, `insta`) for small local models. The agent confirms once in plain Hinglish ("Ho gaya — ab se Instagram ke messages ka reply main khud dunga, tujhse nahi puchunga") and then just does it. The system prompt has a MESSAGING section describing the capability (Hinglish + English phrasings) and the secure-box line — never ask for the token as a chat message.
3. **ON/OFF state in SQLite, default OFF** (`msg_control` table in `data/satyam.db`): a platform only starts auto-replying when the user says so in chat, and the state survives restarts. The v0.6 `.env` toggles `WHATSAPP_ENABLED`/`INSTAGRAM_ENABLED` are removed — **migration note:** a platform that was ON in v0.6 via Settings is OFF in v0.7 until the user says "ab se ... dekhna" once in chat. The v0.6 auto-reply engine itself is unchanged (official Meta APIs, webhooks, 24h window, dedupe, rate limit, replies as Linda in the sender's language) — it just reads `enabled` from the store now instead of settings.
4. **Secure box (the new credential path):** when the user enables a platform whose token/ID is missing, the tool records a pending request (`msg_pending_credential` table — platform + field names only, never values) and says once what is missing. The chat UI polls `GET /messaging/pending` (after every task + on load) and renders a **masked input card in the chat flow** — PWA (`backend/static/app.js` + `.secure-card` styles in `style.css`, custom lock SVG, password inputs for token/verify/app_secret, plain input for the ID) and Flutter (`_SecureCredentialCard` in `chat_screen.dart`, `obscureText` fields, new custom `lock.svg` icon). `POST /messaging/credentials` saves to `.env` via `save_messaging_credentials` (same masking pattern as the Gemini key — never echoed back in chat, never logged, never shown in full; response carries masked previews only), then `complete_setup()` **auto-enables the platform the moment token + target id are present** — paste once, auto-reply starts. Both `/messaging/*` endpoints are behind the API-token middleware; `/webhook/*` stays public. If token+ID are set but the verify token is missing, enabling still works and the secure box is offered once for the webhook fields (otherwise Meta never delivers messages).
5. **Status panel readiness checks kept** (diagnostics, not controls) — their hints now point at the chat commands + secure box.
6. **Docs:** `MESSAGING_SETUP.md` rewritten — secure box first (Part C: "chat me bolo, secure box me paste karo, auto-reply chalu"), `.env` by hand as the advanced alternative, all "Settings me daalo" references gone. `README.md` capability row + changelog, `mobile_app/README.md` Settings row updated. Version strings 0.7.0 everywhere; service-worker cache bumped to v9 (installed PWAs pick up the new UI on next launch).

## What was tested HERE for v0.7.0 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — **25 tests**: all 19 v0.5 tests + the 4 unchanged v0.6 messaging tests (webhook verification, signature+parsers, engine with stub brain/sender, webhook e2e with mock payloads) + 2 new v0.7 tests replacing the old messaging-settings test: `messaging_chat_control` (set_messaging enable/disable persists, aliases, verify-token-missing branch, missing-token blocker + pending request, Settings UI has no messaging fields anywhere, secure-box wiring in PWA + Flutter, system prompt) and `messaging_secure_credentials` (POST saves to temp .env + masked-only response + auto-enable, 400 on bad values/unknown platform, GET /pending lists then empties) | ✅ **25 passed, 0 failed, 0 skipped** |
| `flutter pub get` (Flutter 3.38.1, Dart 3.10.0) | ✅ resolved |
| `flutter analyze` | ✅ PASS — **"No issues found!"** |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.7.0, auto mode), `/`, `/messaging/pending` | ✅ PASS — all HTTP 200 |
| Headless-browser check (Playwright, mobile 390×844) — pending row seeded into the DB, secure card renders in chat (3 fields, token inputs masked), Settings modal has no messaging section, zero page errors | ✅ PASS — screenshots: `design/v0.7-secure-card.png`, `design/v0.7-settings.png` |
| No live Meta API calls | ✅ No tokens exist in this VM — sends were verified with stub senders only; the user must do the Meta setup himself (see MESSAGING_SETUP.md) |

---

## What's new in v0.6.0 (WhatsApp + Instagram auto-reply — official Meta APIs)

The user asked for what Muse doesn't do: his own agent should **auto-manage WhatsApp and Instagram chats by itself** — read an incoming DM, understand it, and reply on its own, without asking him again and again what to say. He picked the **official (safe)** route over the quick unofficial one, so this release uses only Meta's official APIs — no Baileys, no whatsapp-web.js, no instagrapi, no login automation, no ban risk from the integration itself.

1. **New module `backend/app/messaging/`** — `whatsapp.py` (Cloud API send via Graph API v26.0 + webhook parser), `instagram.py` (Messaging API send via `/{page-id}/messages` + webhook parser), `signature.py` (HMAC-SHA256 verification of `X-Hub-Signature-256`), `store.py` (SQLite dedupe + per-contact history + 24h-window timestamps in the same `data/satyam.db`), `autoreply.py` (the engine), `webhooks.py` (FastAPI router).
2. **Auto-reply engine:** on an inbound text DM — check the platform is ON + configured, dedupe by message id (Meta redelivers; a duplicate never gets a second reply), enforce Meta's **24-hour customer-service window** (outside it: skip + log, never send), per-contact **rate limit** (30 replies/hour, loop guard only), load the last 10 turns of per-contact history, call the existing brain (Ollama/Gemini router) with a persona prompt that replies **as Linda himself** — casual, 1–3 sentences, in the **same language/script as the incoming message** (English/Hindi/Hinglish, English default) — then send via the right client. Groups are a non-issue: the WhatsApp Cloud API doesn't deliver group messages and the Instagram Messaging API doesn't support group messaging at all (both documented in code). The engine never raises — every failure is a logged skip, so one bad message can't crash the webhook.
3. **Webhooks:** `GET /webhook/whatsapp` + `GET /webhook/instagram` (Meta verification handshake: `hub.mode`/`hub.verify_token`/`hub.challenge`), `POST` for both (signature check when an app secret is set, non-text events/statuses/echoes ignored, every POST answers 200 immediately and replies on a background thread). Deliberately NOT behind the Linda API-token middleware — Meta's servers can't carry it; the verify token + app-secret signature are the auth.
4. **Controls:** per-platform ON/OFF toggles + token / phone number ID / page ID / verify token / app secret fields in Settings — PWA Settings modal **and** Flutter Settings screen. Toggles default ON, so a platform starts auto-replying the moment its token + id are configured. Tokens are masked in `/settings` responses (same pattern as the Gemini key) and stored in `.env`, never in the repo. Status panel gains two readiness checks (`whatsapp_autoreply`, `instagram_autoreply`): skip when unconfigured, fail with a Hinglish hint when partially configured, ok when ready.
5. **Setup guide `MESSAGING_SETUP.md`** (Hinglish + English, written for a non-developer): Meta developer account → app → WhatsApp product + test number → permanent token via System User → webhook URL (laptop: free ngrok; 24×7: Oracle cloud URL) → verify token → test; Instagram: Business/Creator account → link Facebook Page → Page access token → webhook. Honest notes: 24h window, ~1,000 free WhatsApp service conversations/month, test mode limited to 5 registered numbers / test users (full public use needs Meta app review), replies go out as Linda.
6. **Backend:** version strings bumped to 0.6.0 everywhere; service-worker cache bumped to v8 (installed PWAs pick up the new Settings UI on next launch).

## What was tested HERE for v0.6.0 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — 24 tests: all 19 v0.5 tests + 5 new messaging tests (webhook verification handshake, HMAC signature valid/bad/missing-secret + parsers, auto-reply engine with stub brain + stub sender: reply/dedupe/24h-window/rate-limit/platform-off/unconfigured, end-to-end webhook POST with mock payloads incl. double-delivery dedupe, messaging settings save/mask/validate) | ✅ **24 passed, 0 failed, 0 skipped** |
| `flutter pub get` (Flutter 3.38.1, Dart 3.10.0) | ✅ resolved |
| `flutter analyze` | ✅ PASS — **"No issues found!"** |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.6.0, auto mode), `/` | ✅ PASS — all HTTP 200 |
| Headless-browser check (Playwright, mobile 390×844) | ✅ PASS — Settings modal shows the new messaging section, zero page errors |
| No live Meta API calls | ✅ No tokens exist in this VM — sends were verified with stub senders only; the user must do the Meta setup himself (see MESSAGING_SETUP.md) |

---

## What's new in v0.5.0 (Interface redesigned — high-quality original graphics, user feedback)

The user looked at the v0.4.1 screenshot, cropped the demo chips row, and said three things: (1) remove those suggestion chips, (2) the mic looks copied from Google and the whole interface looks copied/stock, (3) make the interface high-quality graphics. He was right about the mic — v0.4.1 used Google's Material mic path. This release fixes all three, in the PWA **and** the Flutter app. No behaviour change — chat, voice, settings, status, tasks all work exactly as before.

1. **Demo chips removed (PWA + Flutter):** no "Kya kar sakte ho?" / "GitHub project banao" / "Research + Excel report" chips anywhere. The composer sits clean at the bottom. The demo prompts still live in `DEMO_GUIDE.md`. The welcome bubble's third line was updated to match (it used to point at the demo buttons).
2. **All icons are custom hand-drawn SVG paths** — no Material Icons, no icon fonts, no emoji anywhere in the UI. One icon set, drawn from scratch for this app (same paths inlined in the PWA and shipped as files in `mobile_app/assets/icons/`, rendered in Flutter via `flutter_svg` + a `LindaIcon` widget):
   - **Mic (the hero detail):** an original "orbit mic" — a gradient capsule with grille slots, wrapped by a tilted elliptical orbit ring with a satellite dot, on a slim stem with a curved smile base. Deliberately nothing like Google's mic.
   - **Speaker:** a rounded cone with three equalizer bars instead of the usual arcs.
   - **Send:** a hand-drawn paper plane with a faint fold line. **Stop:** rounded square. **Gear:** an 8-tooth gear computed geometrically (root/tip arcs + even-odd centre hole). **Pulse/status:** rounded tile + heartbeat line. **Chat/tasks/list/refresh:** matching originals. **Health icons:** filled green/red/grey circles + white check/cross/dash.
   - The listening state (red button, white mic) and speaking state (gradient badge, white speaker) still work — the PWA overrides only the gradient-painted parts via attribute selectors, so the ring keeps its stroke-only shape; Flutter tints the whole glyph with a `ColorFilter`.
3. **Interface polish:** smoother, more sophisticated pastel background (sky → periwinkle → lavender → lilac-rose → peach → warm cream) with four soft ambient glows; glass bubbles with layered soft shadows + fine light borders + inner highlights; refined spacing and typography rhythm; premium send button (layered shadow + inner top highlight); welcome bubble with a gradient accent bar and a divider above the hint line; the mic button gets a soft violet glow ring.
4. **Backend:** version strings bumped to 0.5.0 everywhere; service-worker cache bumped to v7 (installed PWAs pick up the new UI on next launch).

## What was tested HERE for v0.5.0 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — 19 tests incl. PWA voice wiring (SW cache v7; `/health` reports 0.5.0) + v0.5 guards (no chips, no emoji, no Material icons, custom icon assets present) | ✅ **19 passed, 0 failed, 0 skipped** |
| `flutter pub get` (Flutter 3.38.1, Dart 3.10.0) | ✅ resolved (flutter_svg added) |
| `flutter analyze` | ✅ PASS — **"No issues found!"** |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.5.0, auto mode), `/` | ✅ PASS — all HTTP 200 |
| Headless-browser check (Playwright, mobile 390×844 + desktop 1280×800) | ✅ PASS — mic/listening state, settings modal, health modal with new SVG icons; zero page errors |
| Visual check (screenshots read + inspected) | ✅ PASS — `design/v0.5-screenshot.png` (mobile chat view: clean composer, orbit mic, paper-plane send, speaker badge, no chips), `design/v0.5-check-desktop.png` (desktop), `design/v0.5-check-listening.png` (listening state) — original, premium, no stock feel |

---

## What's new in v0.4.1 (Voice buttons redesigned — user feedback)

The user looked at the v0.4 screenshot and said the mic button "sahi nhi lag raha": it was a plain 🎤 emoji in a small white circle next to the premium gradient send button, and the speaker was a tiny detached circle floating off the bubble. This release redesigns both buttons in the PWA **and** the Flutter app. No behaviour change — same voice logic, same auto-speak toggle.

1. **Mic button (PWA + Flutter):** a proper designed microphone icon (inline SVG in the PWA, Material `Icons.mic` in the app) painted with the accent gradient (sky → violet → orange), in a 44px glass circle the same size as the send button, with a matching soft violet shadow. Listening state unchanged in behaviour: red gradient background + white mic glyph + pulse + "Sun raha hoon…" hint (the hint pill now carries the same gradient mic icon instead of the emoji).
2. **Speaker button (PWA + Flutter):** a proper speaker icon (SVG `volume_up` / Material `Icons.volume_up`) with the gradient glyph, now a 32px badge overlapping the agent bubble's bottom-right corner instead of a floating circle. While speaking it turns into the full accent gradient with a white glyph.
3. **Backend:** version strings bumped to 0.4.1 everywhere; service-worker cache bumped to v6 (installed PWAs pick up the new UI on next launch).

## What was tested HERE for v0.4.1 (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — 19 tests incl. PWA voice wiring (SW cache v6; `/health` reports 0.4.1) | ✅ **19 passed, 0 failed, 0 skipped** |
| `flutter pub get` (Flutter 3.38.1, Dart 3.10.0) | ✅ resolved |
| `flutter analyze` | ✅ PASS — **"No issues found!"** |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3. Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.4.1, auto mode), `/` | ✅ PASS — all HTTP 200 |
| Headless-browser check (Playwright, mobile 390×844) | ✅ PASS — mic tap enters listening state, second tap stops it; zero page errors |
| Visual check (screenshots read + inspected) | ✅ PASS — `design/v0.4.1-screenshot.png` (chat view: gradient mic next to send, speaker badge on welcome bubble), `design/v0.4.1-check-listening.png` (listening state), `design/v0.4.1-check-speaking.png` (speaking state) — premium, consistent with the Light Colourful design |

---

## What's new in v0.4 (Voice — mic input + spoken replies, PWA + Flutter app)

Chatting in Linda should feel like chatting with Muse: tap the mic, talk, and hear replies spoken back. All voice work is **fully client-side and free** — no API keys, no server cost, no backend LLM change. Everything from v0.3 still works.

1. **PWA voice** (`backend/static/`):
   - **🎤 Mic button** next to Send: tap → records via the browser Web Speech API (`SpeechRecognition`, `en-IN` first for English+Hinglish, `hi-IN` fallback if the device has no en-IN recognizer). While listening: pulsing red mic + "🎤 Sun raha hoon…" hint pill + placeholder change. The transcript lands in the composer for editing — **never auto-sent**. Tap again (or pause) to stop.
   - **🔊 Speaker button** on every finished agent message (including the welcome bubble): tap to hear it aloud via `speechSynthesis` (prefers an en-IN voice, rate 0.95); tap again to stop. Long replies are chunked into sentences; code blocks are skipped, not read aloud.
   - **Auto-speak toggle** in Settings (default **OFF**, browser-localStorage only — not a server setting): reads every finished reply aloud automatically. Stop button / a new message silences it.
   - **Robustness:** everything is feature-checked. Browsers without SpeechRecognition (Firefox/Safari) show a clean Hinglish hint toast on mic tap instead of breaking ("Is browser me voice input nahi chalta — Chrome me try karo"); the app works identically without speech APIs.
2. **Flutter app voice** (`mobile_app/`, new `lib/voice.dart` + `speech_to_text ^7.4.0` + `flutter_tts ^4.2.5`): same behaviour — mic button in the composer (tap → listen → text in composer, no auto-send), speaker icon on agent messages, auto-speak toggle in Settings (default OFF, stored in secure storage). Mic permission handled gracefully: first tap asks Android; if denied, a clear message tells the user where to enable it (Settings → Apps → Linda → Permissions). `RECORD_AUDIO` added to AndroidManifest. Note: `speech_to_text` is pinned to `^7.4.0` (not 7.5.0) because 7.5.0 needs Dart ≥3.12 and the build VM has Dart 3.10; on the user's laptop with newer Flutter, `^7.4.0` resolves to 7.5.x, whose API is compatible with the `SpeechListenOptions` code used here.
3. **Backend:** version strings bumped to 0.4.0 everywhere; service-worker cache bumped to v5 (installed PWAs pick up the new UI on next launch). No voice endpoints, no behaviour change.

## What was tested HERE (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `node --check backend/static/app.js` | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — 18 v0.3 tests + 1 new: PWA voice wiring (mic button + listen hint + auto-speak toggle in index.html; SpeechRecognition + speechSynthesis in app.js; SW cache v5; voice packages + RECORD_AUDIO in the Flutter app; `/health` reports 0.4.0) | ✅ **19 passed, 0 failed, 0 skipped** |
| `flutter pub get` (Flutter 3.38.1, Dart 3.10.0) | ✅ resolved (speech_to_text 7.4.0, flutter_tts 4.2.5) |
| `flutter analyze` | ✅ PASS — **"No issues found!"** (fixed along the way: missing paren in the bubble Row, `hasPermission` is a Future, deprecated listen params → `SpeechListenOptions`) |
| `flutter build apk` | ❌ NOT BUILT HERE — same sandbox Gradle block as v0.3 (see below). Source verified clean; APK must be built on his laptop per `mobile_app/README.md`. |
| Live server boot (`python run.py`) + `GET /health` (version 0.4.0, auto mode), `/`, `/style.css`, `/app.js`, `/sw.js`, `/manifest.json`, `/health/detailed` | ✅ PASS — all HTTP 200 |
| Headless-browser voice check (Playwright, mobile 390×844) | ✅ PASS — mic button + speaker button visible; mic tap enters listening state (pulsing red mic + "Sun raha hoon…" hint), second tap stops it; with SpeechRecognition deleted, mic tap shows the clean Hinglish hint toast; Settings auto-speak toggle present and OFF by default; zero page errors |
| Visual check (screenshots read + inspected) | ✅ PASS — `design/v0.4-screenshot.png` (chat view: mic next to send, 🔊 on welcome bubble), `design/v0.4-check-listening.png` (listening state), `design/v0.4-check-settings.png` (Settings modal) — Light Colourful design intact, no overlap |

## What was NOT tested here (needs his laptop / phone)

Real speech recognition + TTS on a real device (headless Chromium exposes the APIs but has no voices and no speech service — the listening UI and hint paths were verified, actual transcription/speech quality was not); Flutter app running on a real phone (mic permission flow, on-device recognizer, TTS voice); APK build + install (blocked here by the sandbox Gradle policy — build it on the laptop). Same v0.3 caveats still apply (no real LLM calls in this VM, Oracle deploy untested live).

## What he needs to do himself (checklist)

1. **Laptop:** extract the new zip, copy old `data/` and `workspace/` in, run `setup.bat` once, then `run.bat` — same as before. Phones with the old PWA get the voice UI automatically via the service-worker cache bump.
2. **Phone app:** rebuild the APK on the laptop from `mobile_app/` (`flutter pub get` → `flutter build apk --debug`) and reinstall — the new APK is needed for the mic permission + voice packages. First mic tap asks for mic permission — allow it.
3. **PWA voice needs Chrome** (Android or desktop) for mic input; Firefox/Safari show the hint and everything else still works.

## Known limits (also in README)

Same as v0.3. Voice input accuracy depends on the device's recognizer (Google speech services on Android / Chrome); Hinglish works best with the en-IN recognizer. Auto-speak reads the reply text with code blocks skipped — long technical replies may sound choppy.

---

# Delivery Notes — Linda v0.3

Built 22 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.3.zip`. APK: **NOT built in this VM — Flutter source only** (see "APK outcome" below).

## What's new in v0.3 (Android app + Oracle cloud — everything from v0.2.1 still works)

1. **Real Flutter Android app** (`mobile_app/`) — Chat (live steps + approval card + demo chips + Stop), Tasks (list + detail), Settings (server URL + API token in secure storage, brain, Gemini key, approval, browser, max steps), Status (health checks + Hinglish fix hints). Same Light Colourful design as the PWA. Talks to the same FastAPI backend over the same endpoints, so laptop + phone share one agent and one task history.
2. **Oracle Always Free cloud deployment** (`deploy/`) — Dockerfile + docker-compose.yml (backend + Caddy reverse proxy with automatic free HTTPS), systemd unit (restart on boot, 24×7), `deploy.sh` (installs Docker, generates a random API_TOKEN, starts everything, installs a `/health` keep-alive cron against Oracle's idle-reclamation rule), and a full Hinglish+English step-by-step `ORACLE_GUIDE.md` (Mumbai region, A1 Flex 2 OCPU/12 GB, ports 80/443, honest out-of-capacity + reclamation caveats).
3. **Optional API_TOKEN auth** — when `API_TOKEN` is set (cloud), `/chat`, `/tasks`, `/settings`, `/memory`, `/health/detailed`, `/config` require `Authorization: Bearer <token>`; `/health` and the static UI stay public. When unset (laptop), behavior is unchanged. The Flutter app sends the token from secure storage; the PWA prompts once and remembers it in localStorage.
4. **Reply language auto-adapts** — the agent now replies in the same language/script the user chats in (English / Hindi / Hinglish), defaulting to English. No language setting anywhere (the user explicitly rejected one) — it's a system-prompt line in `agent.py`.

## What was tested HERE (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — 16 v0.2 tests + 2 new: API token auth (open when unset, 401 without/wrong token when set, `/health` + static files always public) and system-prompt auto-language (prompt line present, no `language` in settable keys) | ✅ 18 passed, 0 failed, 0 skipped |
| `docker compose config` validation (standalone compose binary v2.29.2, no daemon) | ✅ PASS — `COMPOSE_CONFIG_VALID` |
| `flutter analyze` (Flutter 3.38.1, Dart 3.10.0) | ✅ PASS — "No issues found!" (first run had 1 warning + 3 deprecation infos, all fixed: unused `stepLine` ctor param; `DropdownButtonFormField value:` → `initialValue:`) |
| `flutter build apk` | ❌ NOT BUILT HERE — sandbox network policy blocks Gradle's client↔daemon TCP handshake (see APK outcome below). `flutter analyze` is clean, so the source is verified; the APK must be built on his laptop (guide in `mobile_app/README.md`). |
| Live server boot (`python run.py`) + `GET /health` (version 0.3.0, auto mode), `/`, `/sw.js`, `/health/detailed` | ✅ PASS — all HTTP 200 |

## APK outcome — source-only, and why (read this before assuming the app is broken)

**No APK was built in this VM.** The Flutter source is complete and `flutter analyze` reports "No issues found!", but the APK build itself cannot run in this build VM because of a sandbox network policy — not because of anything wrong with the app code:

- The toolchain is fully installed here: Flutter 3.38.1, Dart 3.10.0, Temurin JDK 17, Android SDK (platform-tools r37.0.3, platform android-34, build-tools 34.0.0 — installed by direct download because `sdkmanager` itself crashes on this VM's proxy: Java's `HttpURLConnection` throws `NoSuchElementException` in `doTunneling0`).
- The blocker: Gradle builds need the Gradle client to talk to the Gradle daemon over a localhost TCP connection. In this VM, **Java processes cannot make localhost TCP connections at all** — verified decisively with socket tests: a Java client connecting to a Java/Python server on 127.0.0.1 gets the sandbox message *"Other TCP connections is turned off for this assistant... switch other_tcp from Deny to Ask"*, while a Python client on the same port connects fine. So every Gradle invocation fails with "Could not receive a message from the daemon" after the daemon starts and waits (its log shows it never receives a connection).
- Workarounds tried and exhausted: normal daemon mode, `--no-daemon` (Gradle 8.10.2 still forks a single-use daemon → same TCP failure, even with JVM args matched exactly), `--foreground` (starts the daemon but never dispatches the build, then self-stops on idle timeout), matching `GRADLE_OPTS`/`org.gradle.jvmargs` (still forks), pre-seeding the Gradle distribution (worked — `gradlew --version` runs), proxy settings for dependency downloads (worked for `flutter pub get` — 54 dependencies resolved).
- The only remaining "fix" would be changing the user's Muse network setting (`other_tcp` Deny → Ask) — not appropriate to ask for just to build an APK here, when the same build takes ~10 minutes on his own Windows laptop where no such policy exists.
- **What he does instead:** follow `mobile_app/README.md` — install Flutter + Android Studio, `flutter pub get`, `flutter build apk --debug`, install the APK. The source is verified clean, so the laptop build should succeed as long as the SDKs install.

## What was NOT tested here (needs his laptop / phone)

Same as v0.2.1, plus: APK build + install on a real phone (blocked here by the sandbox policy above — build it on the laptop per `mobile_app/README.md`); Flutter app against a live server on the same Wi-Fi; Oracle VM creation + deploy.sh run on a real VM (no Oracle account was created — only he can, it needs his card); Caddy HTTPS with a real domain; Docker image build (no Docker daemon in this VM — only `docker compose config` was validated).

## What he needs to do himself (checklist)

1. **Laptop:** extract the new zip, copy old `data/` and `workspace/` in, run `setup.bat` once, then `run.bat` — same as before.
2. **Phone app:** build the APK on the laptop from `mobile_app/` (guide in `mobile_app/README.md` — Flutter install → `flutter pub get` → `flutter build apk --debug`), install it on the phone, then in Settings set the server URL (laptop LAN IP on same Wi-Fi, or cloud URL) and the API token if the server is the cloud one. No prebuilt APK in this delivery (see APK outcome above).
3. **Cloud (24×7):** create the Oracle Always Free account himself (card verification, no charge), create the Mumbai A1 Flex VM, open ports 80/443, then follow `deploy/ORACLE_GUIDE.md` — scp the project, run `deploy.sh`, fill DOMAIN + GEMINI_API_KEY in `deploy/.env`, run `deploy.sh` again. Only he can do the account + VM steps.

## Known limits (also in README)

Same as v0.2.1. Default `APPROVAL_MODE=auto` (user's explicit choice). Oracle free tier: 2 OCPU/12 GB since June 2026; ARM capacity is often out of stock (retry at odd hours); idle VMs can be reclaimed (keep-alive cron included, not a guarantee).

---

# Delivery Notes — Linda v0.2.1

Built 22 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.2.1.zip`.

## What's new in v0.2.1 (design release — no feature changes, everything from v0.2 works as before)

1. **Light Colourful design** — the design Linda himself picked from mockups (22 Nov 2026). Soft pastel gradient background (light sky blue → lavender → peach) with airy pastel blobs, glossy translucent white glass chat bubbles (user bubble: soft blue→lavender gradient; agent bubble: translucent white), dark navy text for readability, gradient accent (sky → lavender → peach) on the logo, send button and focus rings, soft shadows, rounded corners. Light theme throughout — no dark backgrounds anywhere in the app UI. Reference mockup: `design/media-generation-linda-design-light-colorful-*.webp`.
2. **New PWA icons** — regenerated with PIL to match: soft pastel gradient rounded square with a white "S" (180/192/512px). `manifest.json` theme/background colors updated to light values (`#dbeafe` / `#eef4ff`); `index.html` theme-color and status-bar style updated to match.
3. **Service worker cache bumped to v3** — phones that installed v0.2.0 pick up the new UI on next launch.
4. **Bug fixed (found by the visual check)** — on narrow phones the app bar was too crowded: the green "online" pill overlapped the "Linda" title and brain/mode line. Fixed: brand text can now shrink + ellipsize, and the pill hides below 560px width (the Status button already shows a warning when something is broken). Verified by screenshot at 390px width.

## What was tested HERE (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `pip install -r requirements.txt` in a clean venv | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — all 16 v0.2 tests | ✅ 16 passed, 0 failed, 0 skipped |
| Live server boot (`python run.py`) + `GET /health` (version 0.2.1, auto mode), `/config`, `/health/detailed`, `/`, `/manifest.json`, `/sw.js`, `/app.js`, `/style.css`, all 3 icons | ✅ PASS — all HTTP 200 |
| Live chat round-trip with Ollama down (via real browser) | ✅ PASS — user bubble + clean Hinglish error bubble render correctly, no hang, composer frees up |
| **Visual check** (headless Chromium screenshots, read + inspected) — mobile 390×844 chat view, Status modal, Settings modal, desktop 1280×800 | ✅ PASS — light pastel gradient, glass bubbles, gradient logo/send button, readable dark text; app-bar overlap found and fixed, re-verified clean. Final screenshot: `design/v0.2.1-screenshot.png` |

Note: this task was started once before and cancelled mid-way (21:13 IST); the cancelled attempt had already re-themed `style.css`/`index.html`/`manifest.json`/`sw.js` and bumped the version in `config.py`. This run verified that work, fixed the app-bar bug it contained, regenerated the icons, and finished testing + packaging. Nothing was redone blindly.

## What was NOT tested here (needs his laptop)

Same as v0.2: real LLM calls (no Ollama/Gemini key in this VM); headed (visible) browser; real git push / Kaggle submit / live sites; PWA install on an actual phone (new icons + manifest served correctly, HTTP 200 verified — actual home-screen install not tested); Cloudflare Tunnel / Oracle VM; `setup.bat` on real Windows.

## What he needs on his laptop (checklist)

Upgrading from v0.2.0: extract the new zip, copy old `data/` and `workspace/` folders in (memory + files carry over), run `setup.bat` once, then `run.bat`. Settings stay as they were (`.env` is preserved if copied over — or just re-set them in the app). Phones with the old PWA installed get the new design automatically via the service worker cache bump.

## Known limits (also in README)

Same as v0.2. Default `APPROVAL_MODE=auto` (user's explicit choice).

---

# Delivery Notes — Linda v0.2

Built 22 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.2.zip`.

## What's new in v0.2 (polish pass — everything from v0.1 still works)

1. **Settings screen (⚙️ in the header)** — change brain (Ollama/Gemini), Ollama model, Gemini key + model, approval mode, browser visible/headless, max steps — all without touching any file. Saved to `.env` via `GET/POST /settings`, applied live, no restart. The Gemini key is never sent back to the UI in full (masked: `AIza••••••••3f9a`). Bad input gets a Hinglish 400.
2. **Status / health panel (Status button)** — checks Ollama reachable, Ollama model pulled, Gemini key valid (only when Gemini is the brain; validated with a tiny models-list call, no generation quota), git installed + configured, Playwright Chromium installed, workspace writable. Each failed check has a Hinglish fix hint. Auto-opens on first load if anything is broken. Backend: `GET /health/detailed`.
3. **Robustness** — brain calls retry once after 1.5s on transient errors (connect/timeout/5xx/429) and never on permanent ones (no key, unknown model, bad request). Every user-visible error is a clean Hinglish message; full tracebacks go to the server log only. Agent loop can never hang: timeouts + max steps + a last-resort safety net.
4. **Stop button (■)** — stops a running task at the next checkpoint (also wakes it from an approval wait). New `POST /tasks/{id}/stop`, task status `stopped`.
5. **Smoother setup** — `setup.bat`/`setup.sh` check Python 3.12+, git, venv, pip install, Playwright Chromium (failure is a warning, not a stop — the Status panel reports it), `.env` creation; every step prints a Hinglish status line. `run.bat`/`run.sh`/`run.py` print the URL clearly and warn (not crash) if Ollama is not running.
6. **UX polish** — header shows current brain + approval mode; Settings/Status buttons in the header; toast notifications; service worker cache bumped to v2 so the updated UI is actually served (v2 also excludes `/settings` and `/health/detailed` from caching).
7. **Bug fixed from v0.1** — after the first task finished, the chat composer stayed blocked (the finished task id was never cleared), so no second message could be sent. Fixed: the composer frees up on done/error/stopped.
8. **Config refactor** — settings now live on the Settings instance (not class attributes), so live reload and direct assignment can never disagree. Found by the full-suite test run: a class/instance shadowing bug made POST /settings silently not apply after brain tests had assigned attributes directly.

## What was tested HERE (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `pip install -r requirements.txt` in a clean venv | ✅ PASS |
| Smoke tests (`python tests/smoke_test.py`) — all 10 v0.1 tests + 6 new: task stop, brain retry (transient 500), brain no-retry (permanent 404), health endpoint, settings masking, settings write + validation | ✅ 16 passed, 0 failed, 0 skipped |
| Live server boot (`python run.py`) + `GET /health`, `/health/detailed`, `/settings` GET/POST, `/`, `/manifest.json`, `/sw.js`, `/app.js`, `/style.css`, icons | ✅ PASS — settings POST persisted to .env and applied live (verified via GET + /health); bad settings POST returns Hinglish 400; stop on unknown task returns Hinglish 404 |
| Live chat round-trip with Ollama down | ✅ PASS — task finishes `error` with a clean Hinglish message, no hang |
| Startup Ollama warning in `run.py` | ✅ PASS — server starts with a clear warning, does not crash |

Bugs found and fixed during v0.2 testing:
1. Settings `refresh()` updated class attributes while tests (and any direct assignment) set instance attributes — the instance shadowed the class, so POST /settings silently did nothing after brain tests ran. Fixed by moving all live values to instance attributes.
2. Test asserted `MODEL_PROVIDER=gemini` in the .env text, but python-dotenv's `set_key` quotes values (`MODEL_PROVIDER='gemini'`). Test now parses with `dotenv_values`.
3. `health.py` had an `elif` after `except` (SyntaxError) — restructured the Gemini check.
4. Validation-error handler matched pydantic's error type wrong (`"Value error"` vs `"value_error"`), so custom Hinglish validator messages were replaced by a generic one. Fixed.

## What was NOT tested here (needs his laptop)

Same as v0.1, plus:
- **Real LLM calls** — no Ollama and no Gemini key in this VM. The planner loop was tested with a stub brain; Gemini key validation in the health panel was NOT tested against Google (no key here) — the code path uses a models-list call that returns 200/400/401/403.
- **Headed (visible) browser** — tested headless only (no display in the VM).
- **Real git push / Kaggle submit / live websites** — deliberately not tested.
- **PWA install on Android** — manifest + service worker + icons served correctly (HTTP 200 verified), actual "Add to Home screen" not tested on a phone. Note: the service worker cache version was bumped to v2, so phones that installed v0.1 will pick up the new UI on next launch.
- **Cloudflare Tunnel / Oracle VM** — documented from verified public info, not set up here.
- **setup.bat on real Windows** — batch syntax written carefully but not executed (no Windows here). `setup.sh` logic mirrors it; the Python-side steps are the same ones tested in the venv install.

## What he needs on his laptop (checklist)

Same as v0.1. Upgrading from v0.1: extract the new zip, copy old `data/` and `workspace/` folders in (memory + files carry over), run `setup.bat` once, then `run.bat`. Settings can now all be changed in the app — no `.env` editing needed. (HOST=0.0.0.0 for phone-on-WiFi is still a `.env` line — it is server-level, set before the server starts.)

## Known limits (also in README)

Same as v0.1. Default `APPROVAL_MODE=auto` (user's explicit choice): the agent runs every action immediately. Change it in Settings if wanted.

---

# Delivery Notes — Linda v0.1

Built 21 Nov 2026. Source: `~/workspace/satyam-ai/`. Zip: `linda-ai-v0.1.zip`.

## What was tested HERE (in the build VM, Python 3.12.3)

| Test | Result |
|---|---|
| `python -m compileall` on all Python files | ✅ PASS |
| `pip install -r requirements.txt` in a clean venv | ✅ PASS (found + fixed: `kaggle` 2.2.5 needs `six`, now in requirements) |
| Smoke tests (`python tests/smoke_test.py`) — memory, approvals auto + ask (approve/reject), files tool + sandbox escape, github init/commit on a local temp repo, agent loop with stub brain, brain error on unreachable Ollama, kaggle no-credentials error | ✅ 9 passed, 0 failed |
| Browser tool headless (open/read/screenshot/close on a local page) | ✅ PASS |
| Demo 3 path (browser read → Excel write → read back) | ✅ PASS |
| Live server boot (`python run.py`) + `GET /health`, `/config`, `/`, `/manifest.json`, `/sw.js`, icons, `POST /chat`, `GET /tasks/{id}`, `/memory` | ✅ PASS — chat with Ollama down fails gracefully with a clear Hinglish error, no hang/crash |

Bugs found and fixed during testing:
1. `kaggle` 2.2.5 imports `six` without declaring it → added `six` to requirements.
2. `kaggle` 2.x `authenticate()` calls `exit(1)` with no credentials → credentials are now pre-checked and `SystemExit` is converted to a clear error, so a Kaggle tool call can never kill the agent thread.
3. `httpx` picked up the VM's system proxy config for localhost Ollama calls and choked on it → Ollama client now uses `trust_env=False` (localhost never needs a proxy); both providers convert any transport error into a clean `BrainError`; the agent loop also catches unexpected brain errors so a task can never get stuck "running".

## What was NOT tested here (needs his laptop)

- **Real LLM calls** — no Ollama and no Gemini key in this VM. The planner loop was tested with a stub brain returning canned JSON. First run on the laptop will tell whether Qwen 2.5 3B follows the JSON format reliably; Gemini free tier is the more reliable demo brain.
- **Headed (visible) browser** — tested headless only (no display in the VM). Headed mode is the same code path with `headless=False`; on Windows it opens a normal Chromium window.
- **Real git push / Kaggle submit / live websites** — deliberately not tested (no real repos touched, no live portal access). Demo 3 against live Wikipedia could not run here: the VM's Chromium has no direct internet (proxy-only egress). On the laptop with direct internet it should work.
- **PWA install on Android** — manifest + service worker + icons ship and are served correctly (HTTP 200 verified), but actual "Add to Home screen" install was not tested on a phone.
- **Cloudflare Tunnel / Oracle VM** — documented from verified public info, not set up here.

## What he needs on his laptop (checklist)

1. Python 3.12 (PATH ticked), Git, Ollama + `ollama pull qwen2.5:3b`
2. `setup.bat` (one-time), then `run.bat` → http://127.0.0.1:8000
3. For the GitHub demo: `git config --global user.name/email` + one manual `git push` login first + an empty GitHub repo
4. For Kaggle tools: `kaggle auth login` (or kaggle.json in `~/.kaggle/`)
5. For the smarter demo brain (recommended): free Gemini key from aistudio.google.com → `.env`

## Known limits (also in README)

- Local Qwen 2.5 3B is small — long plans can go wrong; Gemini free tier is more reliable for demos.
- CAPTCHA/OTP cannot be solved by the agent (human-in-the-loop in the visible browser).
- No auth on the server — personal tool; use `HOST=0.0.0.0` only on a trusted Wi-Fi.
- Some sites block bot browsers (e.g. Amazon).
- Default `APPROVAL_MODE=auto` (user's explicit choice): the agent runs every action immediately. Set `ask` in `.env` for one-click approvals on push/submit.
