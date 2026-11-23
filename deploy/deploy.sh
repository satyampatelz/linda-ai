#!/usr/bin/env bash
# Satyam cloud deploy — run ONCE on the Oracle VM (Ubuntu 24.04).
#
# Usage (from the project root on the VM, e.g. ~/satyam-ai):
#     bash deploy/deploy.sh
#
# First run: installs Docker, creates deploy/.env, generates a random
# API_TOKEN, then STOPS and asks you to fill in DOMAIN + GEMINI_API_KEY.
# Second run (after you edited .env): builds, starts everything, installs
# the systemd unit (auto-start on boot) and the keep-alive cron.
#
# Re-run any time to update: it rebuilds and restarts cleanly, and your
# data/ + workspace/ volumes are kept.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY_DIR="$PROJECT_DIR/deploy"
ENV_FILE="$DEPLOY_DIR/.env"

say() { printf '\n==> %s\n' "$*"; }

# --- 1. Docker -----------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    say "Docker install ho raha hai..."
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io docker-compose-v2
    sudo usermod -aG docker "$USER" || true
    echo "NOTE: pehli baar Docker install hua hai — is script ko dobara"
    echo "chalane se pehle ek baar logout karke wapas login karo (taaki"
    echo "docker group lagu ho jaye), ya abhi ke liye 'sudo' se chalao."
else
    echo "Docker pehle se installed hai: $(docker --version)"
fi

# --- 2. .env --------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
    say "deploy/.env banaya ja raha hai..."
    cp "$DEPLOY_DIR/.env.example" "$ENV_FILE"
fi

# Generate a random API_TOKEN if it is empty/missing.
if ! grep -q '^API_TOKEN=.\+' "$ENV_FILE" 2>/dev/null; then
    TOKEN="$(openssl rand -hex 24 2>/dev/null || od -An -tx1 -N24 /dev/urandom | tr -d ' \n')"
    if grep -q '^API_TOKEN=' "$ENV_FILE"; then
        sed -i "s|^API_TOKEN=.*|API_TOKEN=$TOKEN|" "$ENV_FILE"
    else
        printf 'API_TOKEN=%s\n' "$TOKEN" >> "$ENV_FILE"
    fi
    echo "API_TOKEN generate ho gaya (deploy/.env me save hai)."
fi

# --- 3. Check required values ---------------------------------------------
DOMAIN="$(grep '^DOMAIN=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]' || true)"
GEMINI_KEY="$(grep '^GEMINI_API_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]' || true)"

if [ -z "$DOMAIN" ] || [ -z "$GEMINI_KEY" ]; then
    echo
    echo "Pehle deploy/.env me ye 2 cheezein bharo:"
    echo "  1. DOMAIN= — apne VM ke public IP se, jaise:"
    echo "       DOMAIN=123.45.67.89.nip.io"
    echo "     (Apna public IP dekhne ke liye: curl -s ifconfig.me)"
    echo "  2. GEMINI_API_KEY= — free key aistudio.google.com se"
    echo
    echo "File kholo:  nano $ENV_FILE"
    echo "Phir ye script dobara chalao:  bash deploy/deploy.sh"
    exit 0
fi

# --- 4. Open firewall ports on the VM itself -------------------------------
# Oracle's Ubuntu images block everything except SSH in iptables by
# default — the cloud security list alone is not enough.
say "VM firewall me port 80/443 khole ja rahe hain..."
sudo iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null \
    || sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null \
    || sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
if command -v netfilter-persistent >/dev/null 2>&1; then
    sudo netfilter-persistent save 2>/dev/null || true
elif command -v iptables-save >/dev/null 2>&1; then
    sudo sh -c 'iptables-save > /etc/iptables/rules.v4' 2>/dev/null || true
fi

# --- 5. Build + start ------------------------------------------------------
say "Satyam build + start ho raha hai (pehli baar 2-5 min lag sakte hain)..."
cd "$DEPLOY_DIR"
docker compose up -d --build

# --- 6. Systemd unit (auto-start on boot) ----------------------------------
say "Systemd unit install ho raha hai (boot pe auto-start)..."
UNIT_SRC="$DEPLOY_DIR/satyam.service"
if [ "$PROJECT_DIR" != "/home/ubuntu/satyam-ai" ]; then
    sed "s|/home/ubuntu/satyam-ai|$PROJECT_DIR|g" "$UNIT_SRC" | sudo tee /etc/systemd/system/satyam.service >/dev/null
else
    sudo cp "$UNIT_SRC" /etc/systemd/system/satyam.service
fi
sudo systemctl daemon-reload
sudo systemctl enable satyam.service >/dev/null 2>&1 || true

# --- 7. Keep-alive cron (Oracle idle reclamation se bachav) -----------------
say "Keep-alive cron lagaya ja raha hai..."
CRON_LINE="*/5 * * * * docker exec satyam curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 # satyam-health"
( crontab -l 2>/dev/null | grep -v 'satyam-health' ; echo "$CRON_LINE" ) | crontab -
echo "Har 5 min me /health ping hoga (ye + regular use milke VM ko idle"
echo "reclaim hone se bachata hai — details ORACLE_GUIDE.md me)."

# --- 8. Done ----------------------------------------------------------------
echo
echo "Ho gaya! Satyam cloud pe chal raha hai."
if [ "$DOMAIN" = ":80" ]; then
    echo "  URL (HTTP only): http://$(curl -s ifconfig.me 2>/dev/null || echo '<VM-IP>')"
else
    echo "  URL: https://$DOMAIN"
    echo "  Health check: https://$DOMAIN/health"
fi
echo "  API token (deploy/.env me hai, Flutter app me daalo):"
grep '^API_TOKEN=' "$ENV_FILE" | sed 's/^API_TOKEN=/  API_TOKEN=/'
echo
echo "Logs dekhne ke liye:  cd $DEPLOY_DIR && docker compose logs -f"
echo "Restart karne ke liye: cd $DEPLOY_DIR && docker compose restart"
