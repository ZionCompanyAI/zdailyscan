# [TASK-078] fix(settings): persistir cookies e categorias em Railway env vars

## Objetivo
Após salvar ALIEXPRESS_SESSION_COOKIES ou SCAN_CATEGORIES no settings, além de setar
`os.environ` (runtime), persistir a env var no serviço Railway via API GraphQL, para que o
valor sobreviva a redeploys.

## Pacote / Módulo
`app/routers/dashboard.py`:
- nova função `_persist_railway_env(key, value)` (async)
- chamada em `dashboard_settings_post` após setar `os.environ["ALIEXPRESS_SESSION_COOKIES"]`
- chamada em `dashboard_settings_categories` após setar `os.environ["SCAN_CATEGORIES"]`

## Contratos

```python
async def _persist_railway_env(key: str, value: str) -> None:
    """Persiste env var no serviço Railway via GraphQL. No-op se vars de config ausentes."""
    ...
```

Variáveis necessárias (já presentes no Railway como `${{...}}` referências):
- `RAILWAY_API_TOKEN`
- `RAILWAY_PROJECT_ID`
- `RAILWAY_ENVIRONMENT_ID`
- `RAILWAY_SERVICE_ID`

Se qualquer uma estiver ausente → função retorna sem erro (dev local sem Railway).

## Detalhes de Implementação
- `httpx.AsyncClient` para POST a `https://backboard.railway.app/graphql/v2`
- Header: `Authorization: Bearer <token>`
- Mutation: `variableCollectionUpsert` com `projectId`, `environmentId`, `serviceId`, `variables`
- Qualquer exceção HTTP → log warning, nunca propagar (não bloqueia o save)
- `await _persist_railway_env(...)` chamado após o `os.environ[...]` em ambos os endpoints

## Tasks
- [x] Escrever testes RED (test_issue78_persist_railway_env.py)
- [x] Implementar `_persist_railway_env` em dashboard.py
- [x] Chamar em `dashboard_settings_post`
- [x] Chamar em `dashboard_settings_categories`
- [x] Verify: pytest + ruff

## Critérios de Verificação
```bash
grep -q "_persist_railway_env\|variableCollectionUpsert" app/routers/dashboard.py
python3 -m pytest tests/ -x -q 2>&1 | tail -3
ruff check . --select I,E,F
```
