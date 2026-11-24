# Linda Desktop Icon — open chat in one click 🖥️

Linda now runs from an icon on your laptop's Desktop — just like any other app. Click the icon and the chat opens — **with your previous chat** (the chat is saved on your laptop, so if you close it and open it again, you get the same chat back).

> Linda now lives on your Windows desktop like any app. One click on the icon opens your chat — with your previous chat history intact.

## One-time setup

1. First do the normal setup (if you haven't yet): run `setup.bat` — the steps are in the README.
2. In the `desktop` folder, **double-click `create-shortcut.bat`**.
3. Done — a **Linda** icon (the 3D teal-glass L + gold rings logo) will appear on your Desktop.

That's it. From now on, **double-click the icon** every day — if the server is stopped, it starts by itself (the first time takes 10–20 seconds), then the chat opens in its own app window. You won't see browser tabs or an address bar — it feels just like an app.

## How it works

- **Icon → `desktop\Linda.bat`** — this is the launcher. It first checks whether the server is running (a `/health` check). If it is stopped, it starts it in its own minimized window, then opens Chrome (or Edge, if Chrome is not there) in `--app` mode.
- **The server window** (named "Linda Server", minimized) keeps running in the background — this is normal. Closing the chat window does not stop the work: the server keeps running, and the task keeps finishing. To stop the server, close that window (or press `Ctrl+C`).
- **Chat history** — every message + the agent's reply is saved on the laptop in `data/satyam.db` (only the latest 200 messages). No OTP code is ever saved — a code sent in chat is forgotten once it has been filled in.

## Running from a cloud server (work keeps going even with the laptop off)

If the server is on the laptop, Linda stops as soon as you turn the laptop off. **To keep work going even with the laptop off**, run the server on Oracle Cloud's free VM (setup: `deploy/ORACLE_GUIDE.md`), then:

1. Open `desktop\server.txt` (in Notepad).
2. Change the last line to your VM's URL, e.g. `https://linda.example.com` — just one line, don't touch the lines starting with `#`.
3. Save. Click the icon — the launcher won't start anything locally, it will open the cloud server directly.

Now, laptop off or phone off — work keeps going in the cloud; check the result later from your phone or laptop.

> Tip: the cloud URL must be `https://` (the deploy guide sets up HTTPS with Caddy). An `http://` IP URL will also work, but the browser sometimes blocks the mic (voice input) on insecure sites.

## Auto-start (optional — server starts by itself when the laptop turns on)

From the `desktop` folder in a terminal, run:

```
create-shortcut.bat -AutoStart
```

This puts a shortcut in the Windows Startup folder as well as on the Desktop. Now the Linda server will start by itself in the background as soon as the laptop turns on — click the icon and the chat opens at once, no waiting.

To turn it off: `Win + R` → `shell:startup` → delete `Linda.lnk`.

## Troubleshooting

- **Clicking the icon opens a blank page** — the server is still starting. Wait 10–20 seconds, then refresh the window (F5). If it is still blank, look for the error in the "Linda Server" window.
- **"Linda isn't set up yet" appears** — run `setup.bat` first (a one-time step), then click the icon again.
- **No Chrome** — the launcher will use Edge (already on Windows 11). If neither is there, it will open in your default browser (with tabs).
- **The L logo is not showing on the icon** — Windows sometimes doesn't refresh its icon cache. Right-click the Desktop → Refresh, or log out and log in once.
- **`create-shortcut.bat` closes as soon as it runs** — PowerShell probably hit an error. From the `desktop` folder in a terminal, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\create-shortcut.ps1` — the error will show up.
- **Chat history looks empty** — you only see the history of the server you are connected to. The laptop server and the cloud server have separate histories (each server keeps its own `data/satyam.db`). Copying the old `data/` folder into the new zip brings the history along too.

## Files (in this folder)

| File | What it does |
|---|---|
| `Linda.bat` | Launcher — checks/starts the server + opens the app window |
| `server.txt` | Server URL (laptop by default, or the cloud VM's URL) |
| `create-shortcut.ps1` | Creates the desktop shortcut (with the L logo icon) |
| `create-shortcut.bat` | Double-click wrapper for the script above |
| `linda.ico` | Desktop icon (3D teal-glass L + gold rings logo, 16–256px sizes) |
