# [TASK-115] fix(scraper) — substituir Firecrawl por crawl4ai no scraper de categorias AliExpress

## Objetivo
Remover a chamada ao Firecrawl de `get_hot_products()`. AliExpress bloqueia Firecrawl
com 408 Request Timeout, resultando em `total_scanned=0` no pipeline. crawl4ai
(headless Playwright) já funciona para scans por categoria e deve ser o único scraper
ativo.

## Pacote / Módulo
- `app/scrapers/aliexpress.py` → função `get_hot_products()`
- `tests/test_scraper.py` → remover testes de modo Firecrawl obsoletos
- `tests/test_scraper_regressions.py` → remover `test_scraper_mode_firecrawl_nao_chama_crawl4ai`
- `tests/test_issue98_crawl4ai_no_cookies.py` → remover `test_no_cookies_crawl4ai_empty_falls_back_to_firecrawl`
- `tests/test_issue115_no_firecrawl_fallback.py` → novo arquivo de testes da issue

## Contratos

```python
# ANTES (aliexpress.py)
async def get_hot_products(
    category_id: str, min_rating: float = 0.0, max_results: int = 100
) -> list[AliProduct]:
    mode = os.environ.get("SCRAPER_MODE", "crawl4ai")
    firecrawl_url = os.environ.get("FIRECRAWL_URL", "")
    ...
    if mode == "firecrawl":
        if firecrawl_url:
            products = await get_products_via_firecrawl(...)  # ← REMOVER
    ...
    products = await _scrape_with_crawl4ai(...)
    if not products and firecrawl_url:
        products = await get_products_via_firecrawl(...)  # ← REMOVER

# DEPOIS (aliexpress.py)
async def get_hot_products(
    category_id: str, min_rating: float = 0.0, max_results: int = 100
) -> list[AliProduct]:
    mode = os.environ.get("SCRAPER_MODE", "crawl4ai")
    session_cookies = os.environ.get("ALIEXPRESS_SESSION_COOKIES", "")
    if mode == "mock":
        ...
    products = await _scrape_with_crawl4ai(category_id, max_results, session_cookies)
    filtered = [p for p in products if p.rating >= min_rating]
    return filtered[:max_results]
```

## Detalhes de Implementação
- Remover `from app.scrapers.fallback_firecrawl import get_products_via_firecrawl` de `aliexpress.py`
- Remover leitura de `FIRECRAWL_URL` em `get_hot_products()`
- `SCRAPER_MODE=firecrawl` passa a ser tratado como `crawl4ai` (sem branch separado)
- Manter `fallback_firecrawl.py` no repo (testes #91/#94 testam-no diretamente)
- Não modificar `app/pipeline.py` nem `app/scrapers/fallback_firecrawl.py`

## Tasks
- [x] Criar spec TASK-115
- [ ] RED: escrever `tests/test_issue115_no_firecrawl_fallback.py` (falham com código atual)
- [ ] GREEN: atualizar `app/scrapers/aliexpress.py` (remover Firecrawl)
- [ ] REFACTOR: remover/atualizar testes obsoletos que testavam Firecrawl sendo chamado
- [ ] Verify: `pytest tests/ -x -v` verde

## Critérios de Verificação
- `pytest tests/ -x -v` passa (205+ testes)
- `get_hot_products()` nunca chama `get_products_via_firecrawl`, independente de `SCRAPER_MODE` ou `FIRECRAWL_URL`
- `SCRAPER_MODE=firecrawl` com `FIRECRAWL_URL` setado → crawl4ai é chamado, não Firecrawl
- crawl4ai retorna `[]` com `FIRECRAWL_URL` setado → resultado é `[]`, Firecrawl não é chamado
