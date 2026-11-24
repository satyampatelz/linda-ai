# Linda Desktop Icon — ek click me chat kholo 🖥️

Linda ab laptop ke Desktop pe ek icon ki tarah chalega — bilkul kisi bhi app jaisa. Icon pe click karo, chat khul jayega — **purani chat ke saath** (chat tere laptop pe save hoti hai, band karke dobara kholo toh wahi chat milegi).

> Linda now lives on your Windows desktop like any app. One click on the icon opens your chat — with your previous chat history intact.

## Ek baar ka setup (one-time)

1. Pehle normal setup kar lo (agar abhi tak nahi kiya): `setup.bat` chalao — README me steps hain.
2. `desktop` folder me **`create-shortcut.bat` pe double-click** karo.
3. Ho gaya — Desktop pe **Linda** icon (3D teal-glass L + gold rings wala logo) ban jayega.

Bas. Ab roz **icon pe double-click** karo — server band ho toh khud start ho jayega (pehli baar 10–20 second lagte hain), phir chat apni alag app window me khul jayega. Browser ke tabs/address bar nahi dikhenge — bilkul app jaisa lagega.

## Kaise kaam karta hai? (How it works)

- **Icon → `desktop\Linda.bat`** — ye launcher hai. Wo pehle dekhta hai server chal raha hai ya nahi (`/health` check). Band ho toh apni minimized window me start kar deta hai, phir Chrome (ya Edge, agar Chrome na ho) ko `--app` mode me kholta hai.
- **Server wali window** ("Linda Server" naam se, minimized) peeche chalti rehti hai — ye normal hai. Chat window band karne se kaam nahi rukta: server chalta rehta hai, aur task poora hota rehta hai. Server band karna ho toh us window ko close kar do (ya `Ctrl+C`).
- **Chat history** — har message + agent ka jawab laptop pe `data/satyam.db` me save hota hai (sirf latest 200 messages). Koi OTP code kabhi save nahi hota — jo code chat me bheja, wo bharne ke baad bhool jata hai.

## Cloud server se chalana (laptop band ho toh bhi kaam chale)

Server laptop pe ho toh laptop band karte hi Linda bhi band ho jayega. **Laptop band ho toh bhi kaam chale**, iske liye server Oracle Cloud ke free VM pe chalao (setup: `deploy/ORACLE_GUIDE.md`), phir:

1. `desktop\server.txt` kholo (Notepad me).
2. Last line badal ke apne VM ka URL likh do, jaise `https://linda.example.com` — bas ek line, `#` wali lines ko chhedo mat.
3. Save karo. Icon pe click karo — launcher kuch local start nahi karega, seedha cloud server kholega.

Ab laptop band ho ya phone band ho — kaam cloud pe chalta rahega, baad me phone/laptop se result dekh lena.

> Tip: cloud URL `https://` hona chahiye (deploy guide Caddy se HTTPS lagata hai). `http://` IP wala URL bhi chalega, lekin browser kabhi-kabhi mic (voice input) ko insecure site pe block kar deta hai.

## Auto-start (optional — laptop on hote hi server khud chale)

Terminal me `desktop` folder se chalao:

```
create-shortcut.bat -AutoStart
```

Ye Desktop shortcut ke saath Windows Startup folder me bhi shortcut daal dega. Ab laptop on hote hi Linda server background me khud start ho jayega — icon click karte hi chat turant khul jayega, wait nahi karna padega.

Band karna ho toh: `Win + R` → `shell:startup` → `Linda.lnk` delete kar do.

## Troubleshooting

- **Icon click karne pe blank page khulta hai** — server abhi start ho raha hai. 10–20 second wait karo, phir window me refresh (F5) dabao. Agar phir bhi blank hai toh "Linda Server" wali window me error dekho.
- **"Linda setup nahi hua hai" likha aata hai** — pehle `setup.bat` chalao (ek baar ka kaam), phir icon dobara click karo.
- **Chrome nahi hai** — launcher Edge use kar lega (Windows 11 me pehle se hota hai). Dono na hon toh default browser me khul jayega (tabs ke saath).
- **Icon pe S logo nahi dikh raha** — Windows kabhi-kabhi icon cache refresh nahi karta. Desktop pe right-click → Refresh, ya ek baar logout/login karo.
- **`create-shortcut.bat` chalate hi band ho jata hai** — PowerShell me koi error aaya hoga. Terminal me `desktop` folder se `powershell -NoProfile -ExecutionPolicy Bypass -File .\create-shortcut.ps1` chalao — error dikh jayega.
- **Chat history khaali dikh rahi hai** — history usi server ki dikhti hai jisse connect ho. Laptop server aur cloud server ki history alag-alag hai (har server apni `data/satyam.db` rakhta hai). Purani `data/` folder naye zip me copy karne se history bhi saath aa jati hai.

## Files (is folder me)

| File | Kaam |
|---|---|
| `Linda.bat` | Launcher — server check/start + app window kholta hai |
| `server.txt` | Server URL (laptop default, ya cloud VM ka URL) |
| `create-shortcut.ps1` | Desktop shortcut banata hai (S logo icon ke saath) |
| `create-shortcut.bat` | Upar wali script ka double-click wrapper |
| `linda.ico` | Desktop icon (3D teal-glass L + gold rings logo, 16–256px sizes) |
