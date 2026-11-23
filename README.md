# Satyam — Your Personal AI Agent

**Satyam** is your own autonomous AI agent — like Muse, but fully yours, at **₹0**. Tell it what to do in chat, and it does the work: writes code, pushes to GitHub, researches the web and makes Excel reports, does Kaggle work, manages files.

Built for **Homingo Hack Days — Agents track**.

## What it can do

- **Chat + plan** — describe a task, Satyam plans the steps, runs them, and shows a full step log
- **Code + GitHub** — writes code, commits, and pushes (with your git credentials; no passwords stored)
- **Browser** — works in a visible Chromium window, so you can watch it click, type, and read
- **Kaggle** — lists competitions and datasets, downloads data, submits
- **Files + code** — reads/writes files, runs Python scripts, fixes errors and retries
- **Voice** — talk to it and hear replies (mic + speaker, free, on-device)
- **WhatsApp / Instagram auto-reply** — answers DMs on its own, in your style, via official Meta APIs. Control it from chat: *"start replying to my WhatsApp messages"*
- **Gmail + OTP** — reads Gmail (read-only), fills email OTPs automatically, fills forms
- **Desktop icon + chat history** — one click opens your chat; history survives restarts
- **Android app** — real Flutter app, same agent on laptop and phone

## Quick start (Windows 11)

1. Install **Python 3.12** ([python.org](https://www.python.org/downloads/) — tick **"Add Python to PATH"**), **Ollama** ([ollama.com](https://ollama.com)), and **Git** ([git-scm.com](https://git-scm.com/downloads)).
2. Pull the local brain (one-time, ~1.9 GB):
   ```
   ollama pull qwen2.5:3b
   ```
3. Extract this repo, then run:
   ```
   setup.bat
   run.bat
   ```
4. Open **http://127.0.0.1:8000** and start chatting.

For a smarter free brain, add a Gemini API key in **Settings** (free from [aistudio.google.com](https://aistudio.google.com), no card needed). Linux/macOS/WSL: use `setup.sh` / `run.sh`.

## Phone

- **Same Wi-Fi:** set `HOST=0.0.0.0` in `.env`, open `http://<laptop-IP>:8000` on your phone, add to home screen.
- **24×7 cloud:** deploy to an Oracle Always Free VM — see [deploy/ORACLE_GUIDE.md](deploy/ORACLE_GUIDE.md).
- **Android app:** build the APK from `mobile_app/` — see [mobile_app/README.md](mobile_app/README.md).

## Docs

- [DEMO_GUIDE.md](DEMO_GUIDE.md) — 3 demos to show friends
- [MESSAGING_SETUP.md](MESSAGING_SETUP.md) — WhatsApp/Instagram auto-reply setup
- [GMAIL_SETUP.md](GMAIL_SETUP.md) — Gmail + OTP setup
- [desktop/DESKTOP_GUIDE.md](desktop/DESKTOP_GUIDE.md) — desktop icon + cloud URL

## Cost

₹0. Local Ollama model, Gemini free tier, Playwright, FastAPI, Kaggle API — all free. No paid service anywhere in this project.

## Version

**v0.9.1** (23 Nov 2026) — 3D app icon (teal-glass S, gold rings) everywhere.
