# TASK-167 fix: ScanResult.status None + /scan/run não atualiza _scan_status

## Objetivo
Relatório não aparece na console após scan completar porque:
1. `ScanResult` não tem campo `status` → `/scan/latest` retorna `status: null`
2. `POST /scan/run` usa `_do_scan` local que nunca atualiza `_scan_status` no dashboard → polling retorna 404

## Pacote / Módulo
- `app/pipeline.py` → classe `ScanResult`
- `app/main.py` → endpoint `POST /scan/run`

## Contratos

```python
# pipeline.py — ScanResult com status
class ScanResult(BaseModel):
    scan_id: str
    date: str
    status: str = "completed"   # NOVO campo
    products: list[ProductScore]
    total_scanned: int
    total_viable: int
```

```python
# main.py — scan_run reusa _run_scan_background do dashboard
@app.post("/scan/run")
async def scan_run(
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(...),
) -> dict:
    ...
    scan_id = str(uuid.uuid4())
    background_tasks.add_task(dashboard._run_scan_background, scan_id)
    return {"status": "started", "scan_id": scan_id}
```

## Tasks
- [x] TASK-167a: Adicionar `status: str = "completed"` ao `ScanResult`
- [x] TASK-167b: Substituir `_do_scan` local em `/scan/run` por `dashboard._run_scan_background`

## Critérios de Verificação
```bash
# ScanResult.status == "completed" por default
curl -sf /scan/latest | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='completed'"
# _scan_status[scan_id] atualizado após POST /scan/run
# GET /dashboard/scan/{scan_id}/status retorna completed
```
