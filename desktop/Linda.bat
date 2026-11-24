@echo off
REM Linda v0.9 — desktop launcher (Windows).
REM The desktop shortcut ("Linda" icon) runs this: it starts the local
REM server if it is stopped, then opens the chat in its own app window —
REM no browser tabs or address bar, just like a real app.
REM
REM The server URL lives in desktop\server.txt (default http://127.0.0.1:8000).
REM If that file holds your Oracle cloud VM's URL, the launcher starts
REM nothing locally — it opens the cloud server directly, and work keeps
REM going even with the laptop off (the server is in the cloud).
REM If the LINDA_SERVER_URL env var is set, it wins over server.txt.

setlocal enabledelayedexpansion
cd /d %~dp0\..

REM --- Server URL: env var wins, else server.txt, else laptop default.
set "SERVER_URL=%LINDA_SERVER_URL%"
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
REM Server is stopped — start it in its own minimized window.
if not exist .venv\Scripts\python.exe (
  echo Linda isn't set up yet — run setup.bat first.
  pause
  exit /b 1
)
echo Starting the Linda server...
start "Linda Server" /min .venv\Scripts\python.exe run.py
REM Wait up to ~60 seconds for /health to answer.
set "TRIES=0"
:waitloop
timeout /t 2 /nobreak >nul
call :healthcheck
if "!HEALTH!"=="200" goto :open
set /a TRIES+=1
if !TRIES! lss 30 goto :waitloop
echo The server didn't start (60 seconds passed).
echo Check the error in the "Linda Server" window,
echo or run it manually with run.bat to see the error.
pause
exit /b 1

:open
REM Open in its own app window — Chrome first, Edge if Chrome is missing.
set "BROWSER="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "!ProgramFiles(x86)!\Google\Chrome\Application\chrome.exe" set "BROWSER=!ProgramFiles(x86)!\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "BROWSER=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "!ProgramFiles(x86)!\Microsoft\Edge\Application\msedge.exe" set "BROWSER=!ProgramFiles(x86)!\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if defined BROWSER (
  start "" "!BROWSER!" --app="!SERVER_URL!"
) else (
  REM Chrome/Edge not found — open in the default browser (with tabs).
  start "" "!SERVER_URL!"
)
exit /b 0

:healthcheck
REM HEALTH holds /health's HTTP status code (200 = running,
REM 000 = couldn't reach the server). curl first, PowerShell as backup.
set "HEALTH=000"
where curl >nul 2>&1
if !errorlevel!==0 (
  for /f "tokens=*" %%c in ('curl -s -o nul -w "%%{http_code}" --max-time 3 "!SERVER_URL!/health" 2^>nul') do set "HEALTH=%%c"
) else (
  for /f "tokens=*" %%c in ('powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri '!SERVER_URL!/health' -UseBasicParsing -TimeoutSec 3).StatusCode } catch { 0 }" 2^>nul') do set "HEALTH=%%c"
)
exit /b
