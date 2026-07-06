# How to Fix "403 Forbidden" / Get Grok Working in AETHER

The error `Client error '403 Forbidden'` means xAI rejected the API key.

## Step 1: Get a Real xAI API Key

1. Go to: **https://console.x.ai**
2. Sign in with your xAI / X account (or create one)
3. Create a new API key
4. Copy the key — it starts with `xai-`

**Important:**
- Keys from just using grok.com or the X app **do not work** for the API.
- You may need to add a payment method or have credits in the console.

## Step 2: Add the Key in AETHER (Easiest)

1. Make sure your local server is running (`python -m uvicorn ...`)
2. Open **http://localhost:8000**
3. In the top right, click the **key icon** (next to "API Key")
4. Paste your full `xai-...` key into the box
5. Click **Save Key**

The key is stored only in your browser.

Now click **RUN WITH GROK** again.

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
