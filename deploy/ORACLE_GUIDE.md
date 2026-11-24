# Run Linda on Oracle Cloud — 24×7, for ₹0 (ORACLE_GUIDE)

> **What this guide does:** Run Linda's backend on Oracle's **free** cloud server (VM), so it **works 24×7 — even when your phone or laptop is off**. You just chat; the work keeps happening in the cloud.
>
> **Cost: ₹0.** Oracle's Always Free tier is free forever — creating an account only needs **debit/credit card verification** (no money is charged; it just checks that you are a real person).
>
> **Time:** first time ~30–45 min (account + VM + deploy).

---

## Step 0 — What you need (checklist)

- [ ] An email address (any — Gmail works)
- [ ] Debit or credit card (only for verification — **no charge**)
- [ ] Your laptop + phone (for the steps in this guide)
- [ ] A free Gemini API key — [aistudio.google.com](https://aistudio.google.com) → **Get API key** (with a Google account, no card needed). The cloud VM has no GPU, so the brain there runs on Gemini.

---

## Step 1 — Create an Oracle Cloud account

1. Open in your browser: [cloud.oracle.com](https://cloud.oracle.com) → **Start for free** (or **Sign up**).
2. Fill in email, password, name, country (India) → **Verify** (a code will arrive by email).
3. **Choose Home Region: Mumbai (ap-mumbai-1)** — it is closest to you, so it will be fastest.
   > ⚠️ **Home Region never changes** — once chosen, it is permanent. Don't forget to select Mumbai.
4. Enter card details (for verification — **no money is charged**).
5. Account created — now **Sign in** at [cloud.oracle.com](https://cloud.oracle.com).

---

## Step 2 — Create a free VM (server)

1. Top-left **☰ menu → Compute → Instances** → **Create Instance**.
2. Give it a name, like `linda-server`.
3. **Image:** choose **Ubuntu 24.04** (Canonical Ubuntu 24.04, minimal or normal — either works).
4. **Shape:** **Change Shape** → **Ampere** tab → **VM.Standard.A1.Flex** → set the sliders:
   - **OCPUs: 2**
   - **Memory: 12 GB**
   - It should say **"Always Free eligible"** below — that confirms it is free.
   > ℹ️ Since June 2026 the Always Free Ampere limit is **2 OCPU / 12 GB** (earlier it was 4/24). 2/12 is enough for Linda.
5. **Boot volume:** the default (47 GB) is fine. (The free limit is 200 GB total — using 47 GB is safe.)
6. **SSH key:** choose **"Generate a key pair for me"** → download the private key and keep it safe (this file is how you log in to the VM). Or paste your own public key if you already have one (made with `ssh-keygen`).
7. Press **Create**. The VM will be **Running** in 1–2 min.
8. Note the **Public IP address** from the instance page (e.g. `123.45.67.89`) — you will need it later.

### "Out of capacity"? (very common)

Ampere (ARM) free VMs often show **"Out of capacity"** — it means there is no free space in the region right now. Don't worry:

- **Try again** — at night or early morning (odd hours) the chances of getting capacity are higher.
- **Don't change region** — Always Free resources are only available in your home region (Mumbai).
- **Don't change shape** — AMD micro instances (1 GB RAM) are too small for Linda; wait for A1.
- Some people take 1–2 days — keep trying; demand is high because it is free.

---

## Step 3 — Open ports 80 and 443 (cloud firewall)

Without this, your phone/server won't be able to connect from the internet.

1. On the instance page, click the **Virtual Cloud Network** (VCN) name → **Security Lists** → open the default security list.
2. **Add Ingress Rules** — create 2 rules (for each one):
   - **Rule 1:** Source CIDR `0.0.0.0/0`, Destination Port Range `80`, Protocol TCP
   - **Rule 2:** Source CIDR `0.0.0.0/0`, Destination Port Range `443`, Protocol TCP
3. Save. (deploy.sh will open the firewall inside the VM itself.)

---

## Step 4 — Copy the code to the VM

On the laptop, in a terminal (PowerShell/WSL), from the project folder:

```powershell
# 1. Make Linda's zip (if you don't have one already)
#    You already have linda-ai-v0.3.zip — use that one.

# 2. Send the zip to the VM (replace PUBLIC_IP with your IP)
scp -i <your-private-key.pem> linda-ai-v0.3.zip ubuntu@<PUBLIC_IP>:~/
```

Then log in to the VM:

```powershell
ssh -i <your-private-key.pem> ubuntu@<PUBLIC_IP>
```

Inside the VM:

```bash
sudo apt-get update -qq && sudo apt-get install -y -qq unzip
unzip -o linda-ai-v0.3.zip
ls linda-ai   # the project folder should show up
```

> 💡 If you get a key permission error with `scp`/`ssh` (common on Windows), fix the key file's permissions: right-click the file → Properties → Security → give access only to your own user, remove everyone else. Or run it from a WSL terminal.

---

## Step 5 — Deploy

Inside the VM:

```bash
cd ~/linda-ai
bash deploy/deploy.sh
```

**The first time**, this script will install Docker, create `deploy/.env`, generate a random **API_TOKEN** — then **stop** and ask you to fill in 2 things. Now edit `.env`:

```bash
nano deploy/.env
```

- In place of `DOMAIN=`, write: `DOMAIN=<PUBLIC_IP>.nip.io`
  (for example, if the IP is `123.45.67.89`, then `DOMAIN=123.45.67.89.nip.io` — nip.io is a free service that turns an IP into a real DNS name, which gets you a free HTTPS certificate. No signup, no cost.)
- Paste your free Gemini key in place of `GEMINI_API_KEY=` (from Step 0).
- Save: `Ctrl+O`, `Enter`, `Ctrl+X`.

Then deploy again:

```bash
bash deploy/deploy.sh
```

Now it will build (2–5 min the first time), start the server, install a **systemd unit** (Linda starts by itself when the VM restarts) and set up a **keep-alive cron**. At the end you will see the URL + API token:

```
URL: https://123.45.67.89.nip.io
API_TOKEN=... (enter it in the Flutter app)
```

Open `https://<DOMAIN>/health` in your browser — if you see `{"status": "online", ...}`, everything is fine. ✅

---

## Step 6 — Connect the phone app to the cloud

1. Install the Flutter app (linda-v0.3.apk) on your phone.
2. Open **Settings** in the app:
   - **Server URL:** `https://<DOMAIN>` (e.g. `https://123.45.67.89.nip.io`)
   - **API token:** shown at the end of the deploy (or check it on the VM with `grep API_TOKEN ~/linda-ai/deploy/.env`)
3. Save → open Chat → send `hi`. The agent will answer from the cloud. 🎉

**The same agent also runs from your laptop:** open `https://<DOMAIN>` in your laptop's browser — the same PWA chat UI will open, showing the same tasks. Give a task on the laptop, see the result on the phone (and the other way round) — both talk to the same agent.

---

## Idle reclamation — keep the VM from being shut down

Oracle's policy: if an Always Free instance stays below **20%** usage in CPU, network **and** memory — all three, at the 95th percentile — for **7 days**, Oracle can **reclaim** (delete) it.

How to avoid it:
- **deploy.sh sets up a keep-alive cron** — the server's `/health` is checked every 5 min, which keeps the VM "alive".
- **Regular use is the best protection** — get the agent to do work every day, and the VM never stays idle.
- **Honest note:** a keep-alive ping alone is no guarantee — if the VM sits completely unused for a week, it can still be reclaimed. If that happens, don't worry: create the VM again (Steps 2–5, ~15 min) and run `deploy.sh` again. It is a good idea to keep a backup of your data (`data/` + `workspace/`):
  ```bash
  # Download a backup from the VM (on the laptop):
  scp -i <key.pem> -r ubuntu@<PUBLIC_IP>:~/linda-ai/data ./linda-backup-data
  ```

---

## Daily tasks (on the VM)

```bash
cd ~/linda-ai/deploy

docker compose logs -f            # live logs (Ctrl+C to exit)
docker compose restart            # restart the server
docker compose ps                 # check whether the containers are running
docker compose down               # stop everything (data stays safe)
docker compose up -d              # start again
```

**To update (when a new version comes out):** send the new zip to the VM, extract it (over the old folder — `data/` and `workspace/` are Docker volumes, so they stay safe), then run `bash deploy/deploy.sh` again.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Out of capacity` (Step 2) | Retry at odd hours; wait for the A1 shape (AMD micro is too small). |
| `https://DOMAIN` won't open | (1) Check the Step 3 security-list rules (ports 80+443). (2) On the VM, `sudo iptables -L INPUT` — deploy.sh should have added the rules. (3) `docker compose ps` — both containers should be running. (4) `docker compose logs caddy` — if you see a certificate error, wait 2–3 min (the first certificate takes time to be created). |
| App shows `401` / token error | Check the token again in the Flutter app's Settings — copy the correct token from the VM with `grep API_TOKEN ~/linda-ai/deploy/.env`. |
| Error in the agent's reply | Look in `docker compose logs -f linda`. Common cause: Gemini key wrong or missing → put the correct key in `deploy/.env`, then `docker compose up -d` (to restart). |
| VM was reclaimed | Create the VM again from Step 2 — deploy.sh will get it running again in 15 min. |
| Seeing a charge? | Oracle Console → Billing → Cost Analysis — Always Free resources should show **0.00**. If something paid shows up, delete it at once (you probably created a paid resource by mistake). |

---

## Things worth remembering

- **₹0 cost** — everything is in the Always Free tier (2 OCPU / 12 GB VM, 200 GB storage, 10 TB/month traffic).
- **Work keeps going even with your phone/laptop off** — the agent is in the cloud.
- **Keep your API token safe** — anyone who has the token can use your agent. Don't share it with anyone.
- **The browser runs headless in the cloud** — you won't see Chrome on a screen (the VM has no screen). Browser tasks still work; screenshots are saved in `workspace/screenshots/`.
- **CAPTCHA/OTP** will still ask for your help in the cloud — the agent will pause and tell you, and you solve it from your phone (as discussed before).
