# Demo 2 — GitHub: Code likhe, commit kare, push kare (5 minute)

Ye sabse impressive demo hai: Linda khud code likhta hai aur GitHub pe push karta hai.

## Pehle se taiyaar rakho (ek baar)
1. Git install ho aur ye set ho (ek baar, terminal me):
   ```
   git config --global user.name "Satyam Patel"
   git config --global user.email "sp3856201@gmail.com"
   ```
2. GitHub pe ek **empty repo** banao (github.com → New repository → naam `hello-linda` → public → NO README, NO .gitignore, NO license). URL copy karo, jaise `https://github.com/satyampatelz/hello-linda.git`.
3. GitHub login terminal me ek baar kar lo (`git` pehli baar push karte waqt login maangega — browser se sign in ho jayega). Isse demo me push atakega nahi.

## Demo
1. `run.bat` chalao, `http://127.0.0.1:8000` kholo.
2. Chat me ye paste karo (repo URL apna daalo):

> Workspace me 'hello-linda' naam ka ek Python project banao — ek calculator CLI
> with tests — phir use git me commit karo aur is repo pe push karo:
> https://github.com/satyampatelz/hello-linda.git

## Doston ko kya dikhega
- Live steps me: files likhi → git init → commit → remote add → **push**.
- Phir github.com pe repo kholo — code wahan live hai. Doston ke saamne refresh karke dikhao.
- Ye sab Linda ne khud kiya — tumne sirf ek line likhi thi.

## Notes
- Push ke liye internet + GitHub login chahiye. Agar login na ho toh terminal me ek baar `git push` manually karke login kar lo, phir demo dobara chalao.
- Repo URL galat ho toh agent error dikhayega — URL check karke dobara bolo.
