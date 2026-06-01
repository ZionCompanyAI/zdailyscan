# TASK-122 fix(scraper): injetar ALIEXPRESS_SESSION_COOKIES no BrowserConfig + remover wait_for explosivo

## Objetivo
Corrigir dois bugs em `_scrape_with_crawl4ai`:
1. `session_cookies` recebido mas nunca passado ao `BrowserConfig` → AliExpress bloqueia IP Railway
2. `wait_for="css:[data-item-id]"` lança `RuntimeError` após 45s de timeout sem catch → derruba scraper

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `_scrape_with_crawl4ai`

## Contratos

```python
async def _scrape_with_crawl4ai(
    category_id: str, max_results: int, session_cookies: str = ""
) -> list[AliProduct]:
    # Parsa session_cookies JSON → list[dict] → BrowserConfig(cookies=...)
    # Sem wait_for no CrawlerRunConfig
    # AsyncWebCrawler em try/except → return [] em falha
```

## Mudanças exatas (da spec da issue)

1. Parsear `session_cookies` JSON e passar como `cookies=` ao `BrowserConfig`
2. Remover `wait_for="css:[data-item-id]"` do `CrawlerRunConfig`
3. Envolver `AsyncWebCrawler` em try/except para falha graciosa

## Tasks

- [x] Criar testes RED (test_issue122_aliexpress_cookies_wait_for.py)
- [ ] Implementar fix em aliexpress.py (GREEN)
- [ ] REFACTOR + Verify

## Critérios de Verificação

1. `grep -n "wait_for" app/scrapers/aliexpress.py` → zero matches
2. `grep -n "cookies=cookies" app/scrapers/aliexpress.py` → 1 match
3. `grep -n "except Exception" app/scrapers/aliexpress.py` → ≥1 match no bloco do crawler
4. `python -c "import ast; ast.parse(open('app/scrapers/aliexpress.py').read()); print('OK')"` → OK
5. `pytest tests/ -x -q` → sem erros
