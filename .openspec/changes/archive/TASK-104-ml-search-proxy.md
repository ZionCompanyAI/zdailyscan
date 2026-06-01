# [TASK-104] fix(analyzer) — ML search proxiada via ML_SEARCH_PROXY_URL (PolicyAgent block)

## Objetivo
Quando containers Railway recebem 403 `PA_UNAUTHORIZED_RESULT_FROM_POLICIES` da API de search ML,
rotear a chamada através de uma URL de proxy configurável (`ML_SEARCH_PROXY_URL`).

## Pacote / Módulo
`app/analyzers/mercado_livre.py` → função `search_br_market()`

## Contratos

```python
# Env vars
ML_SEARCH_PROXY_URL: str  # opcional — quando set, usada como URL base do search
# Exemplo: "https://toni-oc01.example.com/ml-proxy/search"
#          "https://orchestrator.zioncompanyai.com.br/ml-search"

# Comportamento de search_br_market():
# 1. Tenta proxy (ML_SEARCH_PROXY_URL) se configurado
#    GET {proxy_url}?q={query}&limit={limit}
#    Headers: Authorization: Bearer {token}  (se token disponível)
#    Resposta esperada: mesmo shape do ML API → {"results": [...], "paging": {"total": N}}
# 2. Se proxy falhar (exception ou non-2xx), loga warning → tenta ML API direto
# 3. Se ML API direto retornar 403, loga warning → retorna BRMarket(found=False, ...)
# 4. Se ML_SEARCH_PROXY_URL não configurado → comportamento atual (direto)
```

## Tasks
- [x] Escrever testes RED (test_issue104_ml_search_proxy.py)
- [x] Implementar lógica proxy em search_br_market() (GREEN)
- [x] Refactor + verificar suite completa (REFACTOR)
- [x] Archive

## Critérios de Verificação
- Quando `ML_SEARCH_PROXY_URL` configurado → chamada vai ao proxy, não direto ao ML
- Quando proxy falha → fallback para ML direto (sem exceção propagada)
- Quando ML retorna 403 → BRMarket(found=False), sem exceção
- Quando `ML_SEARCH_PROXY_URL` ausente → comportamento idêntico ao anterior
