# [TASK-040] fix: /scan/trigger retorna JSON bruto ao invés de redirecionar

## Objetivo
POST /dashboard/scan/trigger deve redirecionar o browser para /dashboard/scanner (303 See Other)
em vez de retornar JSON bruto — o form HTML faz POST normal, não AJAX.

## Pacote / Módulo
`app/routers/dashboard.py` → função `dashboard_scan_trigger()`

## Contratos

```python
# Antes (bugado):
return {"status": "started", "scan_id": scan_id}

# Depois (correto):
return RedirectResponse(url="/dashboard/scanner", status_code=303)
# RedirectResponse já importado na linha 8
```

## Detalhes de Implementação
- Trocar o `return {"status": "started", ...}` por `RedirectResponse(url="/dashboard/scanner", status_code=303)`
- Import já existe: `from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse`
- Atualizar testes em `tests/test_dashboard_phase2.py` que esperam `200 + JSON`

## Tasks
- [x] Criar spec
- [ ] RED: atualizar testes para esperar 303
- [ ] GREEN: implementar redirect
- [ ] VERIFY: suite completa passa

## Critérios de Verificação
```bash
pytest tests/ -x -q
ruff check . --select E,F,I
```
