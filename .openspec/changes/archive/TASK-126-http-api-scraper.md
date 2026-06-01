# [TASK-126] fix: replace crawl4ai browser with AliExpress HTTP JSON API

## Objetivo
AliExpress bloqueia IPs de datacenter Railway quando usamos Playwright headless.
Substituir `_scrape_with_crawl4ai()` por `_scrape_with_http()` que chama o endpoint
JSON interno `https://www.aliexpress.com/fn/search-pc/index` via httpx — sem browser.

## Pacote / Módulo
`app/scrapers/aliexpress.py`

## Contratos

```python
async def _scrape_with_http(
    category_id: str, max_results: int, session_cookies: str = ""
) -> list[AliProduct]:
    """Faz GET no endpoint SPA JSON da AliExpress. Retorna [] se IP bloqueado (HTML)."""

def _parse_fn_json(data: dict, category_id: str, max_results: int) -> list[AliProduct]:
    """Extrai AliProduct da resposta JSON do endpoint /fn/search-pc/index."""

async def get_hot_products(
    category_id: str, min_rating: float = 0.0, max_results: int = 100
) -> list[AliProduct]:
    """Dispatcher: SCRAPER_MODE=http (novo default) | crawl4ai | mock."""
```

## Detalhes de Implementação

- `httpx` já está em requirements.txt (0.28.1) — nenhuma dependência nova
- SCRAPER_MODE default muda de `crawl4ai` → `http`
- `SCRAPER_MODE=crawl4ai` e `firecrawl` → `_scrape_with_crawl4ai()` (backward compat)
- Fluxo HTTP: desktop URL → se HTML/vazio → mobile URL → se ainda vazio → crawl4ai fallback
- Headers obrigatórios: User-Agent Chrome/120, Accept json, Referer aliexpress, X-Requested-With
- Cookies (ALIEXPRESS_SESSION_COOKIES): injetados como `cookies={name: value}` no httpx request
- Resposta HTML (começa com `<`) → log warning, retornar []
- Resposta não-JSON → log warning, retornar []
- JSON path primário: `data.result.resultList[].item`
- Campos extraídos: itemId, title, prices.salePrice.formattedPrice, tradeDesc, averageStar, imageUrl

## Tasks (checklist)
- [x] Escrever testes RED (`tests/test_issue126_http_api.py`)
- [x] Implementar `_parse_fn_json()`
- [x] Implementar `_scrape_with_http()` com httpx + 2 URLs + fallback
- [x] Atualizar `get_hot_products()` — default `http`, crawl4ai/firecrawl compat
- [x] Corrigir `test_scraper.py` — adicionar SCRAPER_MODE=crawl4ai ao teste sem env var
- [x] Rodar suite completa, verificar verde

## Critérios de Verificação
- `SCRAPER_MODE=http` + mock httpx com JSON válido → retorna AliProduct list
- Response HTML → warning logado, retorna []
- Desktop vazio → mobile tentada (segunda chamada httpx)
- Cookies presentes no request httpx quando ALIEXPRESS_SESSION_COOKIES setado
- `SCRAPER_MODE=crawl4ai` → `_scrape_with_crawl4ai` chamado (não `_scrape_with_http`)
- Default (sem SCRAPER_MODE) → mode `http`
- Suite completa: `pytest tests/ -x` verde
