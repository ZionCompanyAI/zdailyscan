# [TASK-159] fix(scraper): session cookies para subprocess curl + delay entre targets

## Objetivo
Passar ALIEXPRESS_SESSION_COOKIES como Cookie header no subprocess curl
do scrapling, e adicionar delay de 2s entre targets no pipeline.

## Módulos
- `app/scrapers/aliexpress.py` → `_scrape_with_scrapling()`
- `app/pipeline.py` → `run_daily_scan()`

## Contratos

```python
# Fix 1 — aliexpress.py (dentro de _scrape_with_scrapling, antes de if keyword:)
_session_cookies_raw = os.environ.get("ALIEXPRESS_SESSION_COOKIES", "")
_cookie_header = ""
if _session_cookies_raw:
    try:
        _raw_cookies = json.loads(_session_cookies_raw)
        _cookie_header = "; ".join(
            f"{c['name']}={c['value']}" for c in _raw_cookies if c.get("value")
        )
    except Exception:
        pass

# curl command: adicionar "-H", f"Cookie: {_cookie_header}" quando _cookie_header truthy

# Fix 2 — pipeline.py (após for product in products: loop)
await asyncio.sleep(2)
```

## Tasks
- [x] Escrever testes RED (test_issue159_session_cookies_curl.py)
- [x] Fix 1: _scrape_with_scrapling lê cookies e passa para curl
- [x] Fix 2: asyncio.sleep(2) no loop de pipeline
- [x] Verify: pytest tests/ -x -q

## Critérios de Verificação
```bash
grep -q "_cookie_header" app/scrapers/aliexpress.py && grep -q "asyncio.sleep" app/pipeline.py && echo PASS || echo FAIL
```
