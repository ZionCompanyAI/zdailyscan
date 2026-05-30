# [TASK-072] feat(scraper): AliExpress session cookie injection

## Objetivo
Substituir username/password do AliExpress por cookie session injection, pois contas Google OAuth não suportam autenticação por senha. Crawl4AI receberá os cookies diretamente para scraping autenticado.

## Pacote / Módulo
- `app/config.py` — remover username/password, adicionar aliexpress_session_cookies
- `app/routers/dashboard.py` — GET/POST settings com SESSION_COOKIES
- `app/templates/settings.html` — substituir card de credentials por session cookies
- `app/scrapers/aliexpress.py` — injetar cookies no arun() do Crawl4AI

## Contratos

```python
# config.py
class Settings(BaseSettings):
    aliexpress_session_cookies: str | None = None  # JSON flat dict
    # aliexpress_username e aliexpress_password removidos

# dashboard.py GET
"aliexpress_cookies_set": bool(settings.aliexpress_session_cookies)

# dashboard.py POST
@router.post("/settings")
async def dashboard_settings_post(
    aliexpress_session_cookies: str = Form(default=""),
): ...

# scrapers/aliexpress.py
cookies_raw = os.getenv("ALIEXPRESS_SESSION_COOKIES", "{}")
cookies: dict = json.loads(cookies_raw) if cookies_raw else {}
result = await crawler.arun(url=url, config=run_config, cookies=cookies)
```

## Tasks (checklist de execução)
- [x] RED: escrever testes em tests/test_issue72_session_cookies.py
- [x] GREEN: implementar mudanças nos 4 arquivos
- [x] REFACTOR: atualizar test_issue57 para remover testes de USERNAME/PASSWORD quebrados
- [x] Verify: pytest + ruff passam

## Critérios de Verificação
```bash
grep -q "SESSION_COOKIES\|session_cookies" app/templates/settings.html
grep -q "SESSION_COOKIES\|session_cookies" app/scrapers/aliexpress.py
grep -q "SESSION_COOKIES\|session_cookies" app/routers/dashboard.py
ruff check app/ --select I,E,F
pytest tests/ -x -q
```
