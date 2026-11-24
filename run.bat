@echo off
REM Linda v0.2 — start the server (Windows). Open http://127.0.0.1:8000
cd /d %~dp0
if not exist .venv (echo Run setup.bat first! & pause & exit /b 1)
call .venv\Scripts\activate.bat
echo.
echo Linda is starting — open it in your browser:
echo   http://127.0.0.1:8000
echo.
python run.py
pause
