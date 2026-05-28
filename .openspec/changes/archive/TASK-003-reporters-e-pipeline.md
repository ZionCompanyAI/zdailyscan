# [TASK-003] Reporters diários — Telegram + arquivo Markdown

## Objetivo
Após cada scan diário, enviar as top 10 oportunidades via Telegram (Mission Control)
e salvar o relatório em arquivo Markdown local. Integrar ao pipeline principal.

## Pacote / Módulo
- `app/models.py` → `ProductScore`
- `app/reporters/__init__.py` → pacote vazio
- `app/reporters/telegram_reporter.py` → `send_daily_report()`
- `app/reporters/file_reporter.py` → `save_daily_report()`
- `app/pipeline.py` → `run_daily_scan()` (stub com integração dos reporters)
- `tests/test_reporter.py` → 3 testes obrigatórios

## Contratos (Referências Técnicas)

```python
# app/models.py
from pydantic import BaseModel

class ProductScore(BaseModel):
    name: str
    score: float
    import_cost_brl: float
    suggested_price_brl: float
    ml_listing_count: int
    aliexpress_url: str

# app/reporters/telegram_reporter.py
async def send_daily_report(results: list[ProductScore]) -> bool:
    """Envia top 10 via POST MC_URL/telegram/reply. Retorna True se HTTP 200."""

# app/reporters/file_reporter.py
def save_daily_report(results: list[ProductScore], report_date: date | None = None) -> Path:
    """Salva relatório em data/reports/YYYY-MM-DD.md. Retorna o Path."""

# app/pipeline.py
async def run_daily_scan() -> list[ProductScore]:
    """Orquestra scan e dispara reporters. Stub retorna lista vazia por ora."""
```

## Detalhes de Implementação
- `send_daily_report` usa `httpx.AsyncClient` para POST em `{settings.mc_url}/telegram/reply`
  com header `x-api-key: {settings.mc_api_key}` e body `{"chat_id": 7041182277, "text": "<msg>"}`
- Formato Markdown da mensagem conforme issue #6 (emoji + nome + score + custo + sugestão + demanda + link)
- Recorta para top 10 internamente (`results[:10]`)
- Em falha (timeout, status 5xx), faz `logging.error(...)` e retorna `False` — não levanta exceção
- `save_daily_report` cria `data/reports/` se não existir; nome do arquivo = `YYYY-MM-DD.md`
- `pipeline.run_daily_scan` chama ambos os reporters no final (fire-and-forget adequado ao scan)

## Tasks
- [x] Criar `app/models.py` com `ProductScore`
- [x] Criar `app/reporters/__init__.py`
- [x] Criar `app/reporters/telegram_reporter.py` com `send_daily_report()`
- [x] Criar `app/reporters/file_reporter.py` com `save_daily_report()`
- [x] Criar `app/pipeline.py` com `run_daily_scan()`
- [x] Criar `tests/test_reporter.py` com os 3 testes obrigatórios

## Critérios de Verificação
```
pytest tests/test_reporter.py -v
# PASSED tests/test_reporter.py::test_report_format_contains_required_fields
# PASSED tests/test_reporter.py::test_mc_failure_does_not_raise
# PASSED tests/test_reporter.py::test_file_report_saved
```
