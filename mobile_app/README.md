# Linda — Android app (Flutter)

Ye Linda agent ka **real Android app** hai — wahi agent, wahi chat,
ab phone pe. Laptop ka PWA (browser) aur ye app **dono ek hi server
se baat karte hain**, isliye ek pe shuru kiya task doosre pe bhi
dikhega.

## Screens

| Tab | Kya karta hai |
|-----|---------------|
| **Chat** | Agent se baat karo — live steps, approval card, Stop button, **mic button (bol ke likho)** aur agent messages pe **speaker badge (bol ke suno)** |
| **Tasks** | Pichle tasks ki list + detail (steps, result) |
| **Settings** | Server URL + API token (sirf is phone me save hota hai), brain (Ollama/Gemini), Gemini key, approval mode, browser, max steps, **auto-speak** |
| **Status** | Server ke health checks, har fail ke neeche Hinglish me fix |

**Language ka koi setting nahi hai** — agent khud samajh jata hai tum
kis language me baat kar rahe ho (English / Hindi / Hinglish) aur usi
me jawab deta hai. Default English hai.

**WhatsApp / Instagram auto-reply bhi Settings me nahi hai (v0.7)** —
chat me bolo **"ab se Instagram ke messages dekhna"** toh ON, **"WhatsApp
band kar do"** toh OFF. Token missing ho toh chat me hi ek **secure box**
khul jata hai — token wahan paste karo (masked rehta hai, kabhi dikhta
nahi), save karte hi auto-reply chalu ho jayega. Setup guide:
`MESSAGING_SETUP.md`.

## Voice — bol ke baat karo (v0.4)

- **Mic button** (send button ke bagal me, custom orbit-mic icon): dabao, bolo — tumhari
  baat likh ke composer me aa jayegi. Edit kar sakte ho, phir **send**
  dabao — apne aap send nahi hota. Dobara mic dabao ya ruk jao toh
  sunna band ho jata hai.
- **Speaker button** har agent message pe: dabao toh jawab bol ke sunayega.
  Dobara dabao toh ruk jayega.
- **Auto-speak** (Settings me, default band): ON karo toh har reply
  apne aap bol ke sunayega. Stop dabane ya naya message bhejne se bolna
  ruk jata hai.
- Sab kuch phone pe hi chalta hai (Android ki speech services) — koi
  API key nahi, koi paisa nahi. Pehli baar mic dabane pe Android mic
  ki permission maangega — **Allow** kar do. Agar galti se deny ho gaya
  toh phone ki Settings → Apps → Linda → Permissions me mic ON karo.

## Server se connect karna

1. App kholo → **Settings** tab.
2. **Server URL** daalo:
   - **Laptop server (same Wi-Fi):** `http://<laptop-ka-IP>:8000`
     (laptop pe `ipconfig` me IPv4 address milega; `127.0.0.1` phone pe
     kaam nahi karega — wo phone ka khud ka address hota hai).
   - **Oracle cloud server:** `https://tumhara-domain` (jaise
     `https://1.2.3.4.nip.io`) — `deploy/ORACLE_GUIDE.md` dekho.
3. **API token** — sirf cloud server ke liye. Cloud VM ke
   `deploy/.env` me jo `API_TOKEN` hai, wahi yahan daalo. Laptop
   server pe token ki zaroorat nahi hai.
4. **Save settings** dabao. Top pe "● online" dikhega toh connected hai.

## APK banane ka tareeka (Windows laptop pe)

> **Zaroorat:** internet + ~10 GB free disk. Ek baar setup ho gaya toh
> har baar sirf `flutter build apk` chalana hai.

### Step 1 — Flutter SDK install karo

1. https://docs.flutter.dev/get-started/install/windows kholo.
2. **Flutter SDK** download karo (zip, ~700 MB) aur `C:\flutter` me
   extract karo (koi space wala folder mat lo, jaise
   `C:\Program Files` — nahi chalega).
