# [TASK-124] fix(scraper): adicionar domain e path nos cookies AliExpress

## Objetivo
Playwright rejeita cookies sem `url` ou `domain`+`path`. Os cookies em
`ALIEXPRESS_SESSION_COOKIES` têm apenas `name` e `value`, causando:
`BrowserContext.add_cookies: Cookie should have a url or a domain/path pair`

## Arquivo
`app/scrapers/aliexpress.py` → função `_scrape_with_crawl4ai`, bloco de parse de cookies (linhas 51–56)

## Contratos

```python
# ANTES
cookies: list[dict] = []
if session_cookies:
    try:
        cookies = _json.loads(session_cookies)
    except Exception:
        pass

# DEPOIS
cookies: list[dict] = []
if session_cookies:
    try:
        raw = _json.loads(session_cookies)
        for c in raw:
            cookies.append({
                **c,
                "domain": c.get("domain", ".aliexpress.com"),
                "path": c.get("path", "/"),
            })
    except Exception:
        pass
```

## Tasks
- [ ] Escrever testes RED (test_issue124_cookie_domain_path.py)
- [ ] Aplicar fix no bloco de cookies (GREEN)
- [ ] Verificar suite completa (REFACTOR/Verify)

## Critérios de Verificação
1. `grep -n "\.aliexpress\.com" app/scrapers/aliexpress.py` → 1 match no bloco de cookies
2. `grep -n "domain.*aliexpress\|aliexpress.*domain" app/scrapers/aliexpress.py` → ao menos 1 match
3. `python -c "import ast; ast.parse(open('app/scrapers/aliexpress.py').read()); print('OK')"` → OK
4. `pytest tests/ -x -q` → sem erros
5. Todos os outros campos do BrowserConfig/CrawlerRunConfig intactos
