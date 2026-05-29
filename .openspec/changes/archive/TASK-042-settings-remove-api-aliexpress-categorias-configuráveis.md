# [TASK-042] Settings — remover API AliExpress, categorias configuráveis, card crawl4ai

## Objetivo
1. Remover card "AliExpress API" (app_key, app_secret, tracking_id) do settings — não usamos API, usamos crawl4ai.
2. Substituir lista estática de categorias por form com checkboxes que persiste em `SCAN_CATEGORIES` env var.
3. Adicionar card informativo "Crawl4AI" mostrando SCRAPER_MODE e categorias ativas.
4. Pipeline lê `SCAN_CATEGORIES` do env (comma-separated IDs) com fallback nas 5 categorias padrão.

## Pacote / Módulo
- `app/templates/settings.html` — UI
- `app/routers/dashboard.py` — endpoint POST + contexto GET /settings
- `app/pipeline.py` — leitura de SCAN_CATEGORIES com fallback

## Contratos

```python
# dashboard.py — novo endpoint
@router.post("/settings/categories")
async def dashboard_settings_categories(request: Request, categories: list[str] = Form([])):
    """Salva categorias ativas em os.environ['SCAN_CATEGORIES'] e redireciona para /dashboard/settings."""
    ...
    return RedirectResponse(url="/dashboard/settings", status_code=303)

# pipeline.py — função auxiliar
def get_active_categories() -> list[str]:
    """Retorna IDs de categorias ativas; lê SCAN_CATEGORIES do env ou usa padrão."""
    raw = os.environ.get("SCAN_CATEGORIES", "")
    if not raw.strip():
        return CATEGORIES  # 5 padrões
    valid = {c for c in CATEGORIES}  # aceita apenas IDs conhecidos
    return [c for c in raw.split(",") if c.strip() in valid] or CATEGORIES
```

## Detalhes de Implementação
- Remover campos `aliexpress_app_key_masked` e `aliexpress_tracking_id` do contexto de `dashboard_settings`
- O card "Crawl4AI" mostra: `SCRAPER_MODE` (env var) + lista de categorias ativas (nomes + IDs)
- Form de categorias: checkboxes com `name="categories"` (multiple), POST para `/dashboard/settings/categories`
- Usar `Form(...)` do FastAPI para receber lista de valores do form HTML
- Após save: `os.environ["SCAN_CATEGORIES"] = ",".join(categories_selecionadas)`, redirect 303

## Tasks
- [x] Criar spec TASK-042
- [ ] RED: escrever testes que falham
- [ ] GREEN: implementar pipeline.get_active_categories() + dashboard endpoint + template
- [ ] REFACTOR: limpar, verificar cobertura
- [ ] Verify: pytest + ruff
- [ ] Archive

## Critérios de Verificação
```bash
pytest tests/ -x -q
ruff check . --select E,F,I
! grep -r "app_key\|app_secret\|tracking_id" app/templates/ && echo OK_NO_API_FIELDS
grep -q "200003655\|SCAN_CATEGORIES" app/templates/settings.html && echo OK_CATEGORIES
grep -q "SCAN_CATEGORIES" app/pipeline.py && echo OK_PIPELINE_READS_ENV
```
