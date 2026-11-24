"""Linda launcher — starts the server using HOST/PORT from .env.

Usage (venv active, from the project root):
    python run.py

Or just double-click run.bat (Windows) / run run.sh (Linux/macOS/WSL).

Default: http://127.0.0.1:8000 (laptop only).
For phone access on the same Wi-Fi, set HOST=0.0.0.0 in .env and restart —
then open http://<laptop-LAN-IP>:8000 on the phone. See README.md.

If Ollama is not running, the server still starts (with a warning) — the
Status panel in the app will show exactly what to fix, and the Gemini
brain in Settings works without Ollama.
"""
import httpx
import uvicorn

from backend.app.config import settings


def _ollama_running() -> bool:
    try:
        with httpx.Client(timeout=2, trust_env=False) as client:
            resp = client.get(f"{settings.ollama_url}/api/tags")
        return resp.status_code == 200
    except Exception:  # noqa: BLE001 — any failure means "not running"
        return False


if __name__ == "__main__":
    print("Linda is running.")
    print(f"  Laptop: http://127.0.0.1:{settings.port}")
    if settings.host == "0.0.0.0":
        print(f"  Phone (same Wi-Fi): http://<laptop-LAN-IP>:{settings.port}")
    print(f"  Brain: {settings.model_provider} | Approval: {settings.approval_mode}")
    if settings.model_provider == "ollama" and not _ollama_running():
        print()
        print("  ! WARNING: Ollama is not running — chat won't work until")
        print("    Ollama starts. Open the Ollama app or run 'ollama serve'.")
        print("    (Or pick the Gemini brain in Settings — it doesn't need Ollama.)")
        print("    The server is still running; the Status panel shows everything.")
    print("Press Ctrl+C to stop.")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
    )
