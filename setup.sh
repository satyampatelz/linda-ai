#!/usr/bin/env bash
# Satyam v0.2 — Linux/macOS/WSL one-time setup.
# Run once: bash setup.sh — then start with: bash run.sh
# Har step pe Hinglish status dikhega; kuch gadbad ho toh wahi ruk jayega.
cd "$(dirname "$0")"

fail() { echo "  X $1"; echo "Setup ruk gaya."; exit 1; }

echo "============================================"
echo "  Satyam setup — ek baar ka kaam"
echo "============================================"
echo

echo "[1/6] Python 3.12+ check kar raha hoon..."
command -v python3 >/dev/null 2>&1 || fail "Python 3 nahi mila. Pehle Python 3.12 install karo (python.org ya system package manager se), phir setup.sh dobara chalao."
python3 -c "import sys; sys.exit(0 if sys.version_info>=(3,12) else 1)" 2>/dev/null \
  || fail "Python 3.12 ya usse naya chahiye — tumhare paas purana version hai. Python 3.12 install karke dobara chalao."
echo "  OK $(python3 --version)"

echo
echo "[2/6] Git check kar raha hoon..."
if command -v git >/dev/null 2>&1; then
  echo "  OK $(git --version)"
else
  echo "  ! Git nahi mila — GitHub demo ke liye chahiye hoga."
  echo "    (Ubuntu/Debian: sudo apt install git). Setup aage badh raha hai."
fi

echo
echo "[3/6] Virtual environment bana raha hoon..."
if [ ! -d .venv ]; then
  python3 -m venv .venv || fail "venv ban nahi paya. (Ubuntu/Debian: sudo apt install python3.12-venv)"
fi
# shellcheck disable=SC1091
. .venv/bin/activate
echo "  OK .venv ready hai."

echo
echo "[4/6] Python packages install ho rahe hain (thoda time lagega)..."
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt || fail "pip install fail ho gaya. Internet check karke setup.sh dobara chalao."
echo "  OK packages install ho gaye."

echo
echo "[5/6] Playwright Chromium install ho raha hai..."
if playwright install chromium; then
  echo "  OK Chromium ready hai."
else
  echo "  ! Chromium install nahi ho paya — browser wala kaam nahi chalega."
  echo "    Baad me venv active karke 'playwright install chromium' dobara chalana."
  echo "    Status panel me ye check dikh jayega. Setup aage badh raha hai."
fi

echo
echo "[6/6] .env file..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  OK .env ban gaya (default settings ke saath)."
else
  echo "  OK .env pehle se hai — chheda nahi."
fi

echo
echo "============================================"
echo "  Setup ho gaya!"
echo "============================================"
echo "  Ollama abhi tak install nahi kiya toh:"
echo "    1. ollama.com se Ollama install karo"
echo "    2. Terminal me chalao: ollama pull qwen2.5:3b"
echo "  (Ya Settings me Gemini free key use kar sakte ho — card nahi lagta.)"
echo
echo "  Ab bash run.sh chalao, phir browser me kholo:"
echo "    http://127.0.0.1:8000"
