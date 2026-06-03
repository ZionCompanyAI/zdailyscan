# ZdailyScan — Architecture Reference

## Overview

ZdailyScan is a daily AliExpress opportunity scanner for the HI Select Store (Shopify). It runs automatically at 09:00 UTC (06:00 BRT), analyzes import viability via ML market data + tax calculation, and delivers the Top 10 products to Telegram and a web dashboard.

---

## Pipeline Flow

```
APScheduler (09:00 UTC daily)
        │
        ▼
pipeline.run_daily_scan()
        │
        ├── scrapers/aliexpress.py
        │       │
        │       ├── SCRAPER_MODE=firecrawl  → Firecrawl /v1/scrape (default)
        │       │       └── on HTTP 402     → scrapling (curl + JS extraction)
        │       ├── SCRAPER_MODE=scrapling  → curl + JS inline extraction
        │       ├── SCRAPER_MODE=crawl4ai   → AsyncWebCrawler + Playwright
        │       ├── SCRAPER_MODE=http       → AliExpress JSON API → crawl4ai fallback
        │       └── SCRAPER_MODE=mock       → static fixtures (test only)
        │               └── yields list[AliProduct]
        │
        ├── [tech filter]  categories only: is_tech_product(title) — skips non-tech
        │
        ├── analyzers/mercado_livre.py     → BRMarket (avg/min/max price, result_count)
        │       └── (see ML token cascade below)
        │
        ├── analyzers/import_calculator.py → ImportCost (tax_brl, total_cost_brl, regime)
        │
        ├── analyzers/trend_analyzer.py   → trend_score 0–1 (pytrends Google Trends BR)
        │       └── 24h in-memory cache per keyword; fallback → 0.5
        │
        └── scoring/scorer.py             → ProductScore (score_total, viavel, sell_price)
                │
                ├── send_daily_report()    → reporters/telegram_reporter.py
                │       └── POST $MC_URL/telegram/reply (Top 10)
                └── save_daily_report()   → reporters/file_reporter.py (Markdown)

storage.py: save_scan() → /data/scans/YYYY-MM-DD.json (Railway Volume)
```

---

## Module Responsibilities

| Module | File | Responsibility |
|--------|------|----------------|
| **Scheduler** | `app/scheduler.py` | APScheduler AsyncIO — triggers daily scan at 09:00 UTC |
| **Pipeline** | `app/pipeline.py` | Orchestrates scrape → analyze → score → report; defines `ScanResult` |
| **Scraper** | `app/scrapers/aliexpress.py` | Multi-mode AliExpress product extraction (4 strategies + mock) |
| **ML Analyzer** | `app/analyzers/mercado_livre.py` | MercadoLibre BR market search; auth cascade + Zoom.com.br fallback |
| **Import Calculator** | `app/analyzers/import_calculator.py` | Brazilian import tax (II + ICMS) by regime |
| **Trend Analyzer** | `app/analyzers/trend_analyzer.py` | Google Trends BR via pytrends; 24h cache |
| **Scorer** | `app/scoring/scorer.py` | Weighted score formula; viability gate |
| **Storage** | `app/storage.py` | JSON persistence on Railway Volume `/data/scans/` |
| **Telegram Reporter** | `app/reporters/telegram_reporter.py` | Formats and sends Top 10 via Mission Control relay |
| **File Reporter** | `app/reporters/file_reporter.py` | Saves Markdown daily report |
| **API** | `app/main.py` | FastAPI: `/health`, `/scan/latest`, `/scan/{date}`, `/scan/run` |
| **Dashboard** | `app/routers/dashboard.py` | Authenticated web UI — list scans, trigger manual scan |
| **Auth** | `app/routers/auth.py` | Cookie session auth (itsdangerous) for dashboard |
| **Config** | `app/config.py` | Pydantic settings from env vars |

---

## Score Formula

```
score_total = 0.30 × Margem
            + 0.25 × Demanda_BR
            + 0.20 × Oportunidade
            + 0.15 × Tendência
            + 0.10 × Logística
```

### Component Definitions

| Component | Weight | Formula | Range |
|-----------|--------|---------|-------|
| **Margem** | 30% | `(avg_price_brl − total_cost_brl) / avg_price_brl` | 0–1 |
| **Demanda_BR** | 25% | `min(result_count / 100, 1.0)` | 0–1 |
| **Oportunidade** | 20% | `1.0 − min(result_count / 500, 1.0)` | 0–1 |
| **Tendência** | 15% | Google Trends BR normalized interest (90 days) | 0–1 |
| **Logística** | 10% | `1.0` (price ≤ $50) · `0.6` ($50–$100) · `0.3` (> $100) | 0.3/0.6/1.0 |

