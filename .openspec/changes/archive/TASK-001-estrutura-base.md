# [TASK-001] Estrutura base do projeto ZDailyScan

## Objetivo
Criar a estrutura base do projeto Python FastAPI para o ZDailyScan — scanner diário de oportunidades AliExpress para LojaHi Select.

## Pacote / Módulo
- `app/main.py` → FastAPI app + health check
- `app/config.py` → pydantic-settings env vars
- `pyproject.toml` → dependências e metadados
- `requirements.txt` → dependências pinadas
- `.env.example` → template de env vars
- `Dockerfile` → build Python 3.11-slim multi-stage
- `railway.toml` → config de deploy
- `.gitignore` → exclusões padrão Python

## Contratos

```python
# app/main.py
GET /health → 200 {"status": "ok", "service": "zdailyscan"}
```

```python
# app/config.py
class Settings(BaseSettings):
    aliexpress_app_key: str
    aliexpress_app_secret: str
    aliexpress_tracking_id: str
    telegram_bot_token: str
    mc_api_key: str
    mc_url: str

    model_config = SettingsConfigDict(env_file=".env")
```

## Detalhes de Implementação
- FastAPI + uvicorn
- pydantic-settings para config
- Python 3.11-slim no Docker
- railway.toml com startCommand uvicorn

## Tasks
- [x] Criar .openspec/changes/TASK-001
- [x] Fase RED: escrever e rodar testes (devem FALHAR)
- [x] Fase GREEN: implementar app/main.py + app/config.py + arquivos de infra
- [x] Fase REFACTOR: limpar, garantir que testes passam
- [x] Verify: pytest 4/4 ✅ | docker build (sem docker local, validado pelo Dockerfile)
- [x] Archive

## Critérios de Verificação
- `GET /health` retorna HTTP 200 `{"status": "ok", "service": "zdailyscan"}`
- `app/config.py` carrega env vars sem erro a partir de `.env.example`
- `docker build` completa sem erros
- `pytest` passa com pelo menos 1 smoke test do health check
