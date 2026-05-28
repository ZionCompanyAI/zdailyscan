# TASK-002 — Analyzer: Mercado Livre market check + import cost calculator

## Objetivo
Para cada produto encontrado no AliExpress, verificar existência e preço no Brasil via ML API,
e calcular custo total de importação considerando o regime tributário brasileiro.

## Pacote / Módulo
- `app/analyzers/mercado_livre.py` → `search_br_market(query: str) -> BRMarket`
- `app/analyzers/import_calculator.py` → `calculate_import_cost(price_usd, freight_usd) -> ImportCost`
- `app/config.py` → adicionar campo `usd_brl_rate: float` (default 5.70)

## Contratos

```python
# app/analyzers/mercado_livre.py
class BRMarket(BaseModel):
    found: bool
    avg_price_brl: float | None
    min_price_brl: float | None
    max_price_brl: float | None
    result_count: int
    top_listings: list[str]  # até 3 URLs

async def search_br_market(query: str) -> BRMarket: ...

# ML API endpoint: GET https://api.mercadolibre.com/sites/MLB/search?q=<query>&limit=10
```

```python
# app/analyzers/import_calculator.py
from typing import Literal

class ImportCost(BaseModel):
    price_usd: float
    freight_usd: float
    tax_brl: float
    total_cost_brl: float
    regime: Literal["remessa_conforme", "normal"]

def calculate_import_cost(price_usd: float, freight_usd: float) -> ImportCost: ...
```

## Detalhes de Implementação

### Mercado Livre
- GET `https://api.mercadolibre.com/sites/MLB/search?q={query}&limit=10` (sem autenticação)
- `found = result_count > 0`
- `avg_price_brl` = média dos preços retornados (campo `price`)
- `min_price_brl` / `max_price_brl` = min/max dos preços
- `top_listings` = até 3 URLs do campo `permalink`
- Usar `httpx.AsyncClient`

### Import Calculator
- `rate = settings.usd_brl_rate`
- `regime = "remessa_conforme"` se `(price_usd + freight_usd) <= 50`
- **Remessa Conforme**: `base_brl = (price_usd + freight_usd) * rate`; `ii = 0.20 * base_brl`; `icms = 0.17 * base_brl`
- **Normal**: `base_brl = (price_usd + freight_usd) * rate`; `ii = 0.60 * base_brl`; `icms = (base_brl + ii) * 0.17 / (1 - 0.17)` (ICMS por dentro)
- `tax_brl = ii + icms`; `total_cost_brl = base_brl + tax_brl`

## Tasks
- [x] Criar `.openspec/changes/TASK-002-...md` (spec)
- [x] Escrever `tests/test_analyzer.py` (RED)
- [x] Adicionar `usd_brl_rate` em `app/config.py`
- [x] Implementar `app/analyzers/__init__.py`
- [x] Implementar `app/analyzers/mercado_livre.py`
- [x] Implementar `app/analyzers/import_calculator.py`
- [x] Verificar suite completa passa (GREEN + REFACTOR)

## Critérios de Verificação
```bash
pytest tests/test_analyzer.py -v
# PASSED tests/test_analyzer.py::test_ml_search_returns_prices
# PASSED tests/test_analyzer.py::test_import_cost_remessa_conforme
# PASSED tests/test_analyzer.py::test_import_cost_normal_regime
```
