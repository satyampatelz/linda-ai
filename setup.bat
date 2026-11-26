@echo off
REM Linda v0.2 — Windows one-time setup.
REM Run this once (double-click or: setup.bat). Then start with run.bat.
REM Each step shows an English status message; if something goes wrong it stops right there.
cd /d %~dp0
setlocal enabledelayedexpansion

echo ============================================
echo   Linda setup — a one-time job
echo ============================================
echo.

echo [1/6] Checking Python 3.12+...
py -3.12 --version >nul 2>&1
if %errorlevel%==0 (
  set PY=py -3.12
) else (
  set PY=python
)
%PY% --version >nul 2>&1
if %errorlevel% neq 0 (
  echo   X Python not found.
  echo   Install Python 3.12 from python.org — while installing,
  echo   don't forget to tick "Add Python to PATH". Then run setup.bat again.
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info>=(3,12) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
  echo   X Python 3.12 or newer is needed — you have an older version.
  echo   Install Python 3.12 from python.org, then run setup.bat again.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('%PY% --version 2^>^&1') do echo   OK %%v

echo.
echo [2/6] Checking Git...
git --version >nul 2>&1
if %errorlevel%==0 (
  for /f "tokens=*" %%v in ('git --version 2^>^&1') do echo   OK %%v
) else (
  echo   ! Git not found — you'll need it for the GitHub demo.
  echo     Install it from git-scm.com. Setup is continuing.
)

echo.
echo [3/6] Creating the virtual environment...
if not exist .venv (
  %PY% -m venv .venv
  if %errorlevel% neq 0 (
    echo   X Couldn't create the venv. Try reinstalling Python.
    pause
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
echo   OK .venv is ready.

echo.
echo [4/6] Installing Python packages (this takes a little while)...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo   X pip install failed. Check your internet and run setup.bat again.
  pause
  exit /b 1
)
echo   OK packages installed.

echo.
echo [5/6] Installing Playwright Chromium...
playwright install chromium
if %errorlevel% neq 0 (
  echo   ! Chromium install failed — browser tasks won't work.
  echo     Later, activate the venv and run 'playwright install chromium' again.
  echo     This check will show up in the Status panel. Setup is continuing.
) else (
  echo   OK Chromium is ready.
)

echo.
echo [6/6] .env file...
if not exist .env (
  if exist .env.example (
    copy .env.example .env >nul
    if exist .env (
      echo   OK .env created (with default settings).
    ) else (
      echo   ! .env copy failed — the app will create it on first Settings save.
    )
  ) else (
    echo   ! .env.example not found — the app will create .env on first Settings save.
  )
) else (
  echo   OK .env already exists — left untouched.
)

echo.
echo ============================================
echo   Setup done!
echo ============================================
echo   If you haven't installed Ollama yet:
echo     1. Install Ollama from ollama.com
echo     2. In a terminal, run: ollama pull qwen2.5:3b
echo   (Or use a Gemini free key in Settings — no card needed.)
echo.
echo   Now run run.bat, then open in your browser:
echo     http://127.0.0.1:8000
echo.
pause
