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

See `backend/DEPLOY.md` for step-by-step.

High-level:
1. Push this repo to GitHub
2. Create Web Service on Render
3. Set Root Directory to `backend`
4. Add environment variables (XAI_API_KEY, optional Stripe keys)
5. Add a persistent Disk for `DATABASE_PATH=/var/data/aether.db`

---

## Credits

- Original 48-hour project: Grok + human collaborator
- Web app: Full FastAPI + stunning vanilla JS/Tailwind frontend with space theme
- Built to amplify first-principles thinking

License: MIT

Now go ask better questions. The universe is waiting. 🚀
