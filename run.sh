#!/usr/bin/env bash
# Linda v0.2 — start the server (Linux/macOS/WSL). Open http://127.0.0.1:8000
set -e
cd "$(dirname "$0")"
[ -d .venv ] || { echo "Run bash setup.sh first!"; exit 1; }
# shellcheck disable=SC1091
. .venv/bin/activate
echo
echo "Linda is starting — open it in your browser:"
echo "  http://127.0.0.1:8000"
echo
exec python run.py
