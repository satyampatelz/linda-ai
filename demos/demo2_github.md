# Demo 2 — GitHub: Write code, commit, push (5 minutes)

This is the most impressive demo: Linda writes code itself and pushes it to GitHub.

## Prepare in advance (once)
1. Git must be installed, and this set (once, in the terminal):
   ```
   git config --global user.name "Satyam Patel"
   git config --global user.email "sp3856201@gmail.com"
   ```
2. Create an **empty repo** on GitHub (github.com → New repository → name `hello-linda` → public → NO README, NO .gitignore, NO license). Copy the URL, e.g. `https://github.com/satyampatelz/hello-linda.git`.
3. Log in to GitHub in the terminal once (`git` will ask you to log in the first time you push — you'll sign in via the browser). This way the push won't get stuck during the demo.

## Demo
1. Run `run.bat`, open `http://127.0.0.1:8000`.
2. Paste this in chat (put in your own repo URL):

> In the workspace, create a Python project called 'hello-linda' — a calculator CLI
> with tests — then commit it in git and push it to this repo:
> https://github.com/satyampatelz/hello-linda.git

## What your friends will see
- In the live steps: files written → git init → commit → remote add → **push**.
- Then open the repo on github.com — the code is live there. Refresh it and show it in front of your friends.
- Linda did all of this itself — you only wrote one line.

## Notes
- Pushing needs internet + GitHub login. If you're not logged in, run `git push` manually once in the terminal to log in, then run the demo again.
- If the repo URL is wrong, the agent will show an error — check the URL and say it again.
