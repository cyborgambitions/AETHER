# AETHER — First Principles Toolkit

**A beautiful, production-ready web app for deep, first-principles reasoning with Grok (xAI).**

Built from the original 48-hour prompt project into a full interactive toolkit with community features, history, and monetization options.

- **Live Demo**: Deploy yourself to Render in minutes.
- **Core**: 6 powerful prompt templates + community prompts.
- **Magic**: One-click "Run with Grok" — bring your own key or use hosted Pro.
- **Monetization built-in**: Free tier + Pro upgrades via Stripe.

---

## Features

- 6 canonical first-principles modes (Deconstructor, Hypothesis Generator, Truth Audit, Consequence Mapper, Synthesizer, Question Amplifier)
- Beautiful cosmic dark UI (Tailwind + custom design)
- Community prompt submission + voting
- Research history + chaining outputs
- Bring-your-own xAI key (free) or hosted Pro mode
- Usage quotas + Stripe monetization
- Fully deployable to Render.com

---

## Quick Local Run

```powershell
cd backend   # or the root of this repo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Set your keys
cp .env.example .env
# Edit .env with your XAI_API_KEY (and Stripe keys for monetization)

python -m uvicorn app.main:app --reload
```

Open http://localhost:8000

Click the **key icon** to paste your xAI key.

---

## Deploy to Render.com (Recommended)

1. Push this code to a GitHub repo (see below).
2. Go to [render.com](https://render.com) → New + Web Service → Connect your GitHub repo.
3. Use these settings (or use the included `render.yaml`):
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables in Render dashboard:
   - `XAI_API_KEY` (your xAI key for hosted Pro)
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_PRO_PRICE_ID` (create a $9/mo product in Stripe)
5. **Important for persistence**:
   - After first deploy, add a **Disk** in the Render service dashboard:
     - Mount path: `/var/data`
     - Size: 1 GB
   - Add env var: `DATABASE_PATH=/var/data/aether.db`

The `render.yaml` in the repo makes blueprint deploys easy.

---

## Monetization Options (Stripe)

The app includes a beautiful **Pricing** section.

### Current Model

- **Free**
  - Bring your own xAI API key (unlimited for you)
  - 50 generations / day on hosted mode (if server key is set)
  - Full access to core toolkit + history

- **Pro — $9/month** (recommended setup)
  - Unlimited generations using the server's xAI key
  - Cloud-saved custom prompts
  - Advanced history export
  - Priority community features

### How to Set Up Monetization

1. Create a Stripe account.
2. Create a product called "AETHER Pro" ($9/mo recurring).
3. Copy the **Price ID** (starts with `price_...`).
4. Add to Render env vars:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_PRO_PRICE_ID`
5. In the app, users click "Upgrade to Pro" → Stripe Checkout → success unlocks Pro features.

Test mode works great for development (use `4242 4242 4242 4242`).

You keep 100% of the revenue (minus Stripe fees).

---

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI + Stripe routes + quota
│   ├── prompts.py       # The 6 core prompts
│   ├── database.py      # SQLite (or Postgres ready)
│   └── grok.py          # xAI API client
├── static/
│   └── index.html       # Beautiful single-page app
├── requirements.txt
├── render.yaml
├── .env.example
└── README.md
```

---

## Environment Variables

See `.env.example`.

Required for full monetization + hosted:

- `XAI_API_KEY`
- Stripe keys (optional but powerful for revenue)

---

## GitHub + Deploy Commands

See the bottom of this README or the separate deploy instructions.

---

## Credits

Originally a 48-hour first-principles project for xAI.

Extended with beautiful UI, persistence, community, and real monetization.

Built with ❤️ for truth-seeking.

**The universe is under no obligation to make sense to you... yet.**

---

## Next Steps After Deploy

- Connect a custom domain on Render
- Set up Stripe webhooks (for automatic Pro status)
- Add email capture for marketing
- Expand premium prompt packs

Let's make humanity think better — and get paid for it.
