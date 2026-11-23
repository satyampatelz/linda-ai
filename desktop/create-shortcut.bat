@echo off
REM Satyam v0.9 — Desktop shortcut banata hai. Double-click karo, bas.
REM (PowerShell ki execution policy ko bypass karke create-shortcut.ps1
REM chalata hai — policy change karne ki zaroorat nahi.)
REM Auto-start bhi chahiye toh terminal me: create-shortcut.bat -AutoStart
cd /d %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-shortcut.ps1" %*
if %errorlevel% neq 0 pause
