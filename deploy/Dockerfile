# Satyam — cloud backend image (Oracle Always Free VM).
#
# Build context is the PROJECT ROOT (see docker-compose.yml), so the
# backend code is copied from ./backend. Run with docker compose from
# the deploy/ folder — see deploy.sh and ORACLE_GUIDE.md.
#
# The cloud VM has no GPU and no screen, so:
#   * the brain is Gemini's free tier (MODEL_PROVIDER=gemini in .env)
#   * the browser runs headless (BROWSER_HEADLESS=true in compose)
# Everything else works exactly like the laptop version.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# git (GitHub tool) + curl (healthcheck). Playwright's --with-deps pulls
# the browser system libraries itself during the pip step below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY backend ./backend
COPY run.py ./
COPY demos ./demos
COPY site-profiles.yaml ./

RUN mkdir -p /app/data /app/workspace

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