**Viability gate:** `score_total >= 0.60`

**Suggested sell price:** `total_cost_brl × 2.5`

---

## Import Tax Calculation (Brazil)

Two regimes based on total shipment value (USD):

| Regime | Condition | Imposto de Importação (II) | ICMS |
|--------|-----------|---------------------------|------|
| `remessa_conforme` | total_usd ≤ $50 | 20% × base_brl | 17% × base_brl |
| `normal` | total_usd > $50 | 60% × base_brl | 17% por dentro (base includes II) |

```
base_brl = (price_usd + freight_usd) × USD_BRL_RATE

# remessa_conforme
tax_brl = 0.20 × base_brl + 0.17 × base_brl

# normal
ii      = 0.60 × base_brl
icms    = (base_brl + ii) × 0.17 / (1 − 0.17)   # ICMS por dentro
tax_brl = ii + icms

total_cost_brl = base_brl + tax_brl
```

---

## ML Token Fallback Cascade

```
get_ml_token()
    │
    ├── AUTH_BUS_URL + AUTH_BUS_API_KEY set?
    │       └── GET $AUTH_BUS_URL/tokens/mercadolibre
    │               ├── 200 → use access_token ✓
    │               └── error / timeout → continue ↓
    │
    └── ML_USER_ACCESS_TOKEN env var (static fallback)
```

## Market Search Fallback Cascade

```
search_br_market(query)
    │
    ├── ML_SEARCH_PROXY_URL set?
    │       └── GET $ML_SEARCH_PROXY_URL?q=...
    │               ├── success → parse results ✓
    │               └── error → continue ↓
    │
    ├── GET api.mercadolibre.com/sites/MLB/search?q=...
    │       ├── success → parse results ✓
    │               └── error → continue ↓
    │
    └── search_br_market_via_zoom(query)
            └── GET zoom.com.br/search?q=... (scrape __NEXT_DATA__ JSON)
                    ├── success → parse hits ✓
                    └── error → return BRMarket(found=False)
```

---

## Persistence Strategy

### Current: Railway Volume `/data/`

```
/data/
└── scans/
    ├── 2026-06-01.json
    ├── 2026-06-02.json
    └── YYYY-MM-DD.json   ← one file per day (ScanResult JSON)
```

- **Pros:** zero DB ops, fast reads, simple file-based history.
- **Cons:** ephemeral if Volume is not mounted; no querying across dates.
- **Critical:** Railway Volume must be mounted at `/data/` — without it, scans are lost on every restart.

### Relational Database (not implemented)

A PostgreSQL schema would allow querying trends over time, product history, and deduplication. Worth considering if scan history grows beyond a few months or cross-day queries are needed.

---

## Scan Targets

Each daily scan iterates over **categories** (bestseller pages) and **keywords** (search results):

| Type | Source | Default values |
|------|--------|---------------|
| Categories | `SCAN_CATEGORIES` env (CSV of IDs) | `200003655` (Consumer Electronics), `100003070` (Phones & Telecom), `200000783` (Computer & Office) |
| Keywords | `SCAN_KEYWORDS` env (CSV) | USB-C adapter, USB hub multiport, HDMI adapter, wireless charger, phone stand, laptop stand, bluetooth earphones, Thunderbolt hub, screen protector, power bank |

Category results are filtered by `is_tech_product()` (regex against 30+ tech keywords). Keyword results skip the tech filter.

---

## API Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| `GET` | `/health` | — | Health check → `{"status":"ok"}` |
| `GET` | `/scan/latest` | — | Most recent ScanResult JSON |
| `GET` | `/scan/{date}` | — | ScanResult for YYYY-MM-DD |
| `POST` | `/scan/run` | `x-api-key` header | Trigger background scan |
| `GET` | `/scrapers/aliexpress` | — | Raw scrape debug (category + limit) |
| `GET` | `/dashboard` | cookie session | List available scans |
| `GET` | `/dashboard/{date}` | cookie session | Products for a specific day |
| `POST` | `/dashboard/scan` | cookie session | Trigger manual scan from UI |
| `GET/POST` | `/login` `/logout` | — | Dashboard authentication |

---

## Deployment

```
Railway Container
    │
    ├── Dockerfile / nixpacks.toml
    │       └── playwright install chromium (on startup via railway.toml)
    ├── APScheduler (in-process, AsyncIO)
    └── Uvicorn → FastAPI app
```

`railway.toml` start command:
```bash
bash -c 'playwright install chromium --with-deps && uvicorn app.main:app --host 0.0.0.0 --port $PORT'
```

Health check: `GET /health` — Railway waits for 200 before marking deployment live (allow ~3 min for Playwright install).
