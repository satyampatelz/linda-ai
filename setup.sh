#!/usr/bin/env bash
# Linda v0.2 — Linux/macOS/WSL one-time setup.
# Run once: bash setup.sh — then start with: bash run.sh
# Each step shows an English status message; if something goes wrong it stops right there.
cd "$(dirname "$0")"

fail() { echo "  X $1"; echo "Setup stopped."; exit 1; }

echo "============================================"
echo "  Linda setup — a one-time job"
echo "============================================"
echo

echo "[1/6] Checking Python 3.12+..."
command -v python3 >/dev/null 2>&1 || fail "Python 3 not found. Install Python 3.12 first (from python.org or your system package manager), then run setup.sh again."
python3 -c "import sys; sys.exit(0 if sys.version_info>=(3,12) else 1)" 2>/dev/null \
  || fail "Python 3.12 or newer is needed — you have an older version. Install Python 3.12 and run again."
echo "  OK $(python3 --version)"

echo
echo "[2/6] Checking Git..."
if command -v git >/dev/null 2>&1; then
  echo "  OK $(git --version)"
else
  echo "  ! Git not found — you'll need it for the GitHub demo."
  echo "    (Ubuntu/Debian: sudo apt install git). Setup is continuing."
fi

echo
echo "[3/6] Creating the virtual environment..."
if [ ! -d .venv ]; then
  python3 -m venv .venv || fail "Couldn't create the venv. (Ubuntu/Debian: sudo apt install python3.12-venv)"
fi
# shellcheck disable=SC1091
. .venv/bin/activate
echo "  OK .venv is ready."

echo
echo "[4/6] Installing Python packages (this takes a little while)..."
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt || fail "pip install failed. Check your internet and run setup.sh again."
echo "  OK packages installed."

echo
echo "[5/6] Installing Playwright Chromium..."
if playwright install chromium; then
  echo "  OK Chromium is ready."
else
  echo "  ! Chromium install failed — browser tasks won't work."
  echo "    Later, activate the venv and run 'playwright install chromium' again."
  echo "    This check will show up in the Status panel. Setup is continuing."
fi

echo
echo "[6/6] .env file..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  OK .env created (with default settings)."
else
  echo "  OK .env already exists — left untouched."
fi

echo
echo "============================================"
echo "  Setup done!"
echo "============================================"
echo "  If you haven't installed Ollama yet:"
echo "    1. Install Ollama from ollama.com"
echo "    2. In a terminal, run: ollama pull qwen2.5:3b"
echo "  (Or use a Gemini free key in Settings — no card needed.)"
echo
echo "  Now run bash run.sh, then open in your browser:"
echo "    http://127.0.0.1:8000"
