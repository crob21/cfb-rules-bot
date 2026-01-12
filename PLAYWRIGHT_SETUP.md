# Playwright Setup for Render

After pushing the Playwright changes, you need to install the Chromium browser on Render.

## Steps:

1. **Push code** (already done)
2. **Wait for Render to deploy** (~3-5 minutes)
3. **SSH into Render and install Chromium**:
   - Go to Render Dashboard → Your Service → Shell tab
   - Run: `playwright install chromium`
   - This downloads the Chromium browser binary (~150MB)

## Alternative: Add to Render Build Command

You can automate this by updating your Render build command to:

```bash
pip install -r requirements.txt && playwright install chromium
```

This way it installs automatically on every deploy.

## Verifying it Works

After setup, check logs for:
```
✅ Playwright available - will use headless browser for Cloudflare bypass
🌐 Playwright browser initialized
✅ Playwright fetch successful
```

## Fallback Chain

If Playwright fails for any reason, the scraper automatically falls back to:
1. **Playwright** (headless browser) ← Best
2. **Cloudscraper** (HTTP with Cloudflare bypass) ← Good
3. **httpx** (plain HTTP) ← Will be blocked

## Testing

After setup, try:
```
/recruiting player name:Logan George
```

Should see in logs: `✅ Playwright fetch successful` instead of blocking errors.

