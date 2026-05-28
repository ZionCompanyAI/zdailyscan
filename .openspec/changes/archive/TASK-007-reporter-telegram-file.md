# [TASK-007] Report diário — Top 10 via Telegram + arquivo Markdown

## Objetivo
Após cada scan diário, enviar relatório com as top 10 oportunidades para Toni via Telegram
usando o endpoint `/telegram/reply` do Mission Control, e salvar cópia local em Markdown.

## Pacote / Módulo
- `app/reporters/telegram_reporter.py` → `send_daily_report(results: list[ProductScore]) -> bool`
- `app/reporters/file_reporter.py` → `save_daily_report(results: list[ProductScore], reports_dir: Path) -> Path`
- `app/scoring/scorer.py` → adicionar `demand_count: int` e `import_cost_brl: float` em `ProductScore`
- `app/pipeline.py` → chamar reporters no final de `run_daily_scan()`

## Contratos

```python
# telegram_reporter.py
async def send_daily_report(results: list[ProductScore]) -> bool:
    """Envia top 10 via POST $MC_URL/telegram/reply. Retorna True em 200, False em falha."""

# file_reporter.py
def save_daily_report(results: list[ProductScore], reports_dir: Path = REPORTS_DIR) -> Path:
    """Salva top 10 em data/reports/YYYY-MM-DD.md. Retorna Path do arquivo."""
```

```python
# ProductScore — novos campos (com default para não quebrar testes existentes)
class ProductScore(BaseModel):
    ...
    demand_count: int = 0        # market.result_count
    import_cost_brl: float = 0.0 # cost.total_cost_brl
```

## Formato da mensagem Telegram
```
🛒 ZDailyScan — 2026-05-27
Top 10 oportunidades AliExpress → LojaHi Select

1. [Nome do produto] ⭐ score: 0.82
   💰 Custo importação: R$ 45,00
   🏷️ Sugestão de venda: R$ 112,50
   📦 Demanda ML: 234 anúncios
   🔗 https://www.aliexpress.com/item/{product_id}.html
```

## Tasks

- [x] Adicionar `demand_count` e `import_cost_brl` em `ProductScore`
- [x] Atualizar `score_product()` para popular os novos campos
- [x] Criar `app/reporters/__init__.py`
- [x] Criar `app/reporters/telegram_reporter.py`
- [x] Criar `app/reporters/file_reporter.py`
- [x] Integrar reporters no final de `pipeline.run_daily_scan()` com try/except
- [x] Escrever `tests/test_reporter.py`

## Critérios de Verificação
```bash
pytest tests/test_reporter.py -v
# PASSED tests/test_reporter.py::test_report_format_contains_required_fields
# PASSED tests/test_reporter.py::test_mc_failure_does_not_raise
# PASSED tests/test_reporter.py::test_file_report_saved
```
