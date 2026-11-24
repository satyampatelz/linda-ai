# Oracle Cloud pe Linda chalao — 24×7, ₹0 me (ORACLE_GUIDE)

> **Ye guide kya karti hai:** Linda ka backend Oracle ke **free** cloud server (VM) pe chalana, taaki wo **24×7 kaam kare — phone band ho ya laptop band ho**, tab bhi. Tum bas chat karte ho, kaam cloud pe hota rehta hai.
>
> **Kharcha: ₹0.** Oracle ka Always Free tier hamesha free hai — bas account banane ke liye **debit/credit card se verification** lagta hai (paise **nahi** katte, sirf ye check hota hai ki tum real insaan ho).
>
> **Time:** pehli baar ~30–45 min (account + VM + deploy).

---

## Step 0 — Kya chahiye (checklist)

- [ ] Ek email address (koi bhi — Gmail chalega)
- [ ] Debit ya credit card (sirf verification ke liye — **koi charge nahi**)
- [ ] Tumhara laptop + phone (is guide ke steps ke liye)
- [ ] Gemini ki free API key — [aistudio.google.com](https://aistudio.google.com) → **Get API key** (Google account se, card nahi lagta). Cloud VM me GPU nahi hai, isliye wahan brain Gemini hi chalega.

---

## Step 1 — Oracle Cloud account banao

1. Browser me kholo: [cloud.oracle.com](https://cloud.oracle.com) → **Start for free** (ya **Sign up**).
2. Email, password, naam, country (India) bharo → **Verify** (email pe code aayega).
3. **Home Region chuno: Mumbai (ap-mumbai-1)** — tumhare sabse paas hai, isliye tez chalega.
   > ⚠️ **Home Region kabhi nahi badalta** — ek baar chun liya toh wahi permanent hai. Mumbai select karna mat bhoolna.
4. Card details daalo (verification ke liye — **paise nahi katte**).
5. Account ban gaya — ab [cloud.oracle.com](https://cloud.oracle.com) pe **Sign in** karo.

---

## Step 2 — Free VM (server) banao

1. Upar left me **☰ menu → Compute → Instances** → **Create Instance**.
2. Naam do, jaise `linda-server`.
3. **Image:** **Ubuntu 24.04** chuno (Canonical Ubuntu 24.04, minimal ya normal — koi bhi chalega).
4. **Shape:** **Change Shape** → **Ampere** tab → **VM.Standard.A1.Flex** → sliders set karo:
   - **OCPUs: 2**
   - **Memory: 12 GB**
   - Neeche **"Always Free eligible"** likha hona chahiye — yahi confirm karta hai ki ye free hai.
   > ℹ️ June 2026 se Always Free Ampere limit **2 OCPU / 12 GB** hai (pehle 4/24 tha). 2/12 Linda ke liye kaafi hai.
5. **Boot volume:** default (47 GB) theek hai. (Free limit total 200 GB hai — 47 GB use karna safe hai.)
6. **SSH key:** **"Generate a key pair for me"** chuno → private key download karke sambhal ke rakho (is file se hi VM me login hoga). Ya apni khud ki public key paste karo agar pehle se hai (`ssh-keygen` se bani).
7. **Create** dabao. 1–2 min me VM **Running** ho jayegi.
8. Instance page se **Public IP address** note kar lo (jaise `123.45.67.89`) — ye aage kaam aayega.

### "Out of capacity" aaye toh? (bahut common hai)

Ampere (ARM) free VMs aksar **"Out of capacity"** dikhate hain — iska matlab region me abhi free jagah nahi hai. Ghabrao mat:

- **Dobara try karo** — raat ko ya subah jaldi (odd hours) capacity milne ke chance zyada hote hain.
- **Region badlo mat** — Always Free resources sirf tumhare home region (Mumbai) me milte hain.
- **Shape mat badlo** — AMD micro instances (1 GB RAM) Linda ke liye bahut chhote hain; A1 ka hi wait karo.
- Kuch logon ko 1–2 din lagte hain — koshish jaari rakho, ye free hai isliye demand zyada hai.

---

## Step 3 — Port 80 aur 443 kholo (cloud firewall)

Bina iske tumhara phone/server internet se connect nahi ho payega.

1. Instance page pe **Virtual Cloud Network** (VCN) ke naam pe click karo → **Security Lists** → default security list kholo.
2. **Add Ingress Rules** — 2 rules banao (har ek ke liye):
   - **Rule 1:** Source CIDR `0.0.0.0/0`, Destination Port Range `80`, Protocol TCP
   - **Rule 2:** Source CIDR `0.0.0.0/0`, Destination Port Range `443`, Protocol TCP
3. Save karo. (VM ke andar ka firewall `deploy.sh` khud khol dega.)

---

## Step 4 — Code VM pe copy karo

Laptop pe terminal (PowerShell/WSL) me, project folder se:

```powershell
# 1. Linda ka zip banao (agar pehle se nahi hai)
#    linda-ai-v0.3.zip tumhare paas pehle se hai — usi ko use karo.

# 2. Zip VM pe bhejo (PUBLIC_IP ki jagah apna IP daalo)
scp -i <tumhari-private-key.pem> linda-ai-v0.3.zip ubuntu@<PUBLIC_IP>:~/
```

Phir VM me login karo:

```powershell
ssh -i <tumhari-private-key.pem> ubuntu@<PUBLIC_IP>
```

VM ke andar:

```bash
sudo apt-get update -qq && sudo apt-get install -y -qq unzip
unzip -o linda-ai-v0.3.zip
ls linda-ai   # project folder dikhna chahiye
```

> 💡 Agar `scp`/`ssh` me key permission error aaye (Windows pe common hai), toh key file ki permission fix karo: file pe right-click → Properties → Security → sirf apne user ko access do, baaki sab hata do. Ya WSL terminal se chalao.

---

## Step 5 — Deploy karo

VM ke andar:

```bash
cd ~/linda-ai
bash deploy/deploy.sh
```

**Pehli baar** ye script Docker install karegi, `deploy/.env` banayegi, ek random **API_TOKEN** generate karegi — phir **ruk jayegi** aur bolegi ki 2 cheezein bharo. Ab `.env` edit karo:

```bash
nano deploy/.env
```

- `DOMAIN=` ki jagah likho: `DOMAIN=<PUBLIC_IP>.nip.io`
  (jaise IP `123.45.67.89` hai toh `DOMAIN=123.45.67.89.nip.io` — nip.io ek free service hai jo IP ko asli DNS naam bana deti hai, jisse free HTTPS certificate mil jata hai. Koi signup nahi, koi kharcha nahi.)
- `GEMINI_API_KEY=` ki jagah apni free Gemini key paste karo (Step 0 se).
- Save karo: `Ctrl+O`, `Enter`, `Ctrl+X`.

Phir dobara deploy karo:

```bash
bash deploy/deploy.sh
```

Ab ye build karega (pehli baar 2–5 min), server start karega, **systemd unit** install karega (VM restart hone pe Linda khud start ho jayega) aur **keep-alive cron** lagayega. Aakhir me tumhe URL + API token dikhega:

```
URL: https://123.45.67.89.nip.io
API_TOKEN=... (Flutter app me daalna hai)
```

Browser me `https://<DOMAIN>/health` kholo — `{"status": "online", ...}` dikhe toh sab theek hai. ✅

---

## Step 6 — Phone app ko cloud se jodo

1. Flutter app (linda-v0.3.apk) phone pe install karo.
2. App me **Settings** kholo:
   - **Server URL:** `https://<DOMAIN>` (jaise `https://123.45.67.89.nip.io`)
   - **API token:** deploy ke aakhir me dikha tha (ya VM pe `grep API_TOKEN ~/linda-ai/deploy/.env` se dekh lo)
3. Save karo → Chat kholo → `hi` likh ke bhejo. Agent cloud se jawab dega. 🎉

**Laptop se bhi wahi agent chalega:** laptop ke browser me `https://<DOMAIN>` kholo — wahi PWA chat UI khulega, wahi tasks dikhenge. Laptop pe task do, phone pe result dekho (aur ulta bhi) — dono ek hi agent se baat karte hain.

---

## Idle reclamation — VM band na ho, iska dhyaan rakho

Oracle ki policy: agar ek Always Free instance **7 din tak** CPU, network **aur** memory — teeno me 95th-percentile usage **20% se kam** rahe, toh Oracle use **reclaim** (delete) kar sakta hai.

Bachav:
- **deploy.sh ek keep-alive cron lagata hai** — har 5 min me server ka `/health` check hota hai, jo VM ko "zinda" rakhta hai.
- **Regular use sabse best hai** — agent se roz kaam karwao, toh VM idle hi nahi rehta.
- **Honest baat:** keep-alive ping akela guarantee nahi hai — agar VM ek hafta bilkul bina kaam ke pada rahe toh reclaim ho sakta hai. Aisa ho toh ghabrao mat: dobara VM banao (Step 2–5, ~15 min) aur `deploy.sh` dobara chalao. Apna data (`data/` + `workspace/`) backup me rakhna achha idea hai:
  ```bash
  # VM se backup download karo (laptop pe):
  scp -i <key.pem> -r ubuntu@<PUBLIC_IP>:~/linda-ai/data ./linda-backup-data
  ```

---

## Roz ke kaam (VM pe)

```bash
cd ~/linda-ai/deploy

docker compose logs -f            # live logs dekho (Ctrl+C se bahar)
docker compose restart            # server restart karo
docker compose ps                 # containers chal rahe hain ya nahi
docker compose down               # sab band karo (data safe rehta hai)
docker compose up -d              # dobara start karo
```

**Update karna hai (nayi version aaye toh):** naya zip VM pe bhejo, extract karo (purane folder ke upar — `data/` aur `workspace/` Docker volumes me hain, safe rahenge), phir `bash deploy/deploy.sh` dobara chalao.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Out of capacity` (Step 2) | Odd hours me retry karo; A1 shape ka hi wait karo (AMD micro bahut chhota hai). |
| `https://DOMAIN` nahi khul raha | (1) Step 3 ke security-list rules check karo (port 80+443). (2) VM pe `sudo iptables -L INPUT` — deploy.sh ne rules daale hone chahiye. (3) `docker compose ps` — dono containers running hone chahiye. (4) `docker compose logs caddy` — certificate error dikhe toh 2–3 min wait karo (pehla cert banne me time lagta hai). |
| App me `401` / token error | Flutter app ki Settings me token dobara check karo — VM pe `grep API_TOKEN ~/linda-ai/deploy/.env` se sahi token copy karo. |
| Agent ke jawab me error | `docker compose logs -f linda` me dekho. Common: Gemini key galat/nahi hai → `deploy/.env` me sahi key daalo, phir `docker compose up -d` (restart ke liye). |
| VM reclaim ho gaya | Step 2 se dobara VM banao — deploy.sh se 15 min me wapas chalu ho jayega. |
| Kharcha dikh raha hai? | Oracle Console → Billing → Cost Analysis — Always Free resources pe **0.00** hona chahiye. Agar kuch paid dikhe toh use turant delete karo (tumne galti se paid resource bana liya hoga). |

---

## Yaad rakhne layak baatein

- **₹0 kharcha** — sab kuch Always Free tier me hai (2 OCPU / 12 GB VM, 200 GB storage, 10 TB/month traffic).
- **Phone/laptop band ho toh bhi kaam chalta rahega** — agent cloud pe hai.
- **API token sambhal ke rakho** — jiske paas token hai, wo tumhara agent use kar sakta hai. Kisi se share mat karo.
- **Browser cloud pe headless chalta hai** — tum Chrome ko screen pe nahi dekh paoge (VM me screen hi nahi hai). Browser wale tasks phir bhi kaam karenge; screenshots `workspace/screenshots/` me save hote hain.
- **CAPTCHA/OTP** cloud pe bhi tumhari madad mangenge — agent ruk ke batayega, tum phone se solve karoge (jaise pehle discuss hua tha).
