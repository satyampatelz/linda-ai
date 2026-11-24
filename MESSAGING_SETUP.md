# WhatsApp + Instagram Auto-Reply — Setup Guide (v0.7)

Linda ab WhatsApp aur Instagram DMs ka jawab **khud** de dega — message aate hi padhega, samjhega, aur tumhari tarah casual style me reply kar dega. Tumse baar-baar nahi poochhega ki kya reply dena hai.

Ye guide **official Meta APIs** (WhatsApp Cloud API + Instagram Messaging API) ke liye hai — koi unofficial hack nahi, isliye account ban hone ka risk nahi hai.

**Control chat se hota hai — Settings me kuch nahi hai.** Token ek baar **secure box** me paste kar do (chat me hi masked input card khulta hai, normal message ki tarah nahi) — bas, phir auto-reply chalu.

---

## Pehle samajh lo (honest baatein)

1. **24-hour window:** Meta sirf usi message ka free-form reply allow karta hai jo **pichhle 24 ghante me** aaya ho. Usse purana message ho toh Linda reply **nahi** bhejega (skip karke log me likh dega) — ye Meta ka rule hai, Linda ka nahi.
2. **WhatsApp free tier:** har mahine **~1,000 free service conversations** milti hain (Meta ki pricing badal sakti hai — dashboard me check karo). Uske baad per-message charge lagta hai.
3. **Test mode vs full use:** shuru me Meta app "development mode" me hota hai — WhatsApp test number sirf 5 registered test numbers ko reply kar sakta hai, Instagram bhi sirf test users ko. Sabko reply karne ke liye **Meta app review** (permissions approve karwana) chahiye — ye free hai, par Meta ko demo dikhana padta hai. Is guide me test setup pehle hai; app review ka step aakhir me hai.
4. **Reply tumhare naam se jayega:** doston ko lagega tumne reply kiya hai — kyunki reply tumhare account se ja raha hai. Linda "main AI hoon" nahi bolega.
5. **Token kabhi normal chat message me mat likho.** Token sirf **secure box** me paste karo (chat me hi khulta hai, masked rehta hai, kabhi dikhta nahi) ya `.env` file me haath se daalo. `.env` git me nahi jata (`.gitignore` me hai).
6. **Webhook ko public URL chahiye:** Meta tumhare server ko internet se call karta hai, isliye `localhost` kaafi nahi — laptop pe test ke liye **ngrok** (free) use karo, 24×7 ke liye **Oracle cloud server** (deploy/ORACLE_GUIDE.md).

---

## Part A — WhatsApp setup

