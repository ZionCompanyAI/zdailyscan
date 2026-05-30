# [TASK-081] fix(scraper): min_rating regrediu para 4.9 — deve ser 0.0

## Objetivo
PR #77 regrediu o fix do PR #71. `get_hot_products()` tem `min_rating: float = 4.9`
mas Firecrawl retorna produtos sem campo rating (rating=0.0 por padrão).
Todos os produtos são filtrados. Corrigir default para `0.0`.

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `get_hot_products()`

## Contratos

```python
async def get_hot_products(
    category_id: str, min_rating: float = 0.0, max_results: int = 100
) -> list[AliProduct]:
    ...
```

## Detalhes de Implementação
- Apenas mudar o default de `4.9` para `0.0` na assinatura de `get_hot_products`.
- Chamadores que precisam filtrar por rating podem passar `min_rating` explicitamente.

## Tasks
- [x] Escrever RED test (test_issue81_min_rating_regression.py)
- [x] Aplicar fix (min_rating: float = 0.0)
- [x] Verificar grep criterion + suite completa

## Critérios de Verificação
```bash
grep -q "min_rating: float = 0.0" app/scrapers/aliexpress.py
python3 -m pytest tests/ -x -q 2>&1 | tail -3
ruff check . --select I,E,F
```
