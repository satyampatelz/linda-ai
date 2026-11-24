@echo off
REM Linda v0.9 — creates the Desktop shortcut. Just double-click it.
REM (Runs create-shortcut.ps1 bypassing PowerShell's execution policy —
REM no policy change needed.)
REM For auto-start too, run in a terminal: create-shortcut.bat -AutoStart
cd /d %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-shortcut.ps1" %*
if %errorlevel% neq 0 pause
