# Gmail Setup — Linda ko apna Gmail padhne do (v0.8)

Linda tumhara Gmail **sirf padhta** hai — mail kabhi bhejta, delete ya
badalta nahi. Isse wo ye kar pata hai:

- **Emails padhna** — "mere Gmail me kya aaya hai?", "Internshala ka mail dikhao"
- **Email OTP auto-fill** — koi site login pe OTP maange toh Linda Gmail se code padh ke khud bhar dega (browser me)
- **Sites check karna** — Internshala jaise sites khol ke applications/messages dekhna (Gmail + browser mil ke)

Setup **ek baar** karna hai (~10 minute), phir kabhi dobara nahi.

---

## Part A — Google Cloud project banao (free, card nahi lagta)

1. [console.cloud.google.com](https://console.cloud.google.com) kholo, apne Google account se sign in karo.
2. Upar **Select a project → New Project** dabao. Naam kuch bhi rakho, jaise `Linda` → **Create**.
3. Project khulne ke baad, left menu → **APIs & Services → Library**.
4. Search me **Gmail API** likho → uspe click karo → **Enable** dabao.

## Part B — OAuth consent screen + client_secret.json

5. Left menu → **APIs & Services → OAuth consent screen**.
6. **User Type: External** chuno → **Create**.
7. App name: `Linda` (kuch bhi chalega), support email: apna Gmail, developer email: apna Gmail → **Save and Continue**.
8. **Scopes** page: **Add or Remove Scopes** → search me `gmail.readonly` → `https://www.googleapis.com/auth/gmail.readonly` ko tick karo → **Update** → **Save and Continue**.
   - Sirf **readonly** scope chahiye — Linda mail bhej/delete nahi karta, isliye usse zyada permission mat do.
9. **Test users** page: **Add Users** → **apna Gmail address** daalo → **Save and Continue** → phir **Back to Dashboard**.
   - Test mode personal use ke liye kaafi hai (tum khud hi user ho). Google ki app-review zaroori nahi hai jab tak tum sirf apna account use kar rahe ho.
10. Left menu → **APIs & Services → Credentials** → upar **+ Create Credentials → OAuth client ID**.
11. Application type: **Desktop app** → **Create**.
12. **Download JSON** dabao. File ka naam kuch `client_secret_1234....json` jaisa hoga — iska naam badal ke **`client_secret.json`** rakho aur **linda-ai project folder me** rakh do (jahan `run.py` hai).
    - Ye file secret hai — kabhi kisi ko mat bhejo, kabhi GitHub pe mat daalo. (Ye `.gitignore` me hai — git me kabhi nahi jayegi.)

## Part C — Ek baar sign-in (token banao)

13. Terminal kholo, project folder me jao, venv active karo (Windows: `setup.bat` ke baad wala venv — `.\.venv\Scripts\activate`), phir ye chalao:

```
python -m backend.app.gmail.auth
```

14. Browser me Google ka consent screen khulega. Apna Gmail account chuno.
    - Agar Google **"This app isn't verified"** dikhaye: **Advanced** dabao → **Go to Linda (unsafe)** — ye warning isliye hai kyunki tumne khud ka app banaya hai (test mode), koi problem nahi.
    - **Allow** dabao (Gmail read-only permission).
15. Browser tab me "The authentication flow has completed" dikhega. Terminal me "Ho gaya! Token save ho gaya" aayega.
16. Bas! Ab Linda se chat me bolo: **"mere Gmail me kya aaya hai?"**

Token `data/token.json` me save hota hai (git-ignored, kabhi repo/zip me nahi jata). Expire hone pe apne aap refresh ho jata hai — dobara sign-in nahi karna. Kabhi access band karna ho toh [Google account permissions](https://myaccount.google.com/permissions) me ja ke Linda ko revoke kar do, aur `data/token.json` delete kar do.

---

## Part D — Google sign-in (browser me, ek baar)

Sites pe "Sign in with Google" / "Login with Google" ke liye:

1. Linda chalao, phir chat me bolo: **"Google kholo"** (ya browser khud kholo — visible browser me `google.com` kholo).
2. **Google pe apne account se sign in karo** (ek baar, khud se — password tum daaloge, Linda nahi).
3. Bas. Browser ka profile save rehta hai (`data/browser-profile/`) — ab Internshala jaise sites pe "Login with Google" dabate hi tum andar ho jaoge, dobara password nahi maangega.

**Cloud (Oracle VM) pe:** VM me koi screen nahi hoti, toh wahan pehli baar Google login seedha nahi hoga. Aasan tareeka: laptop pe sign-in karo, phir `data/browser-profile/` folder ko VM pe copy kar do (scp se, `~/linda-ai/data/` me). Uske baad VM wala browser bhi logged-in rahega.

---

## Kya bolna hai (chat me)

| Bolo | Linda karega |
|---|---|
| "mere Gmail me kya aaya hai?" | Naye emails padh ke batayega |
| "Internshala ka mail dikhao" | Internshala ke emails dikhayega |
| "Internshala check karo" | Internshala khol ke applications/messages dekhega |
| "ye form bhar do" (+ details) | Form khol ke bhar dega, submit karega |
| Site pe OTP aaye | Gmail se code padh ke khud bhar dega (email OTP) |
| SMS OTP aaye | Tumse chat me code maangega (\"SMS pe aaya OTP bhejo\") — code bhej do, wo khud bhar dega |

## Sach wali baatein (limits)

- **SMS OTP Linda padh nahi sakta** (uske paas SMS access nahi hai) — lekin tumhe browser me khud bharna bhi nahi hai: wo chat me code maangega (\"SMS pe aaya OTP bhejo\"), tum code bhej do, wo khud bhar dega aur task continue karega. Code ek baar use hoke bhool jata hai — kahin save nahi hota (memory/DB/log me nahi).
- **CAPTCHA** Linda solve nahi karta — tumhe visible browser me karna hota hai, phir agent ko "continue" bolo.
- **Kuch sites automation block karti hain** (jaise Amazon) — unpe browser atak sakta hai. Internshala jaise normal sites pe kaam karta hai.
- **OTP expire hota hai** — Linda sirf pichhle 10 minute ke emails se code leta hai. Purana code kabhi nahi bharta.
- **Ek hi Gmail account** — jis account se sign-in kiya, sirf uska mail padha jayega. OTP wala email kisi aur account pe aata hai toh Linda ko nahi dikhega.
- **Form ke values tumhe dene honge** — Linda andaza laga ke form nahi bharta. Jo info uske paas nahi hai, wo field khali chhod ke tumhe batayega.
