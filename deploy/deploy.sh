#!/usr/bin/env bash
# Linda cloud deploy — run ONCE on the Oracle VM (Ubuntu 24.04).
#
# Usage (from the project root on the VM, e.g. ~/linda-ai):
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
    say "Installing Docker..."
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io docker-compose-v2
    sudo usermod -aG docker "$USER" || true
    echo "NOTE: Docker was just installed for the first time — before running"
    echo "this script again, log out and log back in once (so the docker"
    echo "group takes effect), or run it with 'sudo' for now."
else
    echo "Docker is already installed: $(docker --version)"
fi

# --- 2. .env --------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
    say "Creating deploy/.env..."
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
    echo "API_TOKEN generated (saved in deploy/.env)."
fi

# --- 3. Check required values ---------------------------------------------
DOMAIN="$(grep '^DOMAIN=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]' || true)"
GEMINI_KEY="$(grep '^GEMINI_API_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]' || true)"

if [ -z "$DOMAIN" ] || [ -z "$GEMINI_KEY" ]; then
    echo
    echo "First, fill in these 2 things in deploy/.env:"
    echo "  1. DOMAIN= — from your VM's public IP, e.g.:"
    echo "       DOMAIN=123.45.67.89.nip.io"
    echo "     (To see your public IP: curl -s ifconfig.me)"
    echo "  2. GEMINI_API_KEY= — free key from aistudio.google.com"
    echo
    echo "Open the file:  nano $ENV_FILE"
    echo "Then run this script again:  bash deploy/deploy.sh"
    exit 0
fi

# --- 4. Open firewall ports on the VM itself -------------------------------
# Oracle's Ubuntu images block everything except SSH in iptables by
# default — the cloud security list alone is not enough.
say "Opening ports 80/443 in the VM firewall..."
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
say "Building + starting Linda (first time can take 2-5 min)..."
cd "$DEPLOY_DIR"
docker compose up -d --build

# --- 6. Systemd unit (auto-start on boot) ----------------------------------
say "Installing the systemd unit (auto-start on boot)..."
UNIT_SRC="$DEPLOY_DIR/linda.service"
if [ "$PROJECT_DIR" != "/home/ubuntu/linda-ai" ]; then
    sed "s|/home/ubuntu/linda-ai|$PROJECT_DIR|g" "$UNIT_SRC" | sudo tee /etc/systemd/system/linda.service >/dev/null
else
    sudo cp "$UNIT_SRC" /etc/systemd/system/linda.service
fi
sudo systemctl daemon-reload
sudo systemctl enable linda.service >/dev/null 2>&1 || true

# --- 7. Keep-alive cron (guards against Oracle idle reclamation) -----------------
say "Setting up the keep-alive cron..."
CRON_LINE="*/5 * * * * docker exec linda curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 # linda-health"
( crontab -l 2>/dev/null | grep -v 'linda-health' ; echo "$CRON_LINE" ) | crontab -
echo "/health will be pinged every 5 min (together with regular use, this"
echo "keeps the VM from being reclaimed as idle — details in ORACLE_GUIDE.md)."

# --- 8. Done ----------------------------------------------------------------
echo
echo "Done! Linda is running in the cloud."
if [ "$DOMAIN" = ":80" ]; then
    echo "  URL (HTTP only): http://$(curl -s ifconfig.me 2>/dev/null || echo '<VM-IP>')"
else
    echo "  URL: https://$DOMAIN"
    echo "  Health check: https://$DOMAIN/health"
fi
echo "  API token (in deploy/.env — enter it in the Flutter app):"
grep '^API_TOKEN=' "$ENV_FILE" | sed 's/^API_TOKEN=/  API_TOKEN=/'
echo
echo "To see the logs:  cd $DEPLOY_DIR && docker compose logs -f"
echo "To restart: cd $DEPLOY_DIR && docker compose restart"
