# [TASK-046] AliExpress login credentials na página Settings

## Objetivo
Permitir configurar usuário/senha do AliExpress pela interface Settings para que o crawl4ai possa autenticar antes de scraper, acessando preços e dados reais.

## Pacote / Módulo
- `app/config.py` — campos `aliexpress_username`, `aliexpress_password` + Railway vars opcionais
- `app/routers/dashboard.py` — endpoint POST `/settings/aliexpress` + pass vars para template
- `app/templates/settings.html` — card AliExpress com form de credenciais
- `app/scrapers/aliexpress.py` — lê credenciais e autentica antes de scraper

## Contratos

```python
# app/config.py — adicionado ao Settings
aliexpress_username: str = ""
aliexpress_password: str = ""
railway_api_token: str = ""
railway_service_id: str = ""
railway_environment_id: str = ""
railway_project_id: str = ""

# app/routers/dashboard.py — novo endpoint
@router.post("/settings/aliexpress")
async def dashboard_settings_aliexpress(
    request: Request,
    aliexpress_username: str = Form(default=""),
    aliexpress_password: str = Form(default=""),
) -> RedirectResponse:
    """Salva credenciais em os.environ e persiste no Railway."""

# Helper Railway
async def _persist_railway_var(name: str, value: str) -> None:
    """Chama Railway GraphQL variableUpsert. No-op se token ausente."""

# Template context adicionado ao GET /settings
{
    "aliexpress_username": settings.aliexpress_username,
    "aliexpress_password_masked": _mask(settings.aliexpress_password),
}

# app/scrapers/aliexpress.py — _scrape_with_crawl4ai
aliexpress_username = os.environ.get("ALIEXPRESS_USERNAME", "")
aliexpress_password = os.environ.get("ALIEXPRESS_PASSWORD", "")
async with AsyncWebCrawler(config=browser_config) as crawler:
    if aliexpress_username and aliexpress_password:
        await crawler.authenticate(
            url="https://www.aliexpress.com/login.htm",
            username=aliexpress_username,
            password=aliexpress_password,
        )
    result = await crawler.arun(url=url, config=run_config)
```

## Detalhes de Implementação
- Credenciais armazenadas SOMENTE como Railway env vars — não em DB
- `os.environ` atualizado na sessão atual; Railway API persiste entre deploys
- Railway API: `POST https://backboard.railway.app/graphql/v2` com mutation `variableUpsert`
- Variáveis Railway disponíveis via env auto-inject no container: `RAILWAY_SERVICE_ID`, `RAILWAY_ENVIRONMENT_ID`, `RAILWAY_PROJECT_ID`
- `RAILWAY_API_TOKEN` deve ser configurado manualmente — não auto-injetado
- Se Railway vars não configuradas, endpoint salva apenas em os.environ (sem falha)
- Senha NUNCA em plaintext na UI — usar `_mask()` existente como placeholder
- Campo senha com `type="password"` no HTML

## Tasks
- [x] Criar spec TASK-046
- [x] Escrever testes (RED)
- [x] Implementar config.py
- [x] Implementar dashboard.py (GET settings + POST /settings/aliexpress)
- [x] Implementar settings.html
- [x] Implementar scrapers/aliexpress.py
- [x] Verify (suite completa — 151 passed)
- [x] Archive

## Critérios de Verificação
```bash
# POST /settings/aliexpress com auth → 303
# GET /settings mostra username, password como "****"
# os.environ["ALIEXPRESS_USERNAME"] atualizado após POST
# pytest tests/ -k "test_settings_aliexpress" → PASSED
```
