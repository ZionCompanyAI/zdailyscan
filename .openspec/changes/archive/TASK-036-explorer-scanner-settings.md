# [TASK-036] Explorer de Produtos + Scanner + Settings — Fase 1 UI Dashboard

## Objetivo
Adicionar 3 novas abas HTML ao dashboard: Explorer (navegação de produtos),
Scanner (histórico + trigger de scans) e Configurações (visão read-only da config).
Adicionar endpoints JSON de suporte e atualizar a navegação em `base.html`.

## Pacote / Módulo
- `app/routers/dashboard.py` — novos endpoints (inseridos ANTES de `/{date}`)
- `app/templates/explorer.html` — página Explorer
- `app/templates/scanner.html` — página Scanner
- `app/templates/settings.html` — página Configurações
- `app/templates/base.html` — nav links

## Contratos

```python
# GET /dashboard/explorer → HTMLResponse (requer sessão)
# GET /dashboard/scanner  → HTMLResponse (requer sessão)
# GET /dashboard/settings → HTMLResponse (requer sessão)

# GET /dashboard/products?category_id&min_score&sort_by&limit=50 → JSON
# GET /dashboard/scans → JSON  {scans: [{scan_id, date, product_count, status}]}
# POST /dashboard/scan/trigger body:{categories?} → JSON {status:"started", scan_id: str}
# GET /dashboard/scan/{scan_id}/status → JSON {scan_id, status, product_count}
# POST /dashboard/settings/telegram-test → JSON {status:"ok"|"error", detail?}
```

## Detalhes de Implementação
- Rotas literais registradas ANTES de `/{date}` para evitar captura pelo catch-all
- `_scan_status` dict em memória para rastrear scans em background
- `asyncio.create_task()` para disparar `run_daily_scan()` em background
- Templates estendem `base.html`, usam apenas `var(--color-*)` tokens OKLCH
- Sem Bootstrap, sem CDN externo de CSS
- SCRAPER_MODE lido via `os.environ.get("SCRAPER_MODE", "crawl4ai")`

## Tasks
- [x] Spec criada
- [x] RED: Testes escritos e falhando
- [x] GREEN: Implementação mínima — testes passando
- [x] REFACTOR: Templates limpos, código sem duplicação
- [x] base.html: nav links adicionados
- [x] Archive

## Critérios de Verificação
- HTTP 200 para /dashboard/explorer, /dashboard/scanner, /dashboard/settings com sessão válida
- /dashboard/products retorna JSON com lista de produtos
- /dashboard/scans retorna JSON com lista de scans
- POST /dashboard/scan/trigger retorna {status:"started", scan_id:...}
- Nenhuma página contém "bootstrap"
- OKLCH tokens ou var(--color-*) presentes nas páginas