### Step 1: Meta developer account + app banao
1. [developers.facebook.com](https://developers.facebook.com) kholo, apne Facebook account se login karo, **Get Started** → developer account banao (free, card nahi lagta).
2. **My Apps → Create App** → app type **Other** → **Business** chuno → app ka naam do (jaise `Linda`) → **Create App**.

### Step 2: WhatsApp product add karo
1. App dashboard me **Add Product** → **WhatsApp** → **Set up**.
2. **WhatsApp → API Setup** page khulegi. Yahan tumhe milega:
   - **Test phone number** (Meta ka free test number — isse shuru karo)
   - **Phone number ID** — isko note karo (secure box me daalna hai)
   - **Temporary access token** (24 ghante valid — test ke liye kaafi hai)

### Step 3: Test recipient add karo
API Setup page pe **Step 1 → Add phone number** me apna (ya dost ka) WhatsApp number daalo — Meta us number pe ek code bhejega, verify karo. Test mode me sirf in numbers ko reply ja sakta hai (max 5).

### Step 4: Permanent token banao (24×7 ke liye)
Temporary token 24 ghante me expire ho jata hai. Permanent token:
1. [business.facebook.com/settings](https://business.facebook.com/settings) → **Users → System Users** → **Add** (Admin role) → naam do (jaise `linda-bot`).
2. System user pe **Add Assets** → **Apps** → apna app select karo → **Full control**.
3. **Generate New Token** → app chuno → permissions tick karo: `whatsapp_business_messaging`, `whatsapp_business_management` → token copy karo.
4. Ye token **kabhi expire nahi hota** — isko secure box me daalna hai (Part C dekho).

### Step 5: Webhook lagao
1. App dashboard → **WhatsApp → Configuration** → **Webhook** section → **Edit**.
2. **Callback URL** daalo (Part D dekho):
   - Laptop test: `https://TUMHARA-NGROK-URL/webhook/whatsapp`
   - Cloud: `https://TUMHARA-DOMAIN/webhook/whatsapp`
3. **Verify token** — ek secret string khud banao (jaise `linda-verify-12345`) aur yahan daalo — **wahi string secure box me bhi daalni hai** (dono same honi chahiye, warna Meta verify nahi karega).
4. **Verify and save** dabao — Meta tumhare server ko `GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...` call karega; Linda challenge wapas bhej dega aur verify ho jayega. (Server chalu hona chahiye is waqt! Webhook verify karne se pehle verify token secure box me daal do — Part C.)
5. Phir **Webhook fields** me **Subscribe** karo: `messages` field zaroor tick karo.

### Step 6: App Secret (recommended)
App dashboard → **Settings → Basic** → **App Secret** → **Show** → copy karke secure box me daalo. Isse Linda har webhook ki signature check karta hai (koi fake request nahi bhej payega). Na ho toh bhi kaam chalega, par kam safe hai.

---

## Part B — Instagram setup

### Step 1: Instagram ko Professional banao + Page link karo
1. Instagram app → apni profile → **Settings → Account type → Switch to professional account** → **Business** ya **Creator** chuno.
2. Ek **Facebook Page** chahiye (na ho toh facebook.com/pages/create se free me banao).
3. Instagram app → **Settings → Accounts Centre → Pages → Add** apna Page link karo. (Ya Facebook Page → Settings → Linked Accounts → Instagram.)

### Step 2: Meta app me Instagram product add karo
1. Wahi Meta app (Part A wala) → **Add Product** → **Instagram** → **Set up**.
2. **Instagram → API setup with Facebook login** me apna Page add karo.
3. Permissions chahiye: `instagram_business_manage_messages` (purana naam: `instagram_manage_messages`) aur `pages_messaging`. Test mode me ye permissions app ke admin/tester ko mil jati hain.

### Step 3: Page access token banao
1. [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer) (Graph API Explorer) → apna app chuno → **Generate Access Token** (User token, permissions: `pages_messaging`, `instagram_business_manage_messages`, `pages_show_list`).
2. Phir **GET /me/accounts** chalao — linked Page ka **Page access token** milega. Isko lamba (long-lived, ~60 din) karne ke liye token debugger se extend karo, ya System User wala tareeqa (Part A Step 4) use karo — System User token best hai 24×7 ke liye.
3. Page token ko secure box me daalna hai (Part C), aur Page ka ID bhi (Page ID `/me/accounts` response me `id` field hai, ya Page → About → Page ID).

### Step 4: Instagram webhook lagao
1. App dashboard → **Webhooks** → **Instagram** object ke liye **Edit Subscription** (na dikhe toh **Add Subscription**).
2. **Callback URL**: `https://TUMHARA-URL/webhook/instagram` (Part D dekho).
3. **Verify token** — ek secret string banao, wahi secure box me daalo.
4. **Verify and save** → phir subscribe karo: **`messages`** field (aur `messaging_postbacks` optional).
5. App Secret wahi hai jo Part A Step 6 me tha — secure box me daalo (dono ek hi app ke hain).

---

## Part C — Linda me chalu karo (chat se + secure box)

Settings me messaging ka koi option nahi hai — sab chat se hota hai:

1. Linda se chat me bolo:
   - **"ab se Instagram ke messages dekhna"** (Instagram on)
   - **"ab se WhatsApp ke messages dekhna"** (WhatsApp on)
   - English me bhi chalega: "start replying to my Instagram messages"
2. Token set nahi hai toh Linda ek baar batayega aur **chat me hi ek secure box khol dega** — masked input card, normal message ki tarah nahi. Usme ye paste karo:

   | Field | Kya daalo |
   |---|---|
   | WhatsApp access token | Part A Step 4 wala permanent token |
   | WhatsApp phone number ID | Part A Step 2 wala ID |
   | WhatsApp verify token | Part A Step 5 wali secret string |
   | WhatsApp app secret | Part A Step 6 wala secret (optional) |
   | Instagram access token | Part B Step 3 wala Page token |
   | Facebook Page ID | Part B Step 3 wala Page ID |
   | Instagram verify token | Part B Step 4 wali secret string |
   | Instagram app secret | Part A Step 6 wala secret (optional, same app) |

3. **Save** dabao — token `.env` me safe save ho jayega (kabhi chat me dikhega nahi, kabhi log me nahi aayega) aur **auto-reply apne aap chalu ho jayega**. Dobara kuch bolne ki zaroorat nahi.
4. **Status** panel me `WhatsApp auto-reply` aur `Instagram auto-reply` checks se verify karo — dono `ok` hone chahiye.

**Band karna ho toh** chat me bolo: **"WhatsApp band kar do"** ya **"Instagram ka reply band kar do"**. Dobara chalu karne ke liye phir se "ab se ... dekhna" bolo — token dobara daalne ki zaroorat nahi (save rehta hai).

**Status poochhna ho toh** bolo: **"WhatsApp reply on hai?"** — Linda bata dega.

### Alternative: .env me haath se (advanced users)
Secure box use nahi karna ho toh `.env` file me seedha daal do (`.env.example` me keys likhi hain: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `INSTAGRAM_TOKEN`, `INSTAGRAM_PAGE_ID`, `INSTAGRAM_VERIFY_TOKEN`, `INSTAGRAM_APP_SECRET`). Phir server restart karo aur chat me bolo "ab se ... dekhna". Cloud server pe `deploy/.env` me daalo aur `docker compose restart` karo.

---

## Part D — Webhook URL: laptop vs cloud

### Laptop pe test (ngrok, free)
Meta ko public HTTPS URL chahiye — `localhost` nahi chalega.
1. [ngrok.com](https://ngrok.com) se ngrok install karo (free account banao, authtoken set karo).
2. Linda server chalao (`run.bat`), phir alag terminal me:
   ```
   ngrok http 8000
   ```
3. ngrok jo `https://xxxx.ngrok-free.app` URL de, usko webhook callback me use karo: `https://xxxx.ngrok-free.app/webhook/whatsapp` aur `.../webhook/instagram`.
4. **Note:** free ngrok URL har restart pe badal jata hai — badle toh Meta dashboard me webhook URL dobara update karo. Laptop band ho toh auto-reply bhi band.

### 24×7 (Oracle cloud server — recommended)
Agar cloud deploy ho gaya hai (deploy/ORACLE_GUIDE.md), toh webhook URL stable hai:
- `https://TUMHARA-DOMAIN/webhook/whatsapp`
- `https://TUMHARA-DOMAIN/webhook/instagram`

Cloud server pe secure box waise hi kaam karta hai (app cloud server se connected ho toh) — token cloud server ke `.env` me save hoga. Laptop/phone band ho tab bhi auto-reply chalta rahega.

---

## Part E — Test karo

1. Apne dusre number (ya dost ke number) se **test WhatsApp number** ko message bhejo (test mode me sirf registered numbers se).
2. Linda ko ~5–15 second do — reply tumhare brain se generate hoke wapas aayega, tumhare style me, usi language me jis me message aaya tha.
3. Instagram ke liye: kisi dusre Instagram account se apne Business account ko DM bhejo.
4. Server log me dikhega: `Replied to whatsapp ...` ya skip hone pe reason (`outside_24h_window`, `duplicate`, `rate_limited`).

---

## App review (sabko reply karne ke liye)

Test mode sirf registered test users tak limited hai. Public use (koi bhi tumhe message kare, Linda reply de) ke liye:
1. App dashboard → **App Review → Permissions and Features** → `whatsapp_business_messaging` aur `instagram_business_manage_messages` ke liye **Request** karo.
2. Meta ko batana padta hai app kya karta hai (short video/demo + description). Ye free hai, approval me kuch din lag sakte hain.
3. Business verification bhi maang sakte hain (business documents) — personal use ke liye test mode hi kaafi hai shuru me.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Webhook verify nahi ho raha (Meta error) | Server chalu hai? Callback URL sahi hai? Verify token Meta dashboard aur secure box me **same** hai? (Copy-paste me space na aaye.) Verify token pehle secure box me daalo, phir Meta me Verify dabao. |
| Message aaya par reply nahi aaya | Status panel check karo (token/ID set hain? auto-reply ON hai — chat me "WhatsApp reply on hai?" poochho). Server log me reason dekho: `outside_24h_window` (24 ghante purana message), `platform_off_or_unconfigured`, `brain_error` (Ollama/Gemini down?), `send_failed` (token expire? Meta error log me detail hai). |
| Secure box nahi khul raha | Chat me dobara bolo "ab se Instagram ke messages dekhna" — token missing hoga toh box khul jayega. Agar token pehle se save hai toh box nahi khulega (zaroorat hi nahi). |
| Token expire ho gaya | Temporary token 24 ghante ka hota hai — Part A Step 4 wala permanent token use karo. Page token ~60 din ka hota hai — System User token use karo ya renew karo. Naya token aaye toh chat me "ab se ... dekhna" bolo — secure box dobara khul jayega. |
| Reply galat language me aaya | Brain usi language me reply karta hai jis me message aaya tha. Agar message me mix language thi toh brain kabhi-kabhi guess galat kar sakta hai — ye model ki limit hai, setting ki nahi. |
| Ek message ka do reply aa gaya | Nahi aana chahiye — dedupe message id se hota hai. Agar ho toh server log bhejo (bug report). |
| Webhook pe bahut saare event aa rahe hain | Normal hai — Meta status updates (delivered/read) bhi bhejta hai; Linda unhe ignore karta hai, sirf text messages pe reply karta hai. |
| Group message ka reply? | WhatsApp Cloud API group messages deliver hi nahi karta, aur Instagram Messaging API me group messaging supported hi nahi hai — sirf 1:1 DMs pe reply jata hai. |
