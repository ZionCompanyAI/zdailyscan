# [TASK-143] fix: replace Scrapling Fetcher with httpx — Playwright conflict in async context

## Objetivo
Substituir `StealthyFetcher` do Scrapling (que usa Playwright/camoufox) por `httpx.get` dentro de
`_scrape_with_scrapling()`. O Fetcher causa falha fatal em contexto async FastAPI:
`FileNotFoundError: Version information not found at /root/.cache/camoufox/version.json` e
`Error: It looks like you are using Playwright Sync API inside the asyncio loop.`

## Pacote / Módulo
`app/scrapers/aliexpress.py` → funções `_scrape_with_scrapling()` + nova `_find_product_list()`

## Contratos

```python
def _find_product_list(data: dict | list, _depth: int = 0) -> list | None:
    """Busca recursiva por lista de dicts com 'productId'."""

async def _scrape_with_scrapling(
    category_id: str, max_results: int, keyword: str = ""
) -> list[AliProduct]:
    """HTTP GET via httpx; extrai window._dida_config_._init_data_ via regex + json.raw_decode."""
```

## Detalhes de Implementação
- Remover `asyncio.to_thread`, `from scrapling.fetchers import StealthyFetcher`
- Remover lógica de CSS selectors (`.search-item-card-wrapper-gallery`)
- Usar `httpx.get(url, headers=_SCRAPLING_HEADERS, follow_redirects=True, timeout=15)`
- Regex: `re.search(r"window\\._dida_config_\\._init_data_\\s*=\\s*", html)` + `json.JSONDecoder().raw_decode`
- Campos do JSON: `productId`, `title.displayTitle`, `prices.salePrice.minPrice`, `star_rating`, `real_trade_count`, `image.imgUrl`
- `httpx` já está em `requirements.txt` (httpx==0.28.1)

## Tasks
- [x] Criar spec `.openspec/changes/TASK-143-scrapling-httpx-fix.md`
- [ ] RED: escrever `tests/test_issue143_scrapling_httpx.py`
- [ ] GREEN: reescrever `_scrape_with_scrapling` + adicionar `_find_product_list`
- [ ] Atualizar testes quebrados em `test_issue139_scrapling.py`
- [ ] VERIFY: rodar suite completa

## Critérios de Verificação
- `POST /scan/run` retorna `total_scanned > 0`
- Nenhuma menção a `camoufox`, `Playwright` ou `StealthyFetcher` nos logs
- `asyncio.to_thread` NÃO é chamado dentro de `_scrape_with_scrapling`
- Testes existentes continuam passando (CI verde)
