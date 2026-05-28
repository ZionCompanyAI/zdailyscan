# [TASK-028] fix: TELEGRAM_CHAT_ID hardcoded → Settings

## Objetivo
Remover constante `TELEGRAM_CHAT_ID = 7041182277` hardcoded em `telegram_reporter.py` e expô-la como campo configurável via env var `ZDAILYSCAN_TELEGRAM_CHAT_ID` em `Settings`.

## Pacote / Módulo
- `app/config.py` → classe `Settings`
- `app/reporters/telegram_reporter.py` → `send_daily_report()`

## Contratos

```python
# app/config.py
class Settings(BaseSettings):
    # ... campos existentes ...
    telegram_chat_id: int = Field(default=7041182277, env="ZDAILYSCAN_TELEGRAM_CHAT_ID")

# app/reporters/telegram_reporter.py
async def send_daily_report(results: list[ProductScore]) -> bool:
    settings = Settings()
    # usa settings.telegram_chat_id em vez de TELEGRAM_CHAT_ID constante
    json={"chat_id": settings.telegram_chat_id, "text": message, "parse_mode": "Markdown"}
```

## Critérios de Verificação (do issue)
```bash
! grep -r "TELEGRAM_CHAT_ID = 7041182277" app/
grep -r "telegram_chat_id" app/config.py
grep -r "settings.telegram_chat_id" app/reporters/telegram_reporter.py
```

## Tasks
- [x] RED: escrever testes que falham
- [x] GREEN: implementar campos e substituição
- [x] REFACTOR: limpar imports desnecessários
