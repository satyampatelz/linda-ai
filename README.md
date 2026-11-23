# Satyam — Your Personal AI Agent 🤖

**Satyam** tumhara khud ka autonomous AI agent hai — Muse jaisa, lekin poora tumhara, aur **₹0 me**. Tum chat me kaam bolo, wo khud karke dikhata hai: code likhna, GitHub pe push karna, website se research karke Excel banana, Kaggle ka kaam, files manage karna.

Built for **Homingo Hack Days — Agents track** (build phase 21 Nov – 6 Dec 2026).

> **Satyam is your personal autonomous agent — like Muse, but fully yours, at ₹0.** You tell it what to do in chat, and it does the work: writes code, pushes to GitHub, researches websites and makes Excel reports, does Kaggle work, manages files.

**Design:** Light Colourful — halka pastel gradient (sky blue → lavender → peach), glass bubbles, premium look. Satyam ne khud pick kiya (v0.2.1).

---

## Kya kar sakta hai? (What can it do?)

| Kaam | Kaise |
|---|---|
| **Chat + plan** | Instruction do → Satyam steps plan karta hai → ek-ek karke execute karta hai → result + full step log UI me dikhta hai |
| **GitHub** | Khud code likhta hai, `git init` / commit / push karta hai (tumhare git credentials se — koi password store nahi hota) |
| **Browser** | Visible Chromium kholta hai — tum dekh sakte ho wo click/type/read kar raha hai. Kisi bhi website pe kaam kar sakta hai |
| **Kaggle** | Official Kaggle API se competitions/datasets list, data download, submission |
| **Files + code** | Workspace me files likhta/padhta hai, Python scripts chala ke output dekhta hai, error aaye toh fix karke dobara chalata hai |
| **Memory** | SQLite me yaad rakhta hai — tumne kya bataya, kaunse tasks hue |
| **Settings + Status** | ⚙️ Settings se brain/key/mode sab badlo (bina file edit, bina restart). Status panel setup check karta hai aur har problem ka Hinglish fix batata hai |
| **Stop button** | Chalta hua task kabhi bhi roko — current step khatam hote hi ruk jayega |
| **Android app (v0.3)** | Real Flutter app — Chat / Tasks / Settings / Status tabs, laptop ya cloud server se connect. Laptop pe APK banao (guide neeche + `mobile_app/README.md`) |
| **Voice (v0.4)** | 🎤 Mic button se bol ke likho (English/Hindi/Hinglish), 🔊 se har reply bol ke suno, Settings me auto-speak toggle — sab free, phone/browser pe hi chalta hai, koi API key nahi |
| **WhatsApp / Instagram auto-reply (v0.6, chat control v0.7)** | DMs ka jawab khud de — message aate hi padhega, samjhega, tumhari tarah reply kar dega. Official Meta APIs (WhatsApp Cloud API + Instagram Messaging API), koi ban risk nahi. **Control chat se hota hai** — bolo "ab se Instagram ke messages dekhna" toh ON, "WhatsApp band kar do" toh OFF. Token ek baar chat me khulne wale **secure box** me paste karo (masked, kabhi dikhta nahi) — Settings me messaging ka koi option nahi hai. Setup: `MESSAGING_SETUP.md` |
| **Gmail + OTP + forms (v0.8)** | Gmail padhta hai (official Gmail API, read-only) — "mere Gmail me kya aaya hai?", "Internshala ka mail dikhao". **Email OTP khud bhar dega** — site pe OTP aaye toh Gmail se code padh ke fill kar dega. **Form bhi bharega** — "ye form bhar do". Browser ka profile save rehta hai, toh ek baar Google sign-in ke baad sites pe "Sign in with Google" seedha kaam karta hai. Internshala profile pehle se likha hai (`site-profiles.yaml`) — "Internshala check karo" bolte hi applications/messages dekh lega. Setup: `GMAIL_SETUP.md` |
| **Desktop icon + chat history (v0.9)** | **Desktop pe Satyam icon** — click karo toh chat apni app window me khul jayega (server band ho toh khud start ho jata hai). **Chat history save hoti hai** — band karke dobara kholo toh wahi chat milegi (latest 200 messages, laptop pe save). **Cloud URL bhi chalega** — `desktop/server.txt` me apne Oracle VM ka URL likh do, toh icon seedha cloud server kholega aur laptop band ho toh bhi kaam chalta rahega. Setup: `desktop/DESKTOP_GUIDE.md` (shortcut ek baar `create-shortcut.bat` se banao; auto-start optional) |
| **Phone app (PWA)** | Mobile-first chat UI + PWA — Android home screen pe install ho jata hai (neeche dekho) |

