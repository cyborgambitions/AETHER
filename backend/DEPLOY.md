# Deploy AETHER to Render.com

Repo: https://github.com/cyborgambitions/AETHER  
App root: `backend/`

---

## Option A — Blueprint (fastest)

1. Push latest code to GitHub (`main` or `v1-carnival-release`).
2. Open [render.com](https://render.com) → **New +** → **Blueprint**.
3. Connect the `cyborgambitions/AETHER` repo.
4. Render reads root `render.yaml` (`rootDir: backend`).
5. When prompted, set secrets:
   - **XAI_API_KEY** — your `xai-...` key from [console.x.ai](https://console.x.ai)
   - **FRONTEND_URL** — set after first deploy to `https://YOUR-SERVICE.onrender.com`
   - Stripe keys optional (Pro checkout works in demo mode without them)
6. Deploy. Open the service URL.

---

## Option B — Manual Web Service

1. **New +** → **Web Service** → connect `cyborgambitions/AETHER`
2. Settings:
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/health`
3. Environment variables (same as Option A).
4. Deploy.

---

## After first deploy

1. Copy the public URL (e.g. `https://aether-first-principles.onrender.com`).
2. Set env `FRONTEND_URL` to that URL (for Stripe redirects).
3. Visit the site → **Connect Key** (or use Hosted Pro if `XAI_API_KEY` is set).
4. Free tier disks are not available; SQLite uses ephemeral `data/aether.db`.  
   For persistence, upgrade the plan and add a Disk at `/var/data` with  
   `DATABASE_PATH=/var/data/aether.db`.

---

## Local smoke test before deploy

```powershell
cd $HOME\OneDrive\AETHER\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# ensure .env has XAI_API_KEY
python -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 and hit `/api/health`.

---

## Monetization (optional)

1. Stripe → Product **AETHER Pro** → $9/mo recurring.
2. Copy Price ID (`price_...`).
3. Set on Render: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRO_PRICE_ID`.

---

## Git push (from this machine)

```powershell
cd $HOME\OneDrive\AETHER
git add -A
git commit -m "Ship stunning AETHER UI + Render deploy config"
git push origin v1-carnival-release
# optional: also update main
git checkout main
git merge v1-carnival-release
git push origin main
git checkout v1-carnival-release
```

Done. Your first-principles carnival is live.
