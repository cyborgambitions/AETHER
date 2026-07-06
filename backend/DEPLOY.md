# Deploy AETHER to Render.com + GitHub

## 1. Prepare the code (already done)

The `backend/` folder contains everything needed.

## 2. Create GitHub Repository

```powershell
cd "$HOME\OneDrive\AETHER\backend"

# Initialize git (if not already)
git init
git add .
git commit -m "Initial AETHER deploy - beautiful first principles toolkit with monetization"

# Create repo on GitHub (web or gh CLI)
# Then connect:
git remote add origin https://github.com/YOUR_USERNAME/aether-first-principles.git
git branch -M main
git push -u origin main
```

## 3. Deploy on Render

1. Go to https://render.com
2. New Web Service → Connect GitHub
3. Select your `aether-first-principles` repo
4. Render will auto-detect Python and use `render.yaml`
5. Add these **Environment Variables** in the dashboard:
   - XAI_API_KEY
   - STRIPE_SECRET_KEY
   - STRIPE_PUBLISHABLE_KEY  
   - STRIPE_PRO_PRICE_ID
6. After first deploy:
   - Add a Disk: Mount path `/var/data`
   - Set env: `DATABASE_PATH=/var/data/aether.db`
7. Deploy!

## 4. Post-Deploy

- Visit your Render URL
- Set your xAI key via the key icon (or use hosted Pro)
- Test the Upgrade to Pro button

## Monetization Setup

1. In Stripe Dashboard create a recurring product ($9/mo)
2. Copy the Price ID
3. Put it in Render env as `STRIPE_PRO_PRICE_ID`

Done. Your beautiful first-principles toolkit with real monetization is live.
