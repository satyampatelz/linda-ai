# Gmail Setup — Let Linda read your Gmail (v0.8)

Linda **only reads** your Gmail — it never sends, deletes, or changes mail.
That lets it do this:

- **Read emails** — "what's new in my Gmail?", "show me the Internshala mail"
- **Email OTP auto-fill** — if a site asks for an OTP at login, Linda reads the code from Gmail and fills it in itself (in the browser)
- **Check sites** — open sites like Internshala and check applications/messages (Gmail + browser together)

Setup is a **one-time** thing (~10 minutes), then never again.

---

## Part A — Create a Google Cloud project (free, no card needed)

1. Open [console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account.
2. At the top, press **Select a project → New Project**. Name it anything, e.g. `Linda` → **Create**.
3. Once the project opens, left menu → **APIs & Services → Library**.
4. In search, type **Gmail API** → click it → press **Enable**.

## Part B — OAuth consent screen + client_secret.json

5. Left menu → **APIs & Services → OAuth consent screen**.
6. Choose **User Type: External** → **Create**.
7. App name: `Linda` (anything works), support email: your Gmail, developer email: your Gmail → **Save and Continue**.
8. **Scopes** page: **Add or Remove Scopes** → search for `gmail.readonly` → tick `https://www.googleapis.com/auth/gmail.readonly` → **Update** → **Save and Continue**.
   - Only the **readonly** scope is needed — Linda doesn't send/delete mail, so don't give it more permission than that.
9. **Test users** page: **Add Users** → enter **your Gmail address** → **Save and Continue** → then **Back to Dashboard**.
   - Test mode is enough for personal use (you are the only user). Google's app review is not needed as long as you only use your own account.
10. Left menu → **APIs & Services → Credentials** → at the top, **+ Create Credentials → OAuth client ID**.
11. Application type: **Desktop app** → **Create**.
12. Press **Download JSON**. The file name will be something like `client_secret_1234....json` — rename it to **`client_secret.json`** and put it in the **linda-ai project folder** (where `run.py` is).
    - This file is secret — never send it to anyone, never put it on GitHub. (It's in `.gitignore` — it will never go into git.)

## Part C — One-time sign-in (create the token)

13. Open a terminal, go to the project folder, activate the venv (Windows: the venv from after `setup.bat` — `.\.venv\Scripts\activate`), then run:

```
python -m backend.app.gmail.auth
```

14. Google's consent screen will open in the browser. Choose your Gmail account.
    - If Google shows **"This app isn't verified"**: press **Advanced** → **Go to Linda (unsafe)** — this warning appears because you made the app yourself (test mode), it's no problem.
    - Press **Allow** (Gmail read-only permission).
15. The browser tab will show "The authentication flow has completed". In the terminal you'll see "Done! Token saved: data/token.json".
16. That's it! Now say in chat with Linda: **"what's new in my Gmail?"**

The token is saved in `data/token.json` (git-ignored, never goes into the repo/zip). When it expires it refreshes by itself — no need to sign in again. To ever stop access, go to [Google account permissions](https://myaccount.google.com/permissions) and revoke Linda, and delete `data/token.json`.

---

## Part D — Google sign-in (in the browser, once)

For "Sign in with Google" / "Login with Google" on sites:

1. Run Linda, then say in chat: **"open Google"** (or open the browser yourself — open `google.com` in the visible browser).
2. **Sign in to Google with your account** (once, yourself — you enter the password, not Linda).
3. Done. The browser profile stays saved (`data/browser-profile/`) — now on sites like Internshala, pressing "Login with Google" takes you straight in, it won't ask for the password again.

**On the cloud (Oracle VM):** a VM has no screen, so the first Google login won't work directly there. Easy way: sign in on the laptop, then copy the `data/browser-profile/` folder to the VM (with scp, into `~/linda-ai/data/`). After that, the VM's browser will stay logged in too.

---

## What to say (in chat)

| Say | Linda will |
|---|---|
| "what's new in my Gmail?" | Read your new emails and tell you about them |
| "show me the Internshala mail" | Show you the Internshala emails |
| "check Internshala" | Open Internshala and check applications/messages |
| "fill in this form" (+ details) | Open the form, fill it in, submit it |
| An OTP comes on a site | Read the code from Gmail and fill it in itself (email OTP) |
| An SMS OTP comes | Asks you for the code in chat (in your language) — send the code, it fills it in itself |

> Note: Hinglish/Hindi commands work too — Linda understands both.

## The honest limits

- **Linda can't read SMS OTPs** (it has no SMS access) — but you don't have to fill it in the browser yourself either: it will ask you for the code in chat (in your language), you send the code, it fills it in itself and continues the task. The code is used once and forgotten — it's never saved anywhere (not in memory/DB/log).
- **CAPTCHA** — Linda doesn't solve CAPTCHAs — you do it in the visible browser, then tell the agent "continue".
- **Some sites block automation** (like Amazon) — the browser can get stuck on those. It works on normal sites like Internshala.
- **OTPs expire** — Linda only takes codes from emails from the last 10 minutes. It never fills an old code.
- **One Gmail account only** — only the mail of the account you signed in with is read. If the OTP email comes to a different account, Linda won't see it.
- **You have to give the form values** — Linda doesn't fill forms by guessing. For any info it doesn't have, it leaves the field blank and tells you.
