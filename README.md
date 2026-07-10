# AETHER

**First Principles Toolkit** — A web app for deep, assumption-busting reasoning powered by Grok (xAI).

> "The universe is under no obligation to make sense to you... yet."

This repository contains:

- The original 48-hour prompt collection (see markdown files)
- A full production web app (frontend + backend) with a stunning space-themed futuristic UI

---

## Project Structure

```
AETHER/
├── README.md                    # This file (project overview)
├── AETHER-48-Hour-Project.md    # Original prompt collection & story
├── backend/                     # The full web application (deploy this)
│   ├── app/
│   │   ├── main.py              # FastAPI backend
│   │   ├── prompts.py           # The 6 core modes
│   │   ├── database.py
│   │   └── grok.py              # xAI API client
│   ├── static/
│   │   └── index.html           # Stunning space-themed frontend (SPA)
│   ├── requirements.txt
│   ├── render.yaml              # Render.com deployment config
│   ├── .env.example
│   └── README.md                # Detailed app docs + run/deploy instructions
├── aether grok/                 # (legacy)
└── backend AETHER/              # (legacy)
```

**Key path:** The web app lives entirely inside `backend/`.

---

## Local Development

```powershell
cd C:\Users\MelG2\OneDrive\AETHER\backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Edit .env with your XAI_API_KEY (copy from .env.example)
cp .env.example .env
notepad .env

python -m uvicorn app.main:app --reload
```

Open http://localhost:8000

The frontend is a beautiful cosmic experience with:
- Animated starfield background
- Holographic/glassmorphic cards
- All 6 first-principles modes
- Workspace with live generation
- Community library + history
- Pricing / monetization (Stripe)

See `backend/README.md` and `backend/DEPLOY.md` for full details.

---

## Git & Repository

This is a single Git repository rooted at the `AETHER/` folder.

- The original prompt project lives at the root (markdown files).
- The modern web app is in the `backend/` subdirectory.

### Why this structure?
- Keeps history together
- Original docs are preserved
- The web app can be deployed independently (Render supports subdirectory root)

When deploying to Render:
- Connect the repo
- Set **Root Directory** = `backend`

---

## Deployment (Render.com)

**GitHub:** https://github.com/cyborgambitions/AETHER  
**Deploy branch:** `v1-carnival-release` (production UI + backend; preferred)  
**Blueprint file:** root `render.yaml` (`rootDir: backend`)

### One-shot Blueprint

1. Open [Render Dashboard → New Blueprint](https://dashboard.render.com/blueprints)
2. Connect repo **cyborgambitions/AETHER**, branch **`v1-carnival-release`**
3. Apply `render.yaml`
4. Set secrets when prompted:
   - `XAI_API_KEY` = your key from [console.x.ai](https://console.x.ai)
   - `FRONTEND_URL` = your `https://….onrender.com` URL (after first deploy)
5. Deploy → open the service URL

### Manual Web Service

1. [New Web Service](https://dashboard.render.com/select-repo?type=web) → this repo
2. Branch: `v1-carnival-release`
3. Root Directory: `backend`
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Health check: `/api/health`
7. Env: `XAI_API_KEY` (required for Hosted Pro), optional Stripe keys

See `backend/DEPLOY.md` for full details. Free tier uses ephemeral SQLite (`data/aether.db`).

---

## Credits

- Original 48-hour project: Grok + human collaborator
- Web app: Full FastAPI + stunning vanilla JS/Tailwind frontend with space theme
- Built to amplify first-principles thinking

License: MIT

Now go ask better questions. The universe is waiting. 🚀
