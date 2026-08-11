# How to Fix API Key Errors / Get Grok Working in AETHER

xAI rejected your API key. Common messages:

- `Incorrect API key provided` (HTTP 400)
- `403 Forbidden` / unauthorized
- Misleading "model name" text that appears after the client retried fallbacks on a bad key

## Step 1: Get a Real xAI API Key

1. Go to: **https://console.x.ai**
2. Sign in with your xAI / X account (or create one)
3. Create a new API key
4. Copy the key — it starts with `xai-`

**Important:**
- Keys from just using grok.com or the X app **do not work** for the API.
- You may need to add a payment method or have credits in the console.

## Step 2A: Fix Render (live site)

If you see this on **https://aether-first-principles.onrender.com**:

1. Open [Render Dashboard](https://dashboard.render.com) → service **aether-first-principles**
2. **Environment** → set `XAI_API_KEY` to your real `xai-...` key (not `xai-REPLACE_...`)
3. Optional: set `DEFAULT_MODEL` = `grok-4.5`
4. **Manual Deploy** → **Deploy latest commit** (or Save Environment so it restarts)
5. Wait until Live, then hard-refresh the site

Or use **Connect Key** in the UI (browser-only; does not need Render env).

## Step 2B: Add the Key in AETHER UI (Easiest for you)

1. Open the live site or local server
2. Click **Connect Key** / the key icon
3. Paste your full `xai-...` key
4. Click **Save Key**

The key is stored only in your browser.

Now click **GENERATE WITH GROK** again.

## Step 3: Alternative - Set Key on the Server (.env)

Run these commands in PowerShell:

```powershell
cd "$HOME\OneDrive\AETHER\backend"

# Create .env with your key (replace the part after = )
"XAI_API_KEY=xai-PASTE_YOUR_KEY_HERE" | Out-File .env -Encoding utf8 -Force

# (Optional) Also copy other settings
Get-Content .env.example | Where-Object { $_ -notlike 'XAI_API_KEY*' } | Add-Content .env
```

Then **restart the server** completely (Ctrl+C then run the start command again).

## Quick Test If Your Key Works

Paste this in PowerShell (replace the key):

```powershell
$key = "xai-PASTE_YOUR_KEY_HERE"
$headers = @{ Authorization = "Bearer $key" }
try {
    $models = Invoke-RestMethod -Uri "https://api.x.ai/v1/models" -Headers $headers
    Write-Host "SUCCESS! Your key works. Available models:"
    $models.data | ForEach-Object { $_.id }
} catch {
    Write-Host "Key failed:" $_.Exception.Message -ForegroundColor Red
}
```

## After Fixing

- Stop the current server with **Ctrl + C**
- Restart with:
  ```powershell
  cd "$HOME\OneDrive\AETHER\backend"; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload
  ```
- Refresh http://localhost:8000
- Enter key via the icon if not using .env
- Try a prompt

## Still getting 403?

- Double-check there are no extra spaces before/after the key
- Make sure it really starts with `xai-`
- Check you have credits/billing set up at console.x.ai
- Try generating a new key

The AETHER code was just updated to give clearer messages on bad keys. Restart the server after pulling these changes.
