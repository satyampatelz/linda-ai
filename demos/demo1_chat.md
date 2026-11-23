# Demo 1 — Chat + Planning (2 minute)

Doston ko pehle ye dikhao: Satyam sirf chatbot nahi hai, wo kaam plan karta hai.

## Setup
1. `run.bat` chalao (ya `bash run.sh`), browser me `http://127.0.0.1:8000` kholo.
2. Ollama chal raha ho (`ollama serve`) aur model download ho (`ollama pull qwen2.5:3b`).
   Agar local model slow lage toh Settings (⚙️) me Gemini free tier on kar lo — demo tez chalega.

## Kya bolna hai
Chat me ye paste karo (ya "👋 Kya kar sakte ho?" chip dabao):

> Mujhe apne baare me batao — tum kya kya kar sakte ho?

Phir ye try karo:

> Mere liye ek Python project ka plan banao: ek to-do list app, FastAPI + HTML.
> Plan ke baad project ke files bhi bana do.

## Doston ko kya dikhega
- Satyam pehle sochta hai (Live steps panel me uske steps dikhte hain).
- Phir wo khud files banata hai — `workspace/` folder me jaake dikhao, files ban gayi hongi.
- Har step ka result UI me live dikhta hai, kuch chhupa nahi hota.

## Agar kuch atak jaye
- "Ollama se connect nahi ho paya" → Ollama app kholo ya `ollama serve` chalao.
- Jawab slow hai → Qwen 3B pehli baar load hone me 10–20 second leta hai, phir tez ho jata hai.
