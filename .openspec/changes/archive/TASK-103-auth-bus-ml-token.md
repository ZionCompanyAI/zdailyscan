# [TASK-103] fix: search_br_market() deve usar auth-bus dinamicamente

## Objetivo
Substituir leitura estática de `ML_USER_ACCESS_TOKEN` por chamada dinâmica ao auth-bus,
garantindo que tokens expirados sejam renovados sem redeploy.

## Pacote / Módulo
`app/analyzers/mercado_livre.py` → nova função `get_ml_token()` + refatorar `search_br_market()`

## Contratos

```python
async def get_ml_token() -> str:
    """Tenta auth-bus; fallback para ML_USER_ACCESS_TOKEN env var."""
    bus_url = os.environ.get("AUTH_BUS_URL", "")
    bus_key = os.environ.get("AUTH_BUS_API_KEY", "")
    if bus_url and bus_key:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{bus_url}/tokens/mercadolibre",
                    headers={"x-api-key": bus_key, "User-Agent": "zdailyscan/1.0"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("access_token", "")
        except Exception:
            pass
    return os.environ.get("ML_USER_ACCESS_TOKEN", "")

async def search_br_market(query: str) -> BRMarket:
    token = await get_ml_token()  # <- dinâmico
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    ...
```

## Env vars
- `AUTH_BUS_URL` — URL base do auth-bus (já configurado no Railway)
- `AUTH_BUS_API_KEY` — chave de acesso (já configurado)
- `ML_USER_ACCESS_TOKEN` — mantido como fallback

## Tasks
- [x] Criar `get_ml_token()` em `app/analyzers/mercado_livre.py`
- [x] Refatorar `search_br_market()` para `await get_ml_token()`
- [x] Atualizar testes existentes (test_issue87) que mockam env var direto
- [x] Escrever `tests/test_issue103_auth_bus_ml_token.py`

## Critérios de Verificação
- Auth-bus retorna token → header `Authorization: Bearer <token>` na chamada ML
- Auth-bus indisponível (exception) → fallback para `ML_USER_ACCESS_TOKEN`
- Auth-bus retorna non-200 → fallback para `ML_USER_ACCESS_TOKEN`
- Nenhum token disponível → sem header Authorization (chamada public API)
