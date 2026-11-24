# Demo 1 — Chat + Planning (2 minutes)

Show your friends this first: Linda is not just a chatbot, it plans work.

## Setup
1. Run `run.bat` (or `bash run.sh`), open `http://127.0.0.1:8000` in the browser.
2. Ollama must be running (`ollama serve`) and the model downloaded (`ollama pull qwen2.5:3b`).
   If the local model feels slow, turn on the Gemini free tier in Settings (⚙️) — the demo will run faster.

## What to say
Paste this in chat:

> Tell me about yourself — what all can you do?

Then try this:

> Make a plan for a Python project for me: a to-do list app, FastAPI + HTML.
> After the plan, create the project files too.

## What your friends will see
- Linda thinks first (its steps show in the live steps panel).
- Then it creates the files itself — go to the `workspace/` folder and show it, the files will be there.
- Every step's result shows live in the UI, nothing is hidden.

## If something gets stuck
- "Couldn't connect to Ollama" → open the Ollama app or run `ollama serve`.
- Answer is slow → Qwen 3B takes 10–20 seconds to load the first time, then gets faster.
