# AETHER → Render.com Setup (step-by-step)

**Repo:** https://github.com/cyborgambitions/AETHER  
**Branch to deploy:** `v1-carnival-release`  
**App code lives in:** `backend/`

---

## Before you start (2 minutes)

1. **Render account** — https://dashboard.render.com/register (free, GitHub login recommended)
2. **xAI API key** (optional but recommended for Hosted Pro) — https://console.x.ai  
   Users can also paste their own key in the app UI without a server key.
3. GitHub already has the code on `v1-carnival-release` — nothing else to push.

---

## Path A — Blueprint (recommended)

### 1. Create Blueprint
1. Open: https://dashboard.render.com/blueprints
2. Click **New Blueprint Instance**
3. Connect GitHub if needed → select **`cyborgambitions/AETHER`**
4. **Branch:** `v1-carnival-release` (not `main`)
5. Render should detect root `render.yaml`

### 2. Fill secrets when prompted

| Variable | Required? | What to put |
|----------|-----------|-------------|
| `XAI_API_KEY` | Recommended | Your `xai-...` key from console.x.ai |
| `FRONTEND_URL` | After first deploy | `https://aether-first-principles.onrender.com` (use your real URL) |
| `STRIPE_SECRET_KEY` | Optional | Leave blank for now |
| `STRIPE_PUBLISHABLE_KEY` | Optional | Leave blank |
| `STRIPE_PRO_PRICE_ID` | Optional | Leave blank |

Pre-filled by blueprint (leave as-is):
- `DATABASE_PATH` = `data/aether.db`
- `DEFAULT_MODEL` = `grok-4.5`
- `CORS_ORIGINS` = `*`
- `PYTHON_VERSION` = `3.12.8`

### 3. Apply / Deploy
Wait for **Live**. First free-tier build can take 5–10 minutes.

### 4. After Live
1. Copy the public URL (e.g. `https://aether-first-principles.onrender.com`)
2. Service → **Environment** → set `FRONTEND_URL` to that exact URL
3. **Manual Deploy** → Deploy latest commit (if needed)
4. Open the URL — you should see the AETHER space carnival UI
5. Smoke test: `https://YOUR-URL/api/health` → `{"status":"ok",...}`

---

## Path B — Manual Web Service

1. Open: https://dashboard.render.com/select-repo?type=web  
2. Select **`cyborgambitions/AETHER`**
3. Configure:

| Field | Value |
|-------|--------|
| Name | `aether-first-principles` |
| Region | Oregon (or closest) |
| Branch | **`v1-carnival-release`** |
| Root Directory | **`backend`** |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance type | Free |
| Health Check Path | `/api/health` |

4. **Environment** tab — add:

```
XAI_API_KEY=xai-your-key-here
DATABASE_PATH=data/aether.db
DEFAULT_MODEL=grok-4.5
CORS_ORIGINS=*
FRONTEND_URL=https://YOUR-SERVICE.onrender.com
```

5. Create Web Service → wait for deploy.

---

## Connect GitHub (if Render can’t see the repo)

1. Render → Account Settings → **GitHub** / **Connected Accounts**
2. Grant access to **cyborgambitions/AETHER** (or the whole org/user)
3. Retry Blueprint / New Web Service

---

## Using the live app

1. Open the Render URL  
2. Click **Connect Key** → paste `xai-...` key (browser-only storage)  
   **OR** enable **Use Hosted (Pro)** if you set `XAI_API_KEY` on Render  
3. Pick a mode → enter a topic → **Generate with Grok**  
4. API docs: `https://YOUR-URL/docs`

---

## Common issues

| Symptom | Fix |
|---------|-----|
| Build fails “No module named app” | Root Directory must be `backend` (or use Blueprint `rootDir`) |
| Deployed old UI / empty repo | Branch must be `v1-carnival-release`, not `main` |
| 502 / app crashed | Check Logs; ensure Start Command uses `$PORT` |
| Health check failing | Path must be `/api/health` |
| Grok 401/403 | Key must start with `xai-` from console.x.ai (not grok.com chat) |
| Free instance asleep | First request after idle can take ~30–60s to wake |
| Data resets on free tier | Expected — no persistent disk on free; upgrade later if needed |

---

## Optional: Stripe Pro ($9/mo)

1. Stripe Dashboard → Product **AETHER Pro** → recurring $9/mo  
2. Copy Price ID (`price_...`)  
3. Render env:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_PRO_PRICE_ID`
4. Redeploy. Without Stripe, “Upgrade to Pro” unlocks demo mode in the browser.

---

## Optional: persistent database (paid plan)

1. Upgrade instance above Free  
2. Add **Disk**: mount path `/var/data`, size 1 GB  
3. Set `DATABASE_PATH=/var/data/aether.db`  
4. Redeploy  

---

## Checklist

- [ ] Render account + GitHub connected  
- [ ] Service created from branch `v1-carnival-release`  
- [ ] Root = `backend` (manual) or Blueprint applied  
- [ ] `XAI_API_KEY` set (or plan to use browser keys only)  
- [ ] Deploy status **Live**  
- [ ] `/api/health` returns ok  
- [ ] UI loads; generate works  
- [ ] `FRONTEND_URL` set to live URL  

When Live, paste your `*.onrender.com` URL back here for a final health check.