3. `C:\flutter\bin` ko **PATH** me daalo:
   - Start menu me "environment variables" search karo →
     "Edit the system environment variables" → **Environment Variables** →
     User variables me **Path** select karke **Edit** → **New** →
     `C:\flutter\bin` → OK.
4. Naya **Command Prompt** kholo aur check karo:
   ```
   flutter --version
   ```

### Step 2 — Android SDK install karo

Sabse aasan tareeka — **Android Studio** se:

1. https://developer.android.com/studio download karke install karo.
2. Android Studio kholo → **More Actions → SDK Manager** →
   **SDK Tools** tab → ye tick karo:
   - **Android SDK Command-line Tools (latest)**
   - **Android SDK Platform-Tools**
   - **Android SDK Build-Tools**
3. **Apply** → install hone do.
4. Command Prompt me:
   ```
   flutter doctor --android-licenses
   ```
   Har sawaal pe `y` dabao (licenses accept karni hain).
5. Check karo:
   ```
   flutter doctor
   ```
   Android toolchain wali line me green tick aana chahiye.

### Step 3 — APK banao

```cmd
cd C:\path\to\linda-ai\mobile_app
flutter pub get
flutter build apk --debug
```

APK yahan banega:

```
build\app\outputs\flutter-apk\app-debug.apk
```

### Step 4 — Phone pe install karo

- APK ko phone pe bhejo (USB, WhatsApp, ya Google Drive).
- Phone pe file kholo → **Install** dabao. Pehli baar "Install unknown
  apps" ki permission maangega — **Allow** kar do.
- App kholo → Settings me server URL daalo → bas, ho gaya.

### Release APK (optional)

```cmd
flutter build apk --release
```

> Note: is project me release build **debug key** se sign hoti hai
> (personal use ke liye theek hai). Play Store pe publish karne ke liye
> apna keystore banana padega — dekho
> https://docs.flutter.dev/deployment/android#signing-the-app.

## Code ka structure

```
lib/
  main.dart        App entry + bottom nav (Chat / Tasks / Settings / Status)
  theme.dart       Light Colourful theme (PWA jaisa gradient + glass bubbles) + LindaIcon (custom SVG icons)
  api.dart         Backend ke HTTP calls (/chat, /tasks, /settings, /health…)
  storage.dart     Server URL + API token + auto-speak pref (flutter_secure_storage)
  voice.dart       Mic input + spoken replies (speech_to_text + flutter_tts)
  screens/
    chat_screen.dart      Chat + live steps + approval + voice (v0.5: demo chips hata diye)
    tasks_screen.dart     Task list + detail
    settings_screen.dart  Server + brain settings + auto-speak (koi language option nahi)
    status_screen.dart    Health checks + Hinglish fix hints
android/           Android scaffolding (Gradle, manifest, launcher icon)
assets/icon.png    App icon (PWA wali pastel "S" icon)
assets/icons/      Custom hand-drawn SVG icon set (mic, speaker, send, gear, …) — v0.5
```

## Common problems

| Problem | Fix |
|---------|-----|
| `flutter` command nahi mil raha | PATH me `C:\flutter\bin` daala? Naya Command Prompt kholo. |
| `Android toolchain` me error | Android Studio me SDK Tools install karo + `flutter doctor --android-licenses` chalao. |
| App me "offline" dikh raha | Laptop server chal raha hai? (`run.bat` se start karo.) Phone aur laptop same Wi-Fi pe hain? URL me laptop ka LAN IP hai, `127.0.0.1` nahi? |
| "API token galat" | Cloud server ke `deploy/.env` wala token Settings me daalo — bilkul same, koi space nahi. |
| Mic dabane pe kuch nahi hota | Mic permission allow hai? Settings → Apps → Linda → Permissions me mic ON karo. Google app / speech services update hai? |
| Awaaz sunai nahi de rahi | Phone ka media volume up karo; Settings → Accessibility me "Select to Speak"/TTS engine check karo. |
| Gradle build me out-of-memory | `android/gradle.properties` me `org.gradle.jvmargs=-Xmx1G` pehle se set hai; laptop pe RAM kam ho toh `-Xmx512m` kar do. |
