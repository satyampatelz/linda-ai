# Linda — Demo Guide (for showing friends)

Three demos, from easiest to most impressive. For every demo, run `run.bat` and open `http://127.0.0.1:8000`. Demo details are also in the `demos/` folder.

**Before the demo (once):** Ollama must be running (`ollama pull qwen2.5:3b` already done). If the local model feels slow, turn on the Gemini free tier in Settings (⚙️) — the demo will run smoothly. Check everything first with the Status button.

---

## Demo 1 — Chat + Planning (2 min) 🗣️
**Show:** Linda doesn't just answer, it plans a task and executes it.

Paste this:
> Tell me about yourself — what all can you do?

Then:
> Make a plan for a Python project for me: a to-do list app, FastAPI + HTML.
> After the plan, create the project files too.

**What you'll see:** In the live steps panel, Linda's steps — thinking, creating files. Then open the `workspace/` folder — the files will be there.

## Demo 2 — GitHub: write code, commit, push (5 min) 🐙
**Show:** Linda works like a developer on its own. (Detail: `demos/demo2_github.md`)

**Prepare in advance:** Create an empty repo on GitHub (`hello-linda`), copy the URL. Git user.name/email must be set.

Paste this (put in your own URL):
> In the workspace, create a Python project called 'hello-linda' — a calculator CLI
> with tests — then commit it in git and push it to this repo:
> https://github.com/satyampatelz/hello-linda.git

**What you'll see:** Live steps — files → git init → commit → push. Then **open the repo on github.com and refresh — the code is live.** This is the moment that will impress your friends the most.

## Demo 3 — Browser + Excel report (3 min) 🌐
**Show:** Linda drives the browser itself and makes a report.

Paste this:
> Research 'Machine Learning' on Wikipedia and make an Excel report of 5 key points
> in the workspace.

**What you'll see:** A Chromium window opens on its own and goes to Wikipedia (visible browser — everything is visible), then `Machine_Learning_report.xlsx` is created in `workspace/`. Open the Excel file and show it.

**Backup (no LLM, 100% deterministic):** if the chat demo ever gets stuck, run this in the terminal:
```
python demos/demo3_browser_excel.py "Machine Learning"
```
This does the same work directly — browser + Excel, no AI planning.

---

## Demo tips
- **Run it yourself once first** — don't try it for the first time in front of your friends.
- The **Gemini free tier** is more reliable for demos (the local 3B can sometimes be slow/wrong).
- Keep the **browser visible** (`BROWSER_HEADLESS=false`) — your friends should see that the browser is running on its own.
- **You can also show it from your phone** — see "Phone" in the README. Chat from the phone, and the browser will be seen running on its own on the laptop. Your friends will be very impressed by this.
- If something fails, don't panic — the error shows in the live steps, read it and say it again ("try that step again").
