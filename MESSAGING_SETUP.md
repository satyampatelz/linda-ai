# WhatsApp + Instagram Auto-Reply — Setup Guide (v0.7)

Linda now answers your WhatsApp and Instagram DMs **itself** — as soon as a message arrives, it reads it, understands it, and replies in your casual style. It won't keep asking you what to reply.

This guide is for the **official Meta APIs** (WhatsApp Cloud API + Instagram Messaging API) — no unofficial hacks, so there is no risk of your account being banned.

**Control happens from chat — there is nothing in Settings.** Paste the token once in the **secure box** (a masked input card that opens in chat, not a normal message) — that's it, auto-reply is on.

---

## Read this first (the honest facts)

1. **24-hour window:** Meta only allows a free-form reply to a message that arrived in the **last 24 hours**. If the message is older than that, Linda will **not** send a reply (it skips it and writes it in the log) — that's Meta's rule, not Linda's.
2. **WhatsApp free tier:** you get **~1,000 free service conversations** per month (Meta's pricing can change — check the dashboard). After that, there is a per-message charge.
3. **Test mode vs full use:** at first, the Meta app is in "development mode" — the WhatsApp test number can only reply to 5 registered test numbers, and Instagram only to test users. To reply to everyone you need **Meta app review** (getting the permissions approved) — this is free, but you have to show Meta a demo. This guide covers the test setup first; the app review step is at the end.
4. **Replies go out in your name:** your friends will think you replied — because the reply is sent from your account. Linda will not say "I am an AI".
5. **Never type a token in a normal chat message.** Paste tokens only in the **secure box** (it opens in chat, stays masked, is never shown) or put them by hand in the `.env` file. `.env` never goes into git (it's in `.gitignore`).
6. **The webhook needs a public URL:** Meta calls your server from the internet, so `localhost` is not enough — use **ngrok** (free) to test on your laptop, and the **Oracle cloud server** (deploy/ORACLE_GUIDE.md) for 24×7.

---

## Part A — WhatsApp setup

### Step 1: Create a Meta developer account + app
1. Open [developers.facebook.com](https://developers.facebook.com), log in with your Facebook account, **Get Started** → create a developer account (free, no card needed).
2. **My Apps → Create App** → app type **Other** → choose **Business** → give the app a name (e.g. `Linda`) → **Create App**.

### Step 2: Add the WhatsApp product
1. In the app dashboard, **Add Product** → **WhatsApp** → **Set up**.
2. The **WhatsApp → API Setup** page will open. Here you get:
   - **Test phone number** (Meta's free test number — start with this)
   - **Phone number ID** — note this down (it goes in the secure box)
   - **Temporary access token** (valid for 24 hours — enough for testing)

### Step 3: Add a test recipient
On the API Setup page, under **Step 1 → Add phone number**, enter your own (or a friend's) WhatsApp number — Meta will send a code to that number, verify it. In test mode, replies can only go to these numbers (max 5).

### Step 4: Create a permanent token (for 24×7)
The temporary token expires in 24 hours. For a permanent token:
1. [business.facebook.com/settings](https://business.facebook.com/settings) → **Users → System Users** → **Add** (Admin role) → give it a name (e.g. `linda-bot`).
2. On the system user, **Add Assets** → **Apps** → select your app → **Full control**.
3. **Generate New Token** → choose the app → tick the permissions: `whatsapp_business_messaging`, `whatsapp_business_management` → copy the token.
4. This token **never expires** — it goes in the secure box (see Part C).

### Step 5: Set up the webhook
1. App dashboard → **WhatsApp → Configuration** → **Webhook** section → **Edit**.
2. Enter the **Callback URL** (see Part D):
   - Laptop test: `https://YOUR-NGROK-URL/webhook/whatsapp`
   - Cloud: `https://YOUR-DOMAIN/webhook/whatsapp`
3. **Verify token** — make up a secret string yourself (e.g. `linda-verify-12345`) and enter it here — **the same string must also go in the secure box** (both must be the same, otherwise Meta will not verify it).
4. Press **Verify and save** — Meta will call your server at `GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...`; Linda will send the challenge back and verification will succeed. (The server must be running at this time! Put the verify token in the secure box before verifying the webhook — Part C.)
5. Then, under **Webhook fields**, **Subscribe** to: the `messages` field is required.

### Step 6: App Secret (recommended)
App dashboard → **Settings → Basic** → **App Secret** → **Show** → copy it and put it in the secure box. With this, Linda checks the signature of every webhook (nobody can send fake requests). It works without it too, but is less safe.

---

## Part B — Instagram setup

### Step 1: Make Instagram Professional + link a Page
1. Instagram app → your profile → **Settings → Account type → Switch to professional account** → choose **Business** or **Creator**.
2. You need a **Facebook Page** (if you don't have one, create one for free at facebook.com/pages/create).
3. Instagram app → **Settings → Accounts Centre → Pages → Add** to link your Page. (Or Facebook Page → Settings → Linked Accounts → Instagram.)

### Step 2: Add the Instagram product to the Meta app
1. The same Meta app (the one from Part A) → **Add Product** → **Instagram** → **Set up**.
2. Under **Instagram → API setup with Facebook login**, add your Page.
3. Permissions needed: `instagram_business_manage_messages` (old name: `instagram_manage_messages`) and `pages_messaging`. In test mode, these permissions are available to the app's admin/tester.

### Step 3: Create a Page access token
1. [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer) (Graph API Explorer) → choose your app → **Generate Access Token** (User token, permissions: `pages_messaging`, `instagram_business_manage_messages`, `pages_show_list`).
2. Then run **GET /me/accounts** — you will get the linked Page's **Page access token**. To make it long-lived (~60 days), extend it via the token debugger, or use the System User method (Part A Step 4) — the System User token is best for 24×7.
3. The Page token goes in the secure box (Part C), and so does the Page ID (the Page ID is the `id` field in the `/me/accounts` response, or Page → About → Page ID).

### Step 4: Set up the Instagram webhook
1. App dashboard → **Webhooks** → for the **Instagram** object, **Edit Subscription** (if it's not there, **Add Subscription**).
2. **Callback URL**: `https://YOUR-URL/webhook/instagram` (see Part D).
3. **Verify token** — make up a secret string and put the same one in the secure box.
4. **Verify and save** → then subscribe to the **`messages`** field (and `messaging_postbacks`, optional).
5. The App Secret is the same one from Part A Step 6 — put it in the secure box (both are from the same app).

---

## Part C — Turn it on in Linda (from chat + secure box)

There is no messaging option in Settings — everything happens from chat:

1. Tell Linda in chat:
   - **"start watching my Instagram messages"** (Instagram on)
   - **"start watching my WhatsApp messages"** (WhatsApp on)
   - You can also say "start replying to my Instagram messages".
   - Hinglish/Hindi commands work too — Linda understands both.
2. If the token is not set, Linda will tell you once and **open a secure box right in chat** — a masked input card, not a normal message. Paste these into it:

   | Field | What to put in |
   |---|---|
   | WhatsApp access token | The permanent token from Part A Step 4 |
   | WhatsApp phone number ID | The ID from Part A Step 2 |
   | WhatsApp verify token | The secret string from Part A Step 5 |
   | WhatsApp app secret | The secret from Part A Step 6 (optional) |
   | Instagram access token | The Page token from Part B Step 3 |
   | Facebook Page ID | The Page ID from Part B Step 3 |
   | Instagram verify token | The secret string from Part B Step 4 |
   | Instagram app secret | The secret from Part A Step 6 (optional, same app) |

3. Press **Save** — the token will be saved safely in `.env` (it will never show in chat, never appear in a log) and **auto-reply will turn on by itself**. You don't need to say anything again.
4. Verify in the **Status** panel with the `WhatsApp auto-reply` and `Instagram auto-reply` checks — both should be `ok`.

**To turn it off**, say in chat: **"stop replying on WhatsApp"** or **"stop replying on Instagram"**. To turn it on again, say "start watching my ..." again — you don't need to enter the token again (it stays saved).

**To check the status**, say: **"Is WhatsApp reply on?"** — Linda will tell you.

### Alternative: by hand in .env (advanced users)
If you don't want to use the secure box, put the tokens directly in the `.env` file (the keys are listed in `.env.example`: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `INSTAGRAM_TOKEN`, `INSTAGRAM_PAGE_ID`, `INSTAGRAM_VERIFY_TOKEN`, `INSTAGRAM_APP_SECRET`). Then restart the server and say in chat "start watching my ...". On the cloud server, put them in `deploy/.env` and run `docker compose restart`.

---

## Part D — Webhook URL: laptop vs cloud

### Testing on a laptop (ngrok, free)
Meta needs a public HTTPS URL — `localhost` will not work.
1. Install ngrok from [ngrok.com](https://ngrok.com) (create a free account, set the authtoken).
2. Run the Linda server (`run.bat`), then in a separate terminal:
   ```
   ngrok http 8000
   ```
3. Use the `https://xxxx.ngrok-free.app` URL ngrok gives you as the webhook callback: `https://xxxx.ngrok-free.app/webhook/whatsapp` and `.../webhook/instagram`.
4. **Note:** the free ngrok URL changes on every restart — if it changes, update the webhook URL in the Meta dashboard again. If the laptop is off, auto-reply is off too.

### 24×7 (Oracle cloud server — recommended)
If the cloud deploy is done (deploy/ORACLE_GUIDE.md), the webhook URL is stable:
- `https://YOUR-DOMAIN/webhook/whatsapp`
- `https://YOUR-DOMAIN/webhook/instagram`

On the cloud server, the secure box works the same way (when the app is connected to the cloud server) — the token will be saved in the cloud server's `.env`. Auto-reply keeps running even when the laptop/phone is off.

---

## Part E — Test it

1. From your second number (or a friend's number), send a message to the **test WhatsApp number** (in test mode, only from registered numbers).
2. Give Linda ~5–15 seconds — the reply will be generated by your brain and come back in your style, in the same language the message came in.
3. For Instagram: send a DM to your Business account from another Instagram account.
4. The server log will show: `Replied to whatsapp ...`, or if skipped, the reason (`outside_24h_window`, `duplicate`, `rate_limited`).

---

## App review (to reply to everyone)

Test mode is limited to registered test users. For public use (anyone messages you, Linda replies):
1. App dashboard → **App Review → Permissions and Features** → **Request** `whatsapp_business_messaging` and `instagram_business_manage_messages`.
2. You have to tell Meta what the app does (a short video/demo + description). This is free; approval can take a few days.
3. They may also ask for business verification (business documents) — for personal use, test mode is enough to start with.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Webhook won't verify (Meta error) | Is the server running? Is the callback URL correct? Is the verify token the **same** in the Meta dashboard and the secure box? (Make sure no space crept in during copy-paste.) Put the verify token in the secure box first, then press Verify in Meta. |
| Message arrived but no reply came | Check the Status panel (are the token/ID set? Is auto-reply ON — ask in chat "Is WhatsApp reply on?"). Check the reason in the server log: `outside_24h_window` (message older than 24 hours), `platform_off_or_unconfigured`, `brain_error` (Ollama/Gemini down?), `send_failed` (token expired? The Meta error in the log has the detail). |
| Secure box won't open | Say in chat again "start watching my Instagram messages" — if the token is missing, the box will open. If a token is already saved, the box won't open (there's no need). |
| Token expired | The temporary token lasts 24 hours — use the permanent token from Part A Step 4. A Page token lasts ~60 days — use a System User token or renew it. When you have a new token, say in chat "start watching my ..." — the secure box will open again. |
| Reply came in the wrong language | The brain replies in the same language the message came in. If the message was in mixed language, the brain can sometimes guess wrong — that's a model limit, not a setting. |
| One message got two replies | It shouldn't happen — dedupe is done by message id. If it does, send the server log (bug report). |
| Lots of events arriving at the webhook | Normal — Meta also sends status updates (delivered/read); Linda ignores them and only replies to text messages. |
| Reply to a group message? | The WhatsApp Cloud API doesn't deliver group messages at all, and group messaging is not supported in the Instagram Messaging API — replies only go to 1:1 DMs. |
