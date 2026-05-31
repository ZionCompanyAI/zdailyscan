# [TASK-091] fix: increase Firecrawl httpx timeout

## Objetivo
Corrigir `product_count: 0` em todos os scans. Causa raiz: `httpx.AsyncClient.post(timeout=60.0)` expira quando o cache do Firecrawl está frio (páginas AliExpress demoram >60s). `httpx.TimeoutException` tem `str()` vazio, então os logs mostram "scraper failed for category X: " sem nada após os dois-pontos.

## Pacote / Módulo
- `app/scrapers/fallback_firecrawl.py` → função `get_products_via_firecrawl()`
- `app/pipeline.py` → `run_daily_scan()` warning logger

## Contratos (Referências Técnicas)

```python
# fallback_firecrawl.py — ANTES
resp = await client.post(..., json={...}, timeout=60.0)

# fallback_firecrawl.py — DEPOIS
resp = await client.post(
    ...,
    json={..., "timeout": 150000},  # Firecrawl-side timeout em ms
    timeout=180.0,
)

# pipeline.py — ANTES
logger.warning("scraper failed for category %s: %s", category_id, exc)

# pipeline.py — DEPOIS
logger.warning("scraper failed for category %s: %r", category_id, exc)
```

## Tasks (checklist de execução)
- [x] Criar testes RED (tests/test_issue91_firecrawl_timeout.py)
- [x] Mudar timeout=60.0 → timeout=180.0 em fallback_firecrawl.py
- [x] Adicionar "timeout": 150000 ao body JSON em fallback_firecrawl.py
- [x] Mudar %s → %r no logger de pipeline.py
- [x] Verify: ruff + pytest

## Critérios de Verificação
```bash
grep -q timeout=180 app/scrapers/fallback_firecrawl.py
grep -q 150000 app/scrapers/fallback_firecrawl.py
```
