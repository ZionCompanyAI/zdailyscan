# [TASK-096] Auth-bus integration — ML_USER_ACCESS_TOKEN auto-renewal

## Objetivo
Antes de cada scan, buscar um token ML fresco do auth-bus em vez de usar a env var
estática ML_USER_ACCESS_TOKEN (que expira em ~24h), eliminando os 403s que zeram
total_viable mesmo com produtos válidos do AliExpress.

## Pacote / Módulo
- `app/analyzers/mercado_livre.py` → nova função `get_ml_token()` + atualizar `search_br_market()`
- `app/pipeline.py` → chamar `get_ml_token()` uma vez no início de `run_daily_scan()`

## Contratos

```python
AUTH_BUS_URL = os.environ.get("AUTH_BUS_URL", "")
AUTH_BUS_API_KEY = os.environ.get("AUTH_BUS_API_KEY", "")

async def get_ml_token() -> str:
    """Retorna token ML fresco do auth-bus, ou fallback para env var estática."""
    if AUTH_BUS_URL and AUTH_BUS_API_KEY:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{AUTH_BUS_URL}/tokens/mercadolibre",
                headers={
                    "x-api-key": AUTH_BUS_API_KEY,
                    "User-Agent": "zdailyscan/1.0",
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json().get("access_token", "")
    return os.environ.get("ML_USER_ACCESS_TOKEN", "")

async def search_br_market(query: str, ml_token: str = "") -> BRMarket:
    headers = {}
    if ml_token:
        headers["Authorization"] = f"Bearer {ml_token}"
    ...
```

## Detalhes de Implementação
- `get_ml_token()` chamado UMA VEZ por scan (no início do pipeline)
- Token passado para todas as chamadas `search_br_market()` daquele scan
- Fallback para `ML_USER_ACCESS_TOKEN` env var se auth-bus não configurado
- `User-Agent: zdailyscan/1.0` obrigatório — WAF bloqueia `Python-urllib/*`
- `x-api-key` header obrigatório para autenticação no auth-bus
- Novas env vars: `AUTH_BUS_URL` e `AUTH_BUS_API_KEY`

## Tasks
- [x] Criar TASK-096 spec
- [x] Escrever testes RED
- [x] Criar `get_ml_token()` em `app/analyzers/mercado_livre.py`
- [x] Atualizar `search_br_market()` para aceitar `ml_token` como parâmetro
- [x] Atualizar `app/pipeline.py`: chamar `get_ml_token()` e passar token
- [x] Atualizar `.env.example` com AUTH_BUS_URL e AUTH_BUS_API_KEY
- [x] Archive spec

## Critérios de Verificação
- `get_ml_token()` retorna `access_token` do auth-bus quando configurado
- Fallback para env var quando auth-bus não configurado ou retorna não-200
- `User-Agent: zdailyscan/1.0` enviado ao auth-bus
- `search_br_market()` aceita `ml_token` e usa como Authorization header
- Pipeline chama `get_ml_token()` uma vez e passa para cada `search_br_market()`
