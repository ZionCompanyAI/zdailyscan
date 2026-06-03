# ZDailyScan — Operations Runbook

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `ALIEXPRESS_APP_KEY` | AliExpress Affiliate API app key |
| `ALIEXPRESS_APP_SECRET` | AliExpress Affiliate API app secret |
| `ALIEXPRESS_TRACKING_ID` | AliExpress affiliate tracking ID |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for daily reports |
| `MC_API_KEY` | Mission Control API key (used to send Telegram messages) |
| `MC_URL` | Mission Control base URL (e.g. `https://orchestrator.zioncompanyai.com.br`) |
| `DASHBOARD_PASSWORD` | Password for the `/dashboard` web UI |
| `DASHBOARD_SESSION_SECRET` | Secret used to sign session cookies (random string, 32+ chars) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `ALIEXPRESS_SESSION_COOKIES` | `""` | AliExpress session cookies (JSON string). Required if API scraping is blocked. Editable via the Settings page. |
| `USD_BRL_RATE` | `5.70` | USD → BRL exchange rate used in import cost calculations |
| `ZDAILYSCAN_TELEGRAM_CHAT_ID` | `7041182277` | Telegram chat ID that receives the daily report |
| `DASHBOARD_USERNAME` | `admin` | Username for the `/dashboard` web UI |
| `SCAN_API_KEY` | `test` | API key for the `POST /scan/run` endpoint (set to a strong random value in production) |
| `DATA_DIR` | `data` | Directory where scan JSON files are stored. On Railway: set to `/data` (mounted volume). |
| `SCAN_CATEGORIES` | all three | Comma-separated AliExpress category IDs to scan. See [Categories](#adjusting-categories-and-keywords). |
| `SCAN_KEYWORDS` | see below | Comma-separated keyword search terms. See [Keywords](#adjusting-categories-and-keywords). |
| `SCRAPER_MODE` | `crawl4ai` | Scraper backend. Options: `crawl4ai`, `scrapling`. |
| `AUTH_BUS_URL` | `https://auth-bus.zioncompanyai.com.br` | Auth-bus base URL for fetching ML OAuth tokens |
| `AUTH_BUS_API_KEY` | `""` | Auth-bus API key. If unset, falls back to `ML_USER_ACCESS_TOKEN`. |
| `ML_USER_ACCESS_TOKEN` | `""` | Mercado Livre access token (fallback when auth-bus is unavailable) |
| `RAILWAY_API_TOKEN` | `""` | Railway API token. Required to persist settings (cookies, categories) across restarts via Railway's GraphQL API. |
| `RAILWAY_PROJECT_ID` | `""` | Railway project ID (used alongside `RAILWAY_API_TOKEN`) |
| `RAILWAY_ENVIRONMENT_ID` | `""` | Railway environment ID |
| `RAILWAY_SERVICE_ID` | `""` | Railway service ID |

---

## Deploy on Railway

### railway.toml

```toml
[deploy]
startCommand = "bash -c 'playwright install chromium --with-deps && uvicorn app.main:app --host 0.0.0.0 --port $PORT'"
healthcheckPath = "/health"
restartPolicyType = "on_failure"
```

Playwright is installed at container start because Railway does not cache the Chromium binary between deploys when using nixpacks without a custom Dockerfile. If startup time is a concern, build a custom Docker image with `crawl4ai-setup` baked in (see `Dockerfile`).

### Persistent Volume

Scan results are stored in `DATA_DIR/scans/` as JSON files. Without a mounted volume the data is lost on every redeploy.

1. In the Railway dashboard, go to the service → **Volumes** → **Add Volume**.
2. Mount path: `/data`
3. Set the env var `DATA_DIR=/data` on the service.

### Scheduled Scan

The scheduler fires automatically at **09:00 server time** (APScheduler cron). No external cron is needed. To trigger a scan manually:

```bash
curl -X POST https://<your-domain>/scan/run \
  -H "x-api-key: <SCAN_API_KEY>"
```

---

## Adjusting Categories and Keywords

### Categories

Three AliExpress categories are supported:

| ID | Name |
|----|------|
| `200003655` | Consumer Electronics |
| `100003070` | Phones & Telecommunications |
| `200000783` | Computer & Office |

To restrict scanning to a subset, set `SCAN_CATEGORIES` to a comma-separated list of IDs:

```
SCAN_CATEGORIES=200003655,100003070
```

Alternatively, use the **Settings** page in the dashboard to toggle categories — the selection is persisted to Railway env vars automatically (requires `RAILWAY_*` vars to be set).

If `SCAN_CATEGORIES` is empty or unset, all three categories are scanned.

### Keywords

Keyword searches complement category browsing. Each keyword runs a targeted AliExpress product search (up to 10 results per keyword).

Default keywords:
```
USB-C adapter, USB hub multiport, HDMI adapter, wireless charger, phone stand,
laptop stand, bluetooth earphones, Thunderbolt hub, screen protector, power bank
```

Override via env var (comma-separated):

```
SCAN_KEYWORDS=USB-C hub,magsafe charger,airpods case
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| **Scan returns 0 products** | AliExpress is blocking requests (bot detection). `ALIEXPRESS_SESSION_COOKIES` missing or expired. | Obtain fresh session cookies from a browser, paste them in **Dashboard → Settings → AliExpress cookies**, or set `ALIEXPRESS_SESSION_COOKIES` env var. Switch `SCRAPER_MODE=scrapling` as an alternative. |
| **ML (Mercado Livre) search fails / market data missing** | `AUTH_BUS_API_KEY` is unset and `ML_USER_ACCESS_TOKEN` is expired or empty. | Refresh the ML OAuth token and set it in `ML_USER_ACCESS_TOKEN`, or configure `AUTH_BUS_API_KEY` to let the service fetch tokens from auth-bus automatically. |
| **Playwright / Crawl4AI timeout** | Chromium binary not installed (Railway deploy without the `playwright install` step), or the container ran out of memory. | Verify `startCommand` in `railway.toml` includes `playwright install chromium --with-deps`. Increase Railway service RAM to at least 1 GB. Check logs for `TimeoutError` or `OOM` markers. |
| **PolicyAgent / AliExpress API 403** | AliExpress API rejects the request due to an IP policy or missing/invalid `ALIEXPRESS_APP_KEY`. | Confirm `ALIEXPRESS_APP_KEY` and `ALIEXPRESS_APP_SECRET` are correct. If using the Firecrawl/Scrapling fallback, ensure the scraper is not hitting the same IP too frequently — add a `SCAN_CATEGORIES` filter to reduce request volume. |
| **Dashboard returns 502** | The Railway service crashed during startup (Playwright install failed, missing required env var, or port mismatch). | Check Railway deploy logs. Confirm all **required** env vars are set. Confirm `PORT` is provided by Railway (it is set automatically — do not hardcode it). The healthcheck at `/health` must return 200 before Railway marks the deploy as healthy. |

---

## Smoke Tests

Run these after every deploy to verify the service is up and data is accessible:

```bash
# Service is alive
curl -sf https://<your-domain>/health | python3 -m json.tool
# Expected: {"status": "ok", "service": "zdailyscan"}

# Latest scan is available
curl -sf https://<your-domain>/scan/latest | python3 -m json.tool
# Expected: JSON object with scan_id, date, products[], total_scanned, total_viable

# Trigger a manual scan (replace <key> with SCAN_API_KEY value)
curl -sf -X POST https://<your-domain>/scan/run \
  -H "x-api-key: <key>" | python3 -m json.tool
# Expected: {"status": "started", "scan_id": "<uuid>"}
```
