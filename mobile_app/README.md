# Linda — Android app (Flutter)

This is the Linda agent's **real Android app** — the same agent, the same chat,
now on your phone. The laptop PWA (browser) and this app **both talk to the same
server**, so a task started on one also shows up on the other.

## Screens

| Tab | What it does |
|-----|---------------|
| **Chat** | Talk to the agent — live steps, approval card, Stop button, **mic button (speak to type)** and a **speaker badge on agent messages (tap to hear the reply)** |
| **Tasks** | List of past tasks + detail (steps, result) |
| **Settings** | Server URL + API token (saved only on this phone), brain (Ollama/Gemini), Gemini key, approval mode, browser, max steps, **auto-speak** |
| **Status** | Server health checks, with an English fix under each failure |

**There is no language setting** — the agent works out by itself which
language you are speaking in (English / Hindi / Hinglish) and answers in the
same one. The default is English.

**WhatsApp / Instagram auto-reply is also not in Settings (v0.7)** —
say in chat **"start checking my Instagram messages"** to turn it ON,
**"turn off WhatsApp"** to turn it OFF. If the token is missing, a
**secure box** opens right in the chat — paste the token there (it stays
masked, never visible), and auto-reply starts as soon as you save.
Setup guide: `MESSAGING_SETUP.md`.

## Voice — talk to it (v0.4)

- **Mic button** (next to the send button, custom orbit-mic icon): tap it,
  speak — what you say appears typed in the composer. You can edit it, then
  tap **send** — it never sends by itself. Tap the mic again or stop speaking
  and listening stops.
- **Speaker button** on every agent message: tap it to hear the reply spoken
  aloud. Tap it again to stop.
- **Auto-speak** (in Settings, off by default): turn it ON and every reply
  is spoken aloud by itself. Tapping Stop or sending a new message stops
  the speaking.
- Everything runs on the phone itself (Android's speech services) — no
  API key, no money. The first time you tap the mic, Android will ask for
  mic permission — tap **Allow**. If you denied it by mistake, turn the mic
  ON in the phone's Settings → Apps → Linda → Permissions.

## Connecting to the server

1. Open the app → **Settings** tab.
2. Enter the **Server URL**:
   - **Laptop server (same Wi-Fi):** `http://<laptop-IP>:8000`
     (you'll find the IPv4 address with `ipconfig` on the laptop;
     `127.0.0.1` won't work on the phone — that is the phone's own address).
   - **Oracle cloud server:** `https://your-domain` (e.g.
     `https://1.2.3.4.nip.io`) — see `deploy/ORACLE_GUIDE.md`.
3. **API token** — only for the cloud server. Enter the same `API_TOKEN`
   that is in the cloud VM's `deploy/.env` here. The laptop server doesn't
   need a token.
4. Tap **Save settings**. If "● online" shows at the top, you're connected.

## How to build the APK (on a Windows laptop)

> **Needed:** internet + ~10 GB free disk. Once setup is done, each time
> you just run `flutter build apk`.

### Step 1 — Install the Flutter SDK

1. Open https://docs.flutter.dev/get-started/install/windows.
2. Download the **Flutter SDK** (zip, ~700 MB) and extract it to `C:\flutter`
   (don't pick a folder with a space in it, like `C:\Program Files` — it
   won't work).
3. Add `C:\flutter\bin` to your **PATH**:
   - Search "environment variables" in the Start menu →
     "Edit the system environment variables" → **Environment Variables** →
     in User variables select **Path** and click **Edit** → **New** →
     `C:\flutter\bin` → OK.
4. Open a new **Command Prompt** and check:
   ```
   flutter --version
   ```

### Step 2 — Install the Android SDK

The easiest way — via **Android Studio**:

1. Download and install https://developer.android.com/studio.
2. Open Android Studio → **More Actions → SDK Manager** →
   **SDK Tools** tab → tick these:
   - **Android SDK Command-line Tools (latest)**
   - **Android SDK Platform-Tools**
   - **Android SDK Build-Tools**
3. **Apply** → let it install.
4. In Command Prompt:
   ```
   flutter doctor --android-licenses
   ```
   Press `y` at every question (you need to accept the licenses).
5. Check:
   ```
   flutter doctor
   ```
   The Android toolchain line should show a green tick.

### Step 3 — Build the APK

```cmd
cd C:\path\to\linda-ai\mobile_app
flutter pub get
flutter build apk --debug
```

The APK is built here:

```
build\app\outputs\flutter-apk\app-debug.apk
```

### Step 4 — Install it on your phone

- Send the APK to your phone (USB, WhatsApp, or Google Drive).
- Open the file on your phone → tap **Install**. The first time it will ask
  for "Install unknown apps" permission — tap **Allow**.
- Open the app → enter the server URL in Settings → done.

### Release APK (optional)

```cmd
flutter build apk --release
```

> Note: in this project the release build is signed with the **debug key**
> (fine for personal use). To publish on the Play Store you will need to
> create your own keystore — see
> https://docs.flutter.dev/deployment/android#signing-the-app.

## Code structure

```
lib/
  main.dart        App entry + bottom nav (Chat / Tasks / Settings / Status)
  theme.dart       Light Colourful theme (PWA-like gradient + glass bubbles) + LindaIcon (custom SVG icons)
  api.dart         Backend HTTP calls (/chat, /tasks, /settings, /health…)
  storage.dart     Server URL + API token + auto-speak pref (flutter_secure_storage)
  voice.dart       Mic input + spoken replies (speech_to_text + flutter_tts)
  screens/
    chat_screen.dart      Chat + live steps + approval + voice (v0.5: demo chips removed)
    tasks_screen.dart     Task list + detail
    settings_screen.dart  Server + brain settings + auto-speak (no language option)
    status_screen.dart    Health checks + English fix hints
android/           Android scaffolding (Gradle, manifest, launcher icon)
assets/icon.png    App icon (PWA pastel "L" icon)
assets/icons/      Custom hand-drawn SVG icon set (mic, speaker, send, gear, …) — v0.5
```

## Common problems

| Problem | Fix |
|---------|-----|
| `flutter` command not found | Did you add `C:\flutter\bin` to PATH? Open a new Command Prompt. |
| Error in `Android toolchain` | Install the SDK Tools in Android Studio + run `flutter doctor --android-licenses`. |
| App shows "offline" | Is the laptop server running? (Start it with `run.bat`.) Are the phone and laptop on the same Wi-Fi? Does the URL have the laptop's LAN IP, not `127.0.0.1`? |
| "API token is wrong or missing" | Enter the token from the cloud server's `deploy/.env` in Settings — exactly the same, no spaces. |
| Nothing happens when I tap the mic | Is mic permission allowed? Turn the mic ON in Settings → Apps → Linda → Permissions. Is the Google app / speech services up to date? |
| Can't hear the voice | Turn the phone's media volume up; check the "Select to Speak"/TTS engine in Settings → Accessibility. |
| Gradle build out-of-memory | `org.gradle.jvmargs=-Xmx1G` is already set in `android/gradle.properties`; if the laptop is low on RAM, change it to `-Xmx512m`. |
