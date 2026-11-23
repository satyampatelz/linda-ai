@echo off
REM Satyam v0.2 — Windows one-time setup.
REM Run this once (double-click or: setup.bat). Then start with run.bat.
REM Har step pe Hinglish status dikhega; kuch gadbad ho toh wahi ruk jayega.
cd /d %~dp0
setlocal enabledelayedexpansion

echo ============================================
echo   Satyam setup — ek baar ka kaam
echo ============================================
echo.

echo [1/6] Python 3.12+ check kar raha hoon...
py -3.12 --version >nul 2>&1
if %errorlevel%==0 (
  set PY=py -3.12
) else (
  set PY=python
)
%PY% --version >nul 2>&1
if %errorlevel% neq 0 (
  echo   X Python nahi mila.
  echo   python.org se Python 3.12 install karo — install karte waqt
  echo   "Add Python to PATH" tick karna mat bhoolna. Phir setup.bat dobara chalao.
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info>=(3,12) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
  echo   X Python 3.12 ya usse naya chahiye — tumhare paas purana version hai.
  echo   python.org se Python 3.12 install karo, phir setup.bat dobara chalao.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('%PY% --version 2^>^&1') do echo   OK %%v

echo.
echo [2/6] Git check kar raha hoon...
git --version >nul 2>&1
if %errorlevel%==0 (
  for /f "tokens=*" %%v in ('git --version 2^>^&1') do echo   OK %%v
) else (
  echo   ! Git nahi mila — GitHub demo ke liye chahiye hoga.
  echo     git-scm.com se install kar lo. Setup aage badh raha hai.
)

echo.
echo [3/6] Virtual environment bana raha hoon...
if not exist .venv (
  %PY% -m venv .venv
  if %errorlevel% neq 0 (
    echo   X venv ban nahi paya. Python dobara install karke try karo.
    pause
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
echo   OK .venv ready hai.

echo.
echo [4/6] Python packages install ho rahe hain (thoda time lagega)...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo   X pip install fail ho gaya. Internet check karke setup.bat dobara chalao.
  pause
  exit /b 1
)
echo   OK packages install ho gaye.

echo.
echo [5/6] Playwright Chromium install ho raha hai...
playwright install chromium
if %errorlevel% neq 0 (
  echo   ! Chromium install nahi ho paya — browser wala kaam nahi chalega.
  echo     Baad me venv active karke 'playwright install chromium' dobara chalana.
  echo     Status panel me ye check dikh jayega. Setup aage badh raha hai.
) else (
  echo   OK Chromium ready hai.
)

echo.
echo [6/6] .env file...
if not exist .env (
  copy .env.example .env >nul
  echo   OK .env ban gaya (default settings ke saath).
) else (
  echo   OK .env pehle se hai — chheda nahi.
)

echo.
echo ============================================
echo   Setup ho gaya!
echo ============================================
echo   Ollama abhi tak install nahi kiya toh:
echo     1. ollama.com se Ollama install karo
echo     2. Terminal me chalao: ollama pull qwen2.5:3b
echo   (Ya Settings me Gemini free key use kar sakte ho — card nahi lagta.)
echo.
echo   Ab run.bat chalao, phir browser me kholo:
echo     http://127.0.0.1:8000
echo.
pause
