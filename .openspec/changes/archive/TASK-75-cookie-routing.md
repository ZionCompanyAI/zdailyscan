# [TASK-75] fix(scraper): usar crawl4ai quando session_cookies definido, firecrawl como fallback sem cookies

## Objetivo
`get_hot_products()` ignora ALIEXPRESS_SESSION_COOKIES ao rotear entre scrapers.
Quando cookies estão presentes, crawl4ai deve ser primário (suporta cookie injection).
Quando cookies ausentes, firecrawl deve ser usado diretamente (listagens públicas).

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `get_hot_products()`

## Contratos

```python
# Lógica nova — pseudocódigo
session_cookies = os.environ.get("ALIEXPRESS_SESSION_COOKIES", "")
if session_cookies:
    products = await _scrape_with_crawl4ai(category_id, max_results, session_cookies)
    if not products and firecrawl_url:
        products = await get_products_via_firecrawl(category_id, firecrawl_url, max_results)
else:
    if firecrawl_url:
        products = await get_products_via_firecrawl(category_id, firecrawl_url, max_results)
    else:
        products = []
```

## Tasks
- [x] Escrever testes RED para os 3 cenários novos
- [x] Implementar lógica de roteamento por cookies em get_hot_products()
- [x] Verificar que testes existentes continuam passando

## Critérios de Verificação
```bash
grep -q "ALIEXPRESS_SESSION_COOKIES" app/scrapers/aliexpress.py
grep -A5 "session_cookies" app/scrapers/aliexpress.py | grep -q "crawl4ai"
python3 -m pytest tests/ -x -q 2>&1 | tail -3
ruff check . --select I,E,F
```
