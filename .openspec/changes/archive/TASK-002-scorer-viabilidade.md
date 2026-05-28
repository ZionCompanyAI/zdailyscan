---
name: TASK-002-scorer-viabilidade
description: Scorer de viabilidade de importação — score composto 5 dimensões
type: project
---

# [TASK-002] Scorer de viabilidade ZDailyScan — score composto por produto

## Objetivo
Calcular o score de viabilidade de importação para cada produto, combinando
margem, demanda BR, oportunidade competitiva, tendência Google Trends e
compatibilidade logística.

## Pacote / Módulo
- `app/models.py` → `AliProduct`, `BRMarket`, `ImportCost`, `ProductScore`
- `app/scoring/__init__.py` → pacote
- `app/scoring/scorer.py` → `score_product(ali, market, cost) -> ProductScore`
- `tests/test_scorer.py` → suíte obrigatória

## Contratos

```python
# app/models.py
class AliProduct(BaseModel):
    product_id: str
    title: str
    price_usd: float

class BRMarket(BaseModel):
    avg_price_brl: float
    result_count: int

class ImportCost(BaseModel):
    total_cost_brl: float  # produto + frete + impostos

class ProductScore(BaseModel):
    product_id: str
    title: str
    score_total: float
    score_margem: float
    score_demanda_br: float
    score_oportunidade: float
    score_tendencia: float
    score_logistica: float
    margin_brl: float
    sell_price_suggestion_brl: float
    viavel: bool  # score_total >= 0.60
```

```python
# app/scoring/scorer.py
def score_product(ali: AliProduct, market: BRMarket, cost: ImportCost) -> ProductScore: ...
```

## Fórmula
```
score = 0.30×Margem + 0.25×Demanda_BR + 0.20×Oportunidade + 0.15×Tendencia + 0.10×Logistica
```

- Margem: `max(0, (avg_price_brl - total_cost_brl) / avg_price_brl)` clamp 0→1
- Demanda_BR: `min(result_count / 100, 1.0)`
- Oportunidade: `1 - min(result_count / 500, 1.0)`
- Tendência: `0.5` fixo (v0.1.0)
- Logística: `1.0` se `price_usd ≤ 50`, `0.6` se `price_usd ≤ 100`, `0.3` acima
- `sell_price_suggestion_brl = total_cost_brl * 2.5`
- `viavel = score_total >= 0.60`

## Tasks
- [x] Fase RED: escrever tests/test_scorer.py — deve FALHAR
- [x] Fase GREEN: implementar app/models.py + app/scoring/scorer.py
- [x] Fase REFACTOR: limpar, garantir verde
- [x] Verify: pytest tests/ 9/9 ✅
- [x] Archive

## Critérios de Verificação (issue #4)
- `avg_price_brl=150`, `total_cost_brl=40`, `result_count=80` → `viavel=True`
- `avg_price_brl=45`, `total_cost_brl=42`, `result_count=800` → `viavel=False`
- `score_total` sempre entre 0.0 e 1.0
- `pytest tests/test_scorer.py -v` passa
