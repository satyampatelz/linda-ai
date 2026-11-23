# Satyam — Demo Guide (doston ko dikhane ke liye)

Teen demo, sabse aasan se sabse impressive tak. Har demo ke liye `run.bat` chala ke `http://127.0.0.1:8000` kholo. Demos ki detail `demos/` folder me bhi hai.

**Demo se pehle (ek baar):** Ollama chal raha ho (`ollama pull qwen2.5:3b` ho chuka ho). Agar local model slow lage toh Settings (⚙️) me Gemini free tier on kar lo — demo smooth chalega. Status button se sab check kar lo pehle.

---

## Demo 1 — Chat + Planning (2 min) 🗣️
**Dikhao:** Satyam sirf jawab nahi deta, kaam plan karke execute karta hai.

Paste karo (ya UI me "👋 Kya kar sakte ho?" chip dabao):
> Mujhe apne baare me batao — tum kya kya kar sakte ho?

Phir:
> Mere liye ek Python project ka plan banao: ek to-do list app, FastAPI + HTML.
> Plan ke baad project ke files bhi bana do.

**Kya dikhega:** Live steps panel me Satyam ke steps — sochna, files banana. Phir `workspace/` folder kholo — files ban gayi hongi.

## Demo 2 — GitHub: code likhe, commit kare, push kare (5 min) 🐙
**Dikhao:** Satyam khud developer ki tarah kaam karta hai. (Detail: `demos/demo2_github.md`)

**Pehle se:** GitHub pe ek empty repo banao (`hello-satyam`), URL copy karo. Git user.name/email set ho.

Paste karo (URL apna daalo):
> Workspace me 'hello-satyam' naam ka ek Python project banao — ek calculator CLI
> with tests — phir use git me commit karo aur is repo pe push karo:
> https://github.com/satyampatelz/hello-satyam.git

**Kya dikhega:** Live steps — files → git init → commit → push. Phir **github.com pe repo kholo aur refresh karo — code live hai.** Ye wala moment doston ko sabse zyada impress karega.

## Demo 3 — Browser + Excel report (3 min) 🌐
**Dikhao:** Satyam browser khud chalata hai aur report banata hai.

Paste karo (ya UI me "🌐 Research + Excel report" chip dabao):
> Wikipedia pe 'Machine Learning' ke baare me research karo aur 5 key points ki
> ek Excel report workspace me banao.

**Kya dikhega:** Chromium window khud khul ke Wikipedia pe jata hai (visible browser — sab dikhta hai), phir `workspace/` me `Machine_Learning_report.xlsx` ban jata hai. Excel khol ke dikhao.

**Backup (bina LLM ke, 100% deterministic):** agar chat wala demo kabhi atak jaye, terminal me ye chalao:
```
python demos/demo3_browser_excel.py "Machine Learning"
```
Ye wahi kaam seedha karta hai — browser + Excel, koi AI planning nahi.

---

## Demo tips
- **Pehle khud ek baar chala ke dekho** — doston ke saamne pehli baar try mat karo.
- **Gemini free tier** demo ke liye zyada reliable hai (local 3B kabhi slow/galat ho sakta hai).
- **Browser visible rakho** (`BROWSER_HEADLESS=false`) — doston ko dikhna chahiye ki browser khud chal raha hai.
- **Phone se bhi dikha sakte ho** — README me "Phone se kaise chalaye" dekho. Phone pe chat karo, laptop pe browser khud chalta hua dikhega. Doston ko ye bahut impress karega.
- Agar kuch fail ho jaye toh ghabrao mat — Live steps me error dikhta hai, use padh ke dobara bolo ("wo step dobara try karo").
