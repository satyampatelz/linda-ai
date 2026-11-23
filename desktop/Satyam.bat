@echo off
REM Satyam v0.9 — desktop launcher (Windows).
REM Desktop shortcut ("Satyam" icon) isi ko chalata hai: local server
REM band ho toh start karta hai, phir chat apni alag app window me
REM kholta hai — browser ke tabs/address bar ke bina, bilkul app jaisa.
REM
REM Server URL desktop\server.txt me hai (default http://127.0.0.1:8000).
REM Agar wahan apne Oracle cloud VM ka URL likha hai, toh launcher kuch
REM local start nahi karta — seedha cloud server kholta hai, aur laptop
REM band ho toh bhi kaam chalta rehta hai (server cloud pe hai).
REM Env var SATYAM_SERVER_URL set ho toh wo server.txt se upar mana jata hai.

setlocal enabledelayedexpansion
cd /d %~dp0\..

REM --- Server URL: env var wins, else server.txt, else laptop default.
set "SERVER_URL=%SATYAM_SERVER_URL%"
if not defined SERVER_URL (
  for /f "usebackq eol=# tokens=* delims=" %%u in ("%~dp0server.txt") do (
    if not defined SERVER_URL set "SERVER_URL=%%u"
  ) 2>nul
)
if not defined SERVER_URL set "SERVER_URL=http://127.0.0.1:8000"

REM --- Local server (127.0.0.1 / localhost)? Make sure it is running.
set "URL_CHECK=!SERVER_URL!"
if not "!URL_CHECK:127.0.0.1=!"=="!URL_CHECK!" goto :local
if not "!URL_CHECK:localhost=!"=="!URL_CHECK!" goto :local
goto :open

:local
call :healthcheck
if "!HEALTH!"=="200" goto :open
REM Server band hai — apni minimized window me start karo.
if not exist .venv\Scripts\python.exe (
  echo Satyam setup nahi hua hai — pehle setup.bat chalao.
  pause
  exit /b 1
)
echo Satyam server start ho raha hai...
start "Satyam Server" /min .venv\Scripts\python.exe run.py
REM /health aane tak ~60 second wait karo.
set "TRIES=0"
:waitloop
timeout /t 2 /nobreak >nul
call :healthcheck
if "!HEALTH!"=="200" goto :open
set /a TRIES+=1
if !TRIES! lss 30 goto :waitloop
echo Server start nahi ho paya (60 second ho gaye).
echo "Satyam Server" wali window me error dekho,
echo ya run.bat se manually chalake dekho kya error aata hai.
pause
exit /b 1

:open
REM Apni app window me kholo — Chrome pehle, Edge agar Chrome na ho.
set "BROWSER="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "!ProgramFiles(x86)!\Google\Chrome\Application\chrome.exe" set "BROWSER=!ProgramFiles(x86)!\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "BROWSER=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "!ProgramFiles(x86)!\Microsoft\Edge\Application\msedge.exe" set "BROWSER=!ProgramFiles(x86)!\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if defined BROWSER (
  start "" "!BROWSER!" --app="!SERVER_URL!"
) else (
  REM Chrome/Edge nahi mila — default browser me kholo (tabs ke saath).
  start "" "!SERVER_URL!"
)
exit /b 0

:healthcheck
REM HEALTH me /health ka HTTP status code aata hai (200 = chal raha hai,
REM 000 = server tak baat nahi ho payi). curl pehle, PowerShell backup.
set "HEALTH=000"
where curl >nul 2>&1
if !errorlevel!==0 (
  for /f "tokens=*" %%c in ('curl -s -o nul -w "%%{http_code}" --max-time 3 "!SERVER_URL!/health" 2^>nul') do set "HEALTH=%%c"
) else (
  for /f "tokens=*" %%c in ('powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri '!SERVER_URL!/health' -UseBasicParsing -TimeoutSec 3).StatusCode } catch { 0 }" 2^>nul') do set "HEALTH=%%c"
)
exit /b
