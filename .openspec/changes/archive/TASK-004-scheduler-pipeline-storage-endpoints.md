---
# [TASK-004] Scheduler diário + pipeline + storage + endpoints /scan

## Objetivo
Orquestrar o scan completo diariamente às 06:00 BRT: AliExpress → analyzer → scorer para
todas as categorias, persistindo resultados em JSON e expondo endpoints REST.

## Pacote / Módulo
- `app/aliexpress.py` — cliente AliExpress Affiliate API
- `app/pipeline.py` — `run_daily_scan() -> ScanResult`
- `app/storage.py` — `save_scan`, `load_scan`, `get_latest_scan`
- `app/scheduler.py` — `AsyncIOScheduler` com cron `0 9 * * *` (UTC = 06:00 BRT)
- `app/main.py` — lifespan + endpoints GET /scan/latest, GET /scan/{date}, POST /scan/run

## Contratos

```python
# app/aliexpress.py
class AliExpressProduct(BaseModel):
    product_id: str
    title: str
    price_usd: float
    freight_usd: float = 5.0

async def get_hot_products(category_id: str, limit: int = 20) -> list[AliExpressProduct]: ...

# app/pipeline.py
CATEGORIES: list[str]  # 5 categorias AliExpress padrão

class ScanResult(BaseModel):
    scan_id: str
    date: str          # YYYY-MM-DD
    products: list[ProductScore]   # top 20 viáveis, score_total desc
    total_scanned: int
    total_viable: int

async def run_daily_scan(scan_id: str | None = None) -> ScanResult: ...

# app/storage.py
SCANS_DIR: Path  # data/scans/

def save_scan(result: ScanResult) -> Path: ...
def load_scan(date_str: str) -> ScanResult | None: ...
def get_latest_scan() -> ScanResult | None: ...
```

## Detalhes de Implementação
- `get_hot_products`: AliExpress Affiliate API (`aliexpress.affiliate.hotproduct.query`),
  lê `ALIEXPRESS_APP_KEY` / `ALIEXPRESS_APP_SECRET` via `os.environ`, retorna `[]` se ausentes
- `run_daily_scan`: itera `CATEGORIES`, chama `get_hot_products → search_br_market →
  calculate_import_cost → score_product`, filtra `viavel=True`, top-20 desc por `score_total`
- `save_scan`: cria `data/scans/YYYY-MM-DD.json` com `model_dump_json(indent=2)`
- `create_scheduler`: `AsyncIOScheduler`, job `_daily_scan_job` com `"cron", hour=9, minute=0`
- `POST /scan/run`: autenticação via header `x-api-key`, env `SCAN_API_KEY` (default `"test"`)
- `lifespan`: inicia/para scheduler no startup/shutdown do FastAPI

## Tasks
- [x] Spec criada
- [x] RED: tests/test_pipeline.py (3 testes obrigatórios)
- [x] GREEN: aliexpress.py + pipeline.py + storage.py + scheduler.py + main.py (lifespan + rotas)
- [x] REFACTOR: lint limpo
- [x] requirements.txt + pyproject.toml: APScheduler==3.10.4 adicionado
- [x] Verify: 18/18 PASSED + ruff clean

## Critérios de Verificação
```bash
pytest tests/test_pipeline.py -v
# PASSED test_pipeline_returns_top20
# PASSED test_results_sorted_by_score
# PASSED test_scan_persisted_to_json
```
- `POST /scan/run` com `x-api-key: test` → `{"status":"started","scan_id":"..."}`
- `GET /scan/latest` retorna ScanResult com products ordenados desc
- `GET /scan/{date}` retorna 404 para data inexistente
- Scheduler registrado no lifespan do FastAPI
