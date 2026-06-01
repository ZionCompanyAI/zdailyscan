# [TASK-139] Scrapling como modo de scraper (substitui Firecrawl sem custos)

## Objetivo
Adicionar `SCRAPER_MODE=scrapling` usando a lib open-source Scrapling com StealthyFetcher
(HTTP puro, anti-bot evasion, sem browser, sem custos). Firecrawl esgotou créditos (402).
Adicionar fallback automático firecrawl→scrapling quando Firecrawl retorna 402.

## Pacote / Módulo
- `requirements.txt` — nova dependência `scrapling[fetchers]`
- `app/scrapers/aliexpress.py` — função `_scrape_with_scrapling()` + dispatcher + 402 fallback

## Contratos (Referências Técnicas)

```python
# Assinatura nova função
async def _scrape_with_scrapling(
    category_id: str, max_results: int, keyword: str = ""
) -> list[AliProduct]:
    """Scrapling StealthyFetcher: HTTP puro, sem browser. Síncrono em thread separada."""
```

```python
# Dispatcher — get_hot_products() — novo branch
elif mode == "scrapling":
    products = await _scrape_with_scrapling(category_id, max_results, keyword=keyword)
```

```python
# Fallback em _scrape_with_firecrawl — quando 402
# Ajuste: _scrape_with_firecrawl() deve propagar o status para que o dispatcher faça fallback
# OU: get_hot_products() trata a exceção internamente
# Decisão: tratar no dispatcher em get_hot_products() com try/except em _scrape_with_firecrawl
```

## Detalhes de Implementação
- `StealthyFetcher.fetch()` é **síncrono** → usar `asyncio.to_thread()` para não bloquear event loop
- CSS selectors: `.search-item-card-wrapper-gallery`, `[class*=search-item-card]`, `[class*=item-title]`, `[class*=price]`, `a::attr(href)`, `img::attr(src)` ou `img::attr(lazy-src)`
- Se `page.css(...)` retornar 0 cards: logger.warning + return []
- Fallback 402: detectar pela string "402" ou "Payment" na exceção de _scrape_with_firecrawl
- `_scrape_with_firecrawl` deve propagar exceção 402 → `get_hot_products` captura e chama scrapling

## Tasks (checklist de execução)
- [x] Adicionar `scrapling[fetchers]` ao requirements.txt
- [x] Implementar `_scrape_with_scrapling()` com asyncio.to_thread + CSS extraction
- [x] Adicionar branch `scrapling` no dispatcher `get_hot_products()`
- [x] Adicionar fallback 402 firecrawl→scrapling em `get_hot_products()`
- [x] Escrever testes (RED antes da implementação)

## Critérios de Verificação
- `pytest tests/test_issue139_scrapling.py -x` → PASSED
- `pytest tests/ -x` → suite completa sem regressões
- `ruff check app/scrapers/aliexpress.py` → sem erros
