# TASK-003 scorer de viabilidade ZDailyScan

## Objetivo
Calcular score composto de viabilidade de importação para cada produto combinando
margem, demanda BR, oportunidade competitiva, tendência e compatibilidade logística.

## Pacote / Módulo
`app/scoring/__init__.py` + `app/scoring/scorer.py`

## Contratos

```python
class AliProduct(BaseModel):
    product_id: str
    title: str

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

def score_product(ali: AliProduct, market: BRMarket, cost: ImportCost) -> ProductScore: ...
```

## Fórmula
```
score = 0.30×Margem + 0.25×Demanda_BR + 0.20×Oportunidade + 0.15×Tendencia + 0.10×Logistica
```

### Dimensões (0.0 → 1.0)
- Margem: `(avg_price_brl - total_cost_brl) / avg_price_brl`, clamp [0, 1]
- Demanda_BR: `min(result_count / 100, 1.0)`
- Oportunidade: `1 - min(result_count / 500, 1.0)`
- Tendência: `0.5` fixo (Google Trends em v0.2.0)
- Logística: `1.0` se `price_usd ≤ 50`, `0.6` se `price_usd ≤ 100`, `0.3` acima
- `sell_price_suggestion_brl = total_cost_brl * 2.5`

## Tasks
- [x] Escrever tests/test_scorer.py (fase RED)
- [x] Criar app/scoring/__init__.py
- [x] Implementar app/scoring/scorer.py (fase GREEN)
- [x] Verificar pytest tests/test_scorer.py -v (fase VERIFY)

## Critérios de Verificação
```bash
pytest tests/test_scorer.py -v
# PASSED tests/test_scorer.py::test_viable_product_score
# PASSED tests/test_scorer.py::test_unviable_product_score
# PASSED tests/test_scorer.py::test_score_bounds
```
