# [TASK-057] feat(dashboard): AliExpress credentials form in settings

## Objetivo
Adicionar card AliExpress Credentials na página /dashboard/settings com form para configurar
ALIEXPRESS_USERNAME / ALIEXPRESS_PASSWORD em runtime. Mostrar status (preenchido/vazio) sem expor valores.

## Pacote / Módulo
- `app/routers/dashboard.py` → novo endpoint `POST /dashboard/settings`
- `app/templates/settings.html` → card AliExpress com form + status

## Contratos

```python
# dashboard.py — novo endpoint
@router.post("/settings")
async def dashboard_settings_post(
    request: Request,
    aliexpress_username: str = Form(default=""),
    aliexpress_password: str = Form(default=""),
) -> RedirectResponse:
    """Salva credenciais AliExpress em os.environ e redireciona para /dashboard/settings."""

# dashboard.py — GET /settings contexto adicional
{
    "aliexpress_username_set": bool(settings.aliexpress_username),
    "aliexpress_password_set": bool(settings.aliexpress_password),
}
```

## Detalhes de Implementação
- POST salva valores não-vazios em `os.environ["ALIEXPRESS_USERNAME"]` e `os.environ["ALIEXPRESS_PASSWORD"]`
- GET passa `aliexpress_username_set`/`aliexpress_password_set` (bool) ao template
- Template mostra "● Preenchido" (verde) ou "○ Vazio" (muted) por campo
- Campos do form são do tipo `password` e opcionais (deixar em branco = não alterar)
- Env var names: `ALIEXPRESS_USERNAME` / `ALIEXPRESS_PASSWORD` (pydantic-settings mapping)

## Tasks
- [x] Criar spec TASK-057
- [ ] RED: escrever testes que falham
- [ ] GREEN: implementar POST + template card
- [ ] REFACTOR: limpar código
- [ ] Verify: pytest + ruff
- [ ] Archive

## Critérios de Verificação
```bash
grep -q "/dashboard/settings" app/routers/dashboard.py
test -f app/templates/settings.html
grep -q "ALIEXPRESS_USERNAME" app/templates/settings.html
pytest tests/test_issue57_aliexpress_settings.py -x -q
ruff check app/routers/dashboard.py app/templates/
```
