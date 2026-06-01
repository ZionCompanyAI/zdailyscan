# [TASK-110] feat(analyzer): search_br_market_via_zoom — Zoom.com.br fallback quando ML API 403

## Objetivo
ML API (`api.mercadolibre.com/sites/MLB/search`) retorna 403 de todos os IPs (Railway e OC01).
Adicionar `search_br_market_via_zoom()` como fallback automático no `search_br_market()` quando ML falha.
Zoom.com.br retorna HTTP 200 e tem `__NEXT_DATA__` com preços reais em BRL.

## Pacote / Módulo
`app/analyzers/mercado_livre.py` — nova função + atualizar except de `search_br_market()`

## Contratos

```python
async def search_br_market_via_zoom(query: str) -> BRMarket:
    """Consulta Zoom.com.br via scraping __NEXT_DATA__ e retorna BRMarket com preços BRL.
    Retorna _not_found() em qualquer falha (HTTP, parse, dados vazios)."""

# BRMarket já existente — sem alteração
```

Estrutura `__NEXT_DATA__` verificada em 2026-06-01:
```
data["props"]["initialReduxState"]["hits"]["hits"]
  → list: {"price": int, "name": str, "url": str (relativo)}
Total de resultados: regex r"([\d.]+)\s+resultado" no HTML
```

## Detalhes de Implementação
- `httpx.AsyncClient(follow_redirects=True)` com headers User-Agent + Accept-Language pt-BR
- Regex `r'"__NEXT_DATA__"[^>]*>(.*?)</script>'` com `re.S` para extrair JSON
- `_not_found()` em qualquer exceção ou ausência de preços
- Timeout 20.0s
- Fallback em `search_br_market()`: substituir `return _not_found()` no except final por `return await search_br_market_via_zoom(query)`

## Tasks
- [x] Escrever tests/test_zoom_market.py (RED)
- [x] Implementar search_br_market_via_zoom() (GREEN)
- [x] Atualizar search_br_market() except final (GREEN)
- [x] REFACTOR se necessário
- [x] Verify (pytest suite)
- [x] Archive

## Critérios de Verificação
```bash
pytest tests/test_zoom_market.py -x -v
```
Ambos os testes devem passar (GREEN).