## Architecture

```
Flutter Android app / Phone / Laptop browser  →  FastAPI server (API + chat UI, port 8000)
                               →  Agent planner loop (JSON tool calls, max 15 steps)
                               →  Brain: Ollama local (qwen2.5:3b) ya Gemini free-tier API
                               →  Tools: files · git/GitHub · Playwright browser
                                      · Kaggle API · code runner · SQLite memory
```

Ek hi Python process — koi npm, koi alag frontend build nahi. Sirf Python chahiye.

---

## Setup — laptop pe (Windows 11)

### 1. Pehle se chahiye (ek baar)
- **Python 3.12** — [python.org](https://www.python.org/downloads/) se install karo, install karte waqt **"Add Python to PATH" tick** karo.
- **Ollama** — [ollama.com](https://ollama.com) se install karo, phir terminal me:
  ```
  ollama pull qwen2.5:3b
  ```
  (Ye local AI model hai, ~1.9 GB. Ek baar download, phir hamesha free.)
- **Git** — [git-scm.com](https://git-scm.com/downloads) se install karo.

### 2. Project setup (ek baar)
Zip extract karo, phir folder me:
```
setup.bat
```
Ye virtual environment banata hai, packages install karta hai, aur Playwright Chromium download karta hai. (Linux/macOS/WSL: `bash setup.sh`)

### 3. Chalao — ONE command
```
run.bat
```
Phir browser me kholo: **http://127.0.0.1:8000**

Bas. Chat me kaam bolo. (Linux/macOS/WSL: `bash run.sh`. Manual: `.venv` activate karke `python run.py`.)

### 4. Pehli baar: Status check + Settings (koi file edit nahi)

App khulte hi **Status** panel apne aap khul jayega agar kuch theek nahi hai — Ollama chal raha hai ya nahi, model download hua ya nahi, git configured hai ya nahi, Chromium installed hai ya nahi. Har fail ke neeche Hinglish me fix bhi likha hota hai. Baad me kabhi bhi upar **Status** button dabake dobara check kar sakte ho.

Sab settings app ke andar **⚙️ Settings** se badalti hain — koi file edit karne ki zaroorat nahi, aur save karte hi bina restart ke lagu ho jati hain:
- Brain: Ollama (local) ya Gemini (free API) + model ka naam
- Gemini API key (key kabhi poori dikhai nahi deti — masked rehti hai)
- Approval mode: auto (default) ya ask
- Browser: visible ya headless
- Max steps per task (1–50)

### 5. (Optional) Zyada smart brain — Gemini free tier
Local 3B model chhota hai; planning me kabhi galti kar sakta hai. Free me zyada smart brain chahiye toh:
1. [aistudio.google.com](https://aistudio.google.com) → Get API key (Google account chahiye, **card nahi**).
2. App me **⚙️ Settings** kholo → Brain me **Gemini** chuno → key paste karo → Save. Bas — restart ki zaroorat nahi.
3. Default model `gemini-2.5-flash` hai (free tier, Nov 2026 me verify kiya). Agar Google kabhi is id ko reject kare toh Settings me `gemini-3.8-flash` ya `gemini-3.5-flash-lite` try karo — dono ke bhi free tier hain.

---

## Android app (v0.3 — real Flutter app)

PWA ke alawa ab ek **asli Android app** bhi hai — same Light Colourful
design, same 4 cheezein: **Chat** (live steps + approval card),
**Tasks** (history + detail), **Settings** (server URL + token, brain,
Gemini key, approval, browser, max steps), **Status** (health checks +
Hinglish fix hints).

**APK banana + install karo (laptop pe, ~10 min):**
> Is delivery me ready-made APK nahi hai — build VM ki network policy
> Gradle ko chalne nahi deti (details `DELIVERY_NOTES.md` me). App ka
> source poora verified hai (`flutter analyze` clean), isliye laptop pe
> build aasaani se ho jayega.

1. Poori step-by-step guide **[mobile_app/README.md](mobile_app/README.md)**
   me hai: Flutter SDK + Android Studio install karo, phir
   `mobile_app/` folder me `flutter pub get` aur
   `flutter build apk --debug` chalao.
2. Bana hua APK (`build\app\outputs\flutter-apk\app-debug.apk`) ko
   phone pe bhejo (USB / WhatsApp / Drive) aur kholo → Install.
   Pehli baar "Install unknown apps" allow karna padega.
3. App me **Settings** tab kholo → **Server URL** daalo:
   - Laptop server: `http://<laptop-ka-LAN-IP>:8000` (same Wi-Fi;
     `127.0.0.1` phone pe kaam nahi karega)
   - Cloud server: `https://tumhara-domain` (neeche Oracle section dekho)
4. Cloud server ho toh **API token** bhi daalo (VM ke `deploy/.env`
   wala `API_TOKEN`). Laptop server pe token ki zaroorat nahi.
5. Save dabao — top pe "● online" aana chahiye.

Server URL aur token sirf phone ke **secure storage** me rehte hain —
kahin aur nahi bheje jaate.

---

## Approval mode — saaf-saaf

**Default: `auto`.** Satyam jo bolo wo karta hai — koi approval popup nahi, koi rok nahi. Ye default isliye hai kyunki tumne full-auto manga tha.

Agar kabhi chaho ki bahar jaane wale actions (git push/clone, Kaggle submit) se pehle ek click me poochhe, toh **⚙️ Settings** me Approval mode ko **ask** kar do (bina restart ke lagu ho jayega). Phir UI me Approve/Reject card aayega. Iske alawa agent me koi hardcoded restriction nahi hai.

**Task rokna:** koi task chalte waqt **■ Stop** button dabao — current step khatam hote hi task ruk jayega.

---

## Phone se kaise chalaye (Muse jaisa app experience)

UI mobile-first hai — phone pe full-screen chat app jaisa lagta hai, input neeche pinned hai, steps bottom-sheet me dikhte hain. Teen tareeke hain:

### (a) Same Wi-Fi — sabse aasan, ghar ke andar
1. `.env` me `HOST=0.0.0.0` kar do, server restart karo.
2. Laptop ka LAN IP nikalo: Windows me `ipconfig` chalao → `IPv4 Address` (jaise `192.168.1.5`).
3. Phone ke Chrome me kholo: `http://192.168.1.5:8000` (laptop aur phone ek hi Wi-Fi pe hon).
4. Windows Firewall pehli baar poochhe toh **Allow** kar do.
5. Chrome menu → **Add to Home screen** se shortcut banao. (HTTP hone ki wajah se full PWA install nahi hoga — shortcut Chrome me khulega, lekin chalega poora.)

### (b) Cloudflare Tunnel — free, kahin se bhi, full app install
Laptop on rehne pe phone kahin se bhi connect ho jayega, aur HTTPS milne se **full PWA install** (home screen app, standalone) bhi chalega:
1. [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect/downloads/) download karo (free, **koi account/card nahi** chahiye quick tunnel ke liye).
2. Ek terminal me Satyam chalao (`run.bat`), doosre me:
   ```
   cloudflared tunnel --url http://localhost:8000
   ```
3. Jo `https://....trycloudflare.com` URL mile, use phone ke Chrome me kholo → **Add to Home screen** / **Install app**. Ab Satyam phone pe ek app ki tarah chalega.
4. Note: laptop band hote hi tunnel band. URL har baar naya banta hai (quick tunnel).

### (c) Oracle Always Free VM — sach me 24×7, kahin se bhi
Laptop band ho tab bhi Satyam chalta rahe. Poori step-by-step guide:
**[deploy/ORACLE_GUIDE.md](deploy/ORACLE_GUIDE.md)** (Hinglish + English).

Short me:
1. [Oracle Cloud](https://www.oracle.com/cloud/free/) pe Always Free account banao (signup ke liye card verification chahiye, charge nahi hota). Home region **Mumbai (ap-mumbai-1)** chuno — ye permanent hota hai.
2. **Always Free** Ampere A1 VM launch karo: 2 OCPU + 12 GB RAM, Ubuntu 24.04. (June 2026 se limit 2 OCPU/12 GB hai. ARM capacity kabhi-kabhi "out of capacity" dikhata hai — odd hours me dobara try karo.)
3. VM ke security list me ports **80 aur 443** kholo.
4. Project ko VM pe copy karo (scp), SSH karke **`bash deploy/deploy.sh`** chalao — ye Docker install karta hai, backend + Caddy (automatic free HTTPS) start karta hai, systemd se boot pe restart set karta hai, aur `/health` keep-alive cron lagata hai.
5. `deploy/.env` me **DOMAIN** (jaise `<public-ip>.nip.io` — free HTTPS) aur **GEMINI_API_KEY** daalo, phir deploy.sh dobara chalao.
6. Phone app / PWA me `https://tumhara-domain` daalo + **API token** (deploy.sh ne generate kiya tha) — bas, 24×7 Satyam ready.
> Honest caveat: Oracle idle VM (7 din tak 20% se kam use) reclaim kar sakta hai — deploy.sh wala keep-alive cron risk kam karta hai, guarantee nahi deta. Guide me sab likha hai.

---

## Demo — doston ko dikhane ke liye

Poori guide: **[DEMO_GUIDE.md](DEMO_GUIDE.md)**. Teen demo ready hain:

1. **Chat + planning** — Satyam plan banata hai aur project files bana deta hai.
2. **GitHub** — "ek Python project banao aur GitHub pe push karo" — code likhta hai, commit karta hai, push karta hai. Doston ke saamne github.com pe refresh karke dikhao.
3. **Browser + Excel** — Wikipedia se research karke Excel report banata hai, visible browser me sab dikhta hai. (Standalone script bhi hai: `python demos/demo3_browser_excel.py "Machine Learning"`)

UI me teen demo chips bhi hain — dabao, prompt bhar jayega, Send dabao.

## Kaggle setup (jab chahiye)
1. Terminal me: `kaggle auth login` (browser me Kaggle login hoga — sabse aasan).
2. Ya kaggle.com → Settings → API → Create New Token → `kaggle.json` ko `C:\Users\<tum>\.kaggle\kaggle.json` me rakho.

## Site notes (IITM portal wagera)
Browser agent kisi bhi site ko generically chalata hai — page padh ke plan banata hai. Kisi site ka khaas note likhna ho toh [`site-profiles.yaml`](site-profiles.yaml) me likho (example andar commented hai). **Internshala ka profile pehle se likha hai** (login URL, applications/messages kahan hain) — "Internshala check karo" bolte hi agent use padh ke kaam karega. Koi hardcoded selector ship nahi kiya gaya, kyunki bina verify kiye selector likhna galat hoga.

## Troubleshooting

Sabse pehle app me **Status** button dabao — wo bata dega kya theek hai aur kya nahi, fix ke saath.

| Problem | Fix |
|---|---|
| "Ollama se connect nahi ho paya" | Ollama app kholo ya `ollama serve` chalao; `ollama pull qwen2.5:3b` check karo. Ya Settings me Gemini brain chuno |
| Jawab bahut slow | Pehli baar model load hone me time lagta hai. Ya Gemini free tier use karo (Settings me) |
| "Chromium launch nahi ho paya" | `playwright install chromium` dobara chalao (venv active karke) |
| `git commit` fail: user.name/email | `git config --global user.name "Tumhara Naam"` aur `git config --global user.email "tum@email.com"` |
| Push pe login maange | Terminal me ek baar manually `git push` karke login kar lo, phir demo chalao |
| Phone se connect nahi ho raha | `.env` me `HOST=0.0.0.0` hai? Server restart kiya? Ek hi Wi-Fi? Firewall Allow? |
| Task atak gaya lag raha hai | **■ Stop** dabao — current step khatam hote hi ruk jayega. Phir dobara bolo |
| CAPTCHA aa gaya | Agent khud solve nahi kar sakta — visible browser me tum solve karo, phir agent ko "continue" bolo |
| SMS OTP aa gaya | Agent chat me code maangega ("SMS pe aaya OTP bhejo") — code bhej do, wo khud bhar dega (EMAIL OTP wo Gmail se khud bharta hai — v0.8) |

## Cost — ₹0
Ollama local model free. Gemini free tier (rate limits ke saath). Playwright, FastAPI, Kaggle API sab free. Cloudflare Tunnel quick tunnel free. Oracle Always Free VM free (card sirf verification ke liye). Voice bhi free hai — browser/phone ki speech services use hoti hain, koi API key nahi. Koi paid cheez is project me nahi hai.

## Voice — bol ke baat karo (v0.4, PWA + Android app dono me)

- **🎤 Mic button** (send button ke bagal me): dabao, bolo — tumhari baat likh ke composer me aa jayegi. Edit kar sakte ho, phir **send** dabao — apne aap send nahi hota. Dobara mic dabao ya ruk jao toh sunna band ho jata hai. Sunte waqt mic laal ho ke pulse karta hai aur "Sun raha hoon…" dikhta hai.
- **🔊 button** har agent message pe: dabao toh jawab bol ke sunayega. Dobara dabao toh ruk jayega.
- **Auto-speak** (Settings me, default **band**): ON karo toh har reply apne aap bol ke sunayega. Stop dabane ya naya message bhejne se bolna ruk jata hai.
- **Language:** bolne ke liye en-IN pehle try hota hai (English + Hinglish), zaroorat pade toh hi-IN fallback. Jawab usi language me aata hai jis me tum likhte/bolte ho (default English).
- **Browser support (PWA):** voice input ke liye **Chrome** chahiye (Android ya desktop) — Firefox/Safari me mic dabane pe saaf hint dikhega, app nahi tootega. Awaaz sunna (speaker button) zyadatar modern browsers me chalta hai.

## Limits — sach wale
- **Local 3B model** chhota hai: lambi planning me kabhi galti ya loop kar sakta hai. Demo ke liye Gemini free tier zyada reliable hai.
- **CAPTCHA** agent solve nahi karta — tumhe visible browser me karna hota hai. (EMAIL OTP wo Gmail se khud bhar deta hai — v0.8; SMS OTP ke liye wo chat me code maangta hai aur khud bhar deta hai — v0.8.1.)
- **24×7** sirf Oracle VM (c) se — laptop band hote hi (a) aur (b) band.
- **Kuch websites bots block karti hain** (jaise Amazon) — unpe browser automation atak sakta hai.
- **Cloud server ka auth** — `API_TOKEN` set ho toh `/chat`, `/tasks`, `/settings`, `/approve`, `/memory` sirf us token se khulte hain (Flutter app aur PWA dono token bhejte hain); `/health` public rehta hai. Token set nahi hai (laptop) toh pehle jaisa hi khula rehta hai — isliye laptop server sirf apne Wi-Fi pe chalao, public network pe nahi.

## Project structure
```
satyam-ai/
├── run.py / run.bat / run.sh     one-command start (Ollama warning ke saath)
├── setup.bat / setup.sh          one-time setup (har step pe Hinglish status)
├── backend/app/                  FastAPI server, agent loop, brain, memory, approvals
│   ├── health.py                 Status panel checks (Ollama, Gemini, git, browser, Gmail…)
│   ├── tools/                    files · github · browser · kaggle · code_run · gmail · messaging
│   ├── gmail/                    Gmail API (OAuth, read-only) + OTP extraction
│   └── static/                   chat UI (mobile-first) + PWA files + Settings/Status
├── GMAIL_SETUP.md                Gmail + Google sign-in setup guide (Hinglish)
├── MESSAGING_SETUP.md            WhatsApp/Instagram auto-reply setup guide
├── demos/                        3 friend-ready demos
├── mobile_app/                   Flutter Android app (Chat / Tasks / Settings / Status)
├── deploy/                       Oracle cloud: Dockerfile, docker-compose, Caddy, systemd, deploy.sh, ORACLE_GUIDE.md
├── desktop/                      Windows desktop icon: Satyam.bat launcher, server.txt, create-shortcut.ps1/.bat, satyam.ico, DESKTOP_GUIDE.md
├── tests/smoke_test.py           python tests/smoke_test.py (45 tests)
├── site-profiles.yaml            per-site notes (Internshala profile included)
└── .env.example                  default settings (Settings screen se badalti hain)
```

## Version
**v0.9.1** (23 Nov 2026) — **Naya 3D app icon** (icon-swap release — sirf icon artwork + version badla hai, baaki sab v0.9.0 jaisa hi hai): user ne FINAL icon pick kiya — **3D teal-glass S with gold rings** (sheeshe wala gehara neela S, sunehri orbit rings, halka neela background, asli 3D render). PWA icons (180/192/512), Android launcher icons (5 densities) aur desktop `.ico` (7 sizes, 16–256px) sab usi se dobara bane hain — master `design/icon-final-3d.png` (512px, rounded corners). Service worker cache v15. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.9.0** (23 Nov 2026) — **Desktop icon + chat history** (user chahta hai laptop ki screen pe icon ho — click kare toh wahi chat khule, aur laptop band ho toh bhi kaam chale): **Desktop pe Satyam icon** — `desktop/create-shortcut.bat` ek baar chalao, Desktop pe naya Double Orbit wala icon ban jayega. Click karte hi launcher (`desktop/Satyam.bat`) server check karta hai — band ho toh minimized window me khud start kar deta hai — phir chat Chrome/Edge ki app-mode window me khulta hai (tabs/address bar nahi, bilkul app jaisa). **Chat history ab save hoti hai** — har message + agent ka jawab SQLite me save hota hai (latest 200 messages), band karke dobara kholo toh wahi chat milegi, welcome ke neeche. OTP code kabhi save nahi hota. **Cloud URL support** — `desktop/server.txt` me apne Oracle VM ka URL likh do, toh launcher kuch local start nahi karega, seedha cloud server kholega — laptop band ho toh bhi kaam chalta rahega. Auto-start optional hai (`create-shortcut.bat -AutoStart` — laptop on hote hi server khud chale). **Naya app icon** — user ne "Double Orbit" pick kiya (sky-to-teal-to-mint gradient, white S, double crossing orbit rings): PWA icons, Android launcher icons (5 densities) aur desktop `.ico` sab usi se bane hain. Guide: `desktop/DESKTOP_GUIDE.md`. Service worker cache v14. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo (history bhi saath aa jayegi), phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.8.3** (23 Nov 2026) — **Clean chat screen** (user feedback — chat me bahut faltu ka text tha): ab chat me sirf welcome message hai — "Hey! I'm Satyam — your personal AI agent. Just tell me what you need, and I'll get it done." Capabilities wala paragraph aur first-time hints hata diye. Composer ka placeholder ab English me hai ("Tell Satyam what to do…"), aur chat pe dikhne wale saare toasts/hints bhi English me hain (voice, listening pill, steps, approval, secure box). Header se model wali subtitle line ("Ollama (qwen2.5:3b) • auto mode") bhi hata di — brain ki info Status panel me hai. Service worker cache v13. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.8.2** (23 Nov 2026) — **English welcome + composer snap-back** (demo video dekhne ke baad user feedback): welcome message ab English me hai — "Hey! I'm Satyam — your personal AI agent. Just tell me what you need, and I'll get it done…" — app ab starting me fixed Hinglish greeting nahi bolega; tum jis language me baat karoge (English/Hindi/Hinglish), wo usi me jawab dega, pehle message se hi. Koi language setting nahi hai — sab automatic hai. Composer bhi theek hua: message bhejte hi box turant ek line ka ho jata hai (pehle do line ka reh jata tha). Service worker cache v12. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.8.1** (23 Nov 2026) — **SMS OTP ask-and-fill** (user ka correction — v0.8 me SMS OTP aane pe agent user ko browser me khud bharne ko bolta tha; ab nahi): site pe SMS OTP aaye toh Satyam chat me code maangega (**"SMS pe aaya OTP bhejo"**), tum code bhej do, wo khud bhar dega aur task continue karega. Browser band nahi hota — OTP wala page persistent session me khula rehta hai, code aate hi fill ho jata hai. Code ek baar use hoke bhool jata hai — memory, task DB, log ya step history me kahin save nahi hota (step args aur task messages bhi masked hote hain). Email OTP pehle jaisa hi poora automatic hai (Gmail se padh ke bharta hai, kabhi poochhta nahi); CAPTCHA abhi bhi tumhe visible browser me karna hota hai. Service worker cache v11. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.8.0** (23 Nov 2026) — **Gmail + email OTP auto-fill + Google auto sign-in + form filling** (user chahta hai Satyam "sab kuchh" kare): Gmail padhta hai — official Gmail API, **read-only** scope (kabhi mail bhejta/delete nahi karta), OAuth 2.0 one-time setup (`python -m backend.app.gmail.auth`, token `data/token.json` me, auto-refresh). Chat me bolo **"mere Gmail me kya aaya hai?"** / **"Internshala ka mail dikhao"**. **Email OTP khud bharta hai** — site pe OTP aaye toh Gmail se code padh ke (sirf pichhle 10 minute ke mails se, purana code kabhi nahi) browser me fill kar dega, single field ho ya multi-box; code kabhi chat/log me nahi dikhta. **Form bhi bharega** — `browser_fill_form` (label/name/placeholder se field dhoondhta hai, select/checkbox bhi, submit karke result batata hai). Browser ab **persistent profile** use karta hai (`data/browser-profile/`) — ek baar Google sign-in ke baad sites pe "Sign in with Google" seedha kaam karta hai, login restart ke baad bhi yaad rehta hai. **Internshala profile** `site-profiles.yaml` me likha hai — "Internshala check karo" bolte hi applications/messages dekh lega. Status panel me Gmail readiness check. Setup guide: `GMAIL_SETUP.md` (Google Cloud project → Gmail API → client_secret.json → one-time auth). Sach wali baatein: sirf EMAIL OTP padha ja sakta hai (SMS OTP nahi), CAPTCHA tumhe karna hoga, kuch sites automation block karti hain. Service worker cache v10. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat` (nayi Google dependencies install hongi); app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.7.0** (23 Nov 2026) — **Chat-controlled messaging + in-chat secure box** (user feedback pe — messaging Settings me nahi, chat se control hona chahiye): Settings se messaging section poora hata diya (PWA + Flutter dono me — toggles + token fields sab gaye). Ab chat me bolo **"ab se Instagram ke messages dekhna"** / **"Instagram ka reply on kar do"** toh auto-reply ON ho jata hai aur reply khud de deta hai (tumse nahi poochhta); **"WhatsApp band kar do"** toh OFF. Token missing ho toh chat me hi ek **secure box** khul jata hai (masked password card, normal message ki tarah nahi) — token wahan ek baar paste karo, `.env` me safe save ho jata hai (kabhi chat me dikhta nahi, kabhi log me nahi aata), aur auto-reply apne aap chalu ho jata hai. `.env` me haath se daalna advanced users ke liye alternative hai. ON/OFF state SQLite me save hoti hai (restart ke baad bhi yaad rehta hai), default OFF — bina bole kabhi reply nahi jayega. v0.6 ka auto-reply engine bilkul same hai (official Meta APIs, webhooks, 24h window, dedupe, rate limit, sender ki language me reply). Status panel ke readiness checks ab chat commands ki taraf hint karte hain. Service worker cache v9. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao. (Note: v0.6 me Settings se ON kiya hua auto-reply v0.7 me default OFF hoga — chat me ek baar "ab se ... dekhna" bolna hoga.)

**v0.6.0** (23 Nov 2026) — WhatsApp + Instagram **auto-reply** (official Meta APIs — user ne official/safe route pick kiya): DMs aate hi Satyam khud padhega, samjhega, aur tumhari tarah casual style me reply kar dega — tumse kabhi nahi poochhega ki kya reply dena hai. WhatsApp Cloud API + Instagram Messaging API (Graph API v26.0), webhook verification + HMAC-SHA256 signature check, message-id dedupe (double reply kabhi nahi), Meta ka 24-hour reply window (uske bahar skip + log), per-contact rate limit (30/hour), per-contact chat history (last 10 turns) se context-aware replies, reply usi language me jis me message aaya (English/Hindi/Hinglish). Settings me per-platform ON/OFF + token/ID/verify-token/app-secret fields (PWA + Flutter app dono me), Status panel me dono platforms ke readiness checks. Setup guide: `MESSAGING_SETUP.md` (Meta app, permanent token, webhook URL — laptop pe ngrok, 24×7 ke liye Oracle cloud). Service worker cache v8. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.5.0** (22 Nov 2026) — Interface ka full redesign, high-quality original graphics (user feedback pe — unhone kaha interface copy/stock lag raha tha, mic Google jaisa lag raha tha): **demo suggestion chips hata diye** (composer ab clean hai), **saare icons ab custom hand-drawn SVG paths hain** — mic ab ek original "orbit mic" design hai (capsule + tilted orbit ring + satellite dot + curved base), speaker cone + equalizer bars, paper-plane send, custom gear/pulse/chat/tasks/list/refresh/check icons. Koi Material Icon, koi icon font, koi emoji nahi — PWA aur Flutter app dono me wahi icon set (Flutter me `flutter_svg` se). Background ab aur smooth pastel flow + soft ambient glows, glass bubbles ab layered shadows + fine light borders ke saath, welcome bubble me gradient accent bar. Koi feature change nahi — chat, voice, settings, status, tasks sab waise hi kaam karte hain. Service worker cache v7. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.4.1** (22 Nov 2026) — Voice buttons ka redesign (user feedback pe): mic ab proper gradient mic icon hai — send button ke barabar size, premium look; speaker button ab agent bubble ke corner pe badge ki tarah baithta hai. Voice ka behaviour same hai (bol ke likho, bol ke suno, auto-speak default band). Service worker cache v6. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao.

**v0.4.0** (22 Nov 2026) — Voice: mic input + spoken replies, PWA aur Flutter app dono me. 🎤 Mic se bol ke likho (transcript composer me aata hai, auto-send nahi hota), 🔊 har agent message ko bol ke suno, Settings me auto-speak toggle (default band). Sab client-side aur free hai — browser ki Web Speech API (PWA) aur Android speech services (app), koi API key ya server change nahi. Service worker cache v5 (purana PWA naya UI apne aap le aayega). Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`; app ke liye `mobile_app/README.md` se APK dobara banao (mic permission ke liye naya APK chahiye).

**v0.3.0** (22 Nov 2026) — Real Flutter Android app (Chat / Tasks / Settings / Status, Light Colourful design, server URL + API token secure storage me) + Oracle Always Free cloud deployment (Docker + Caddy automatic HTTPS + systemd 24×7 + deploy.sh + Hinglish ORACLE_GUIDE.md). Optional `API_TOKEN` auth: cloud server pe set ho toh API calls token maangti hain, laptop pe unset ho toh sab pehle jaisa. Agent ab reply ki language khud adapt karta hai — tum English/Hindi/Hinglish me bolo, wo usi me jawab dega (default English; koi language setting nahi hai). Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`.

**v0.2.1** (22 Nov 2026) — Light Colourful design: pastel gradient UI (sky blue → lavender → peach), glass chat bubbles, gradient logo + new PWA icons, light theme throughout. Koi feature change nahi — v0.2.0 ke sab features waise hi kaam karte hain. Upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo, phir `setup.bat` / `run.bat`. (Phone pe purana PWA install hai toh service worker naya UI apne aap le aayega.)

**v0.2.0** (22 Nov 2026) — Settings screen, Status/health panel, Stop button, brain retry, smoother setup. v0.1 se upgrade: naya zip extract karo, purana `data/` aur `workspace/` copy kar lo (memory + files bach jayenge), phir `setup.bat` / `run.bat`.

## License
Personal project — Satyam Patel. Free to use and modify for personal use.
