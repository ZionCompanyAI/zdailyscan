# [TASK-030] Dashboard web — relatórios, force scan e login compartilhável

## Objetivo
Criar uma interface web para o ZDailyScan com visualização dos relatórios diários,
botão "Force Scan" para scan manual, e login simples com cookie assinado.

## Pacote / Módulo
Novos arquivos:
- `app/routers/auth.py` — login/logout (itsdangerous cookie)
- `app/routers/dashboard.py` — rotas HTML do dashboard
- `app/templates/login.html` — formulário de login
- `app/templates/base.html` — layout base
- `app/templates/dashboard.html` — lista de relatórios por data
- `app/templates/report.html` — tabela de produtos de um dia
- `app/static/style.css` — CSS mínimo

Modificações:
- `app/config.py` — adicionar `dashboard_username`, `dashboard_password`, `dashboard_session_secret`
- `app/main.py` — registrar auth/dashboard routers + StaticFiles + Jinja2Templates
- `requirements.txt` — adicionar `itsdangerous`, `jinja2`

## Contratos

```python
# GET /           → redirect /dashboard se cookie válido, /login se não
# GET /login      → HTML formulário de login
# POST /login     → Form(username, password) → valida → set cookie session → redirect /dashboard
# GET /logout     → apaga cookie → redirect /login
# GET /dashboard  → lista arquivos data/scans/*.json por data (desc)
# GET /dashboard/{date} → lê data/scans/{date}.json → tabela produtos
# POST /dashboard/scan  → chama POST /scan/run com x-api-key → redirect /dashboard
```

## Detalhes de Implementação

- Cookie `session` assinado via `itsdangerous.URLSafeSerializer(secret, salt="session")`
- Payload do cookie: `{"user": username}`
- Dependência `require_session(request)` → devolve username ou RedirectResponse(/login)
- Templates: Jinja2 com `request` no contexto
- `POST /dashboard/scan` chama internamente `httpx.post("/scan/run", headers={"x-api-key": SCAN_API_KEY})`
- `app/static/` servido em `/static`

## Tasks
- [x] Spec criada
- [ ] RED: testes escritos e falhando
- [ ] GREEN: implementação mínima
- [ ] REFACTOR: limpeza

## Critérios de Verificação
```bash
python3 -c "from app.routers.auth import router; from app.routers.dashboard import router as dr; print('ok')"
python3 -m pytest tests/test_dashboard.py -v -k "auth or login or redirect"
python3 -m pytest tests/test_dashboard.py -v -k "report or table"
grep -E "dashboard_username|dashboard_password|dashboard_session_secret" app/config.py
ruff check app/routers/dashboard.py app/routers/auth.py
```
