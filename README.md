# ZDailyScan

Scanner diário de oportunidades AliExpress para LojaHi Select — produtos top-vendidos, análise de viabilidade e comparativo de mercado BR.

## Descrição

ZDailyScan é um serviço FastAPI que escaneia o AliExpress em busca de produtos com alto potencial para a loja LojaHi Select, gerando relatórios diários via Telegram e disponibilizando um dashboard web para visualização e controle.

O scan completo executa automaticamente às **06:00 BRT** (cron `0 9 * * *` UTC): scraper AliExpress → analyzer Mercado Livre → scorer de viabilidade → persistência JSON → relatório Telegram + arquivo Markdown.

O **dashboard web** em `zdailyscan.zioncompanyai.com.br` permite visualizar relatórios históricos, disparar scans manuais e compartilhar acesso via login com usuário/senha.

## Setup local

```bash
# 1. Clone e entre no diretório
git clone https://github.com/ZionCompanyAI/zdailyscan.git
cd zdailyscan

# 2. Crie o venv e instale dependências
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# edite .env com suas credenciais

# 4. Inicie o servidor
uvicorn app.main:app --reload
```

## Env vars

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `ALIEXPRESS_APP_KEY` | Sim | App Key da API AliExpress Affiliate |
| `ALIEXPRESS_APP_SECRET` | Sim | App Secret da API AliExpress Affiliate |
| `ALIEXPRESS_TRACKING_ID` | Sim | Tracking ID para afiliados |
| `ALIEXPRESS_USERNAME` | Não | Usuário AliExpress para scraping autenticado |
| `ALIEXPRESS_PASSWORD` | Não | Senha AliExpress para scraping autenticado |
| `TELEGRAM_BOT_TOKEN` | Sim | Token do bot Telegram para notificações |
| `MC_API_KEY` | Sim | API Key do Mission Control |
| `MC_URL` | Sim | URL do Mission Control (ex: https://orchestrator.zioncompanyai.com.br) |
| `AUTH_BUS_URL` | Não | URL do auth-bus para obter ML token dinamicamente |
| `AUTH_BUS_API_KEY` | Não | API Key do auth-bus (obrigatória se `AUTH_BUS_URL` configurado) |
| `ML_USER_ACCESS_TOKEN` | Não | ML access token estático (fallback quando auth-bus indisponível) |
| `ML_SEARCH_PROXY_URL` | Não | URL de proxy para ML search (contorna bloqueio PolicyAgent em Railway) |
| `SCAN_API_KEY` | Não | Chave para `POST /scan/run` (default: `test`) |
| `USD_BRL_RATE` | Não | Taxa de câmbio USD/BRL (default: `5.70`) |
| `DASHBOARD_USERNAME` | Não | Usuário do dashboard web (default: `admin`) |
| `DASHBOARD_PASSWORD` | Sim | Senha do dashboard web |
| `DASHBOARD_SESSION_SECRET` | Sim | Secret para assinar cookies de sessão (gerar aleatório) |

## Módulos

| Módulo | Descrição |
|--------|-----------|
| `app/aliexpress.py` | Cliente AliExpress Affiliate API — busca produtos quentes por categoria |
| `app/pipeline.py` | Orquestrador do scan: AliExpress → analyzer → scorer, retorna top-20 viáveis |
| `app/storage.py` | Persistência JSON diária em `data/scans/YYYY-MM-DD.json` |
| `app/scheduler.py` | `AsyncIOScheduler` registrado no lifespan do FastAPI (cron 09:00 UTC) |
| `app/analyzers/mercado_livre.py` | Busca preços e contagem de resultados no Mercado Livre BR |
| `app/analyzers/import_calculator.py` | Calcula custo total de importação (II + ICMS, regimes remessa_conforme e normal) |
| `app/scoring/scorer.py` | Score de viabilidade composto (margem, demanda, oportunidade, tendência, logística) |
| `app/reporters/telegram_reporter.py` | Envia top 10 oportunidades para Toni via `POST $MC_URL/telegram/reply` |
| `app/reporters/file_reporter.py` | Salva relatório Markdown em `data/reports/YYYY-MM-DD.md` |
| `app/routers/auth.py` | Login/logout com cookie de sessão assinado (`itsdangerous`) |
| `app/routers/dashboard.py` | Dashboard web: lista relatórios, exibe tabela, dispara scan |
| `app/templates/` | Templates Jinja2: `login.html`, `dashboard.html`, `report.html` |
| `app/static/style.css` | CSS do dashboard (sem framework externo) |

### Score de viabilidade

```python
from app.scoring.scorer import score_product, AliProduct

score = score_product(ali, market, cost)
# score.viavel: True se score_total >= 0.60
# score.sell_price_suggestion_brl: total_cost_brl × 2.5
```

Fórmula: `score = 0.30×Margem + 0.25×Demanda_BR + 0.20×Oportunidade + 0.15×Tendencia + 0.10×Logistica`

## Endpoints

### API JSON

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `GET` | `/scan/latest` | Retorna o último scan salvo (404 se nenhum) |
| `GET` | `/scan/{date}` | Retorna scan de data específica (`YYYY-MM-DD`) |
| `POST` | `/scan/run` | Dispara scan manual imediato (header `x-api-key` obrigatório) |

### Dashboard web (HTML — requer login)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Redirect para `/dashboard` (logado) ou `/login` |
| `GET` | `/login` | Formulário de login |
| `POST` | `/login` | Valida credenciais → seta cookie → redirect `/dashboard` |
| `GET` | `/logout` | Apaga cookie → redirect `/login` |
| `GET` | `/dashboard` | Lista relatórios disponíveis por data |
| `GET` | `/dashboard/{date}` | Tabela de produtos do dia (`YYYY-MM-DD`) |
| `POST` | `/dashboard/scan` | Dispara scan manual (requer login) |

```bash
# Disparar scan manual
curl -X POST http://localhost:8000/scan/run \
  -H "x-api-key: test"
# {"status": "started", "scan_id": "..."}

# Consultar último scan
curl http://localhost:8000/scan/latest

# Consultar scan de data específica
curl http://localhost:8000/scan/2026-05-28
```

## Desenvolvimento

```bash
# Instale as dependências de desenvolvimento
pip install -r requirements-dev.txt

# Configure o pre-commit hook (ruff linter + ruff-format)
pre-commit install

# Executar manualmente em todos os arquivos
pre-commit run --all-files
```

O hook roda automaticamente em cada `git commit`: **ruff** verifica e corrige problemas de lint, **ruff-format** garante formatação consistente.

## Testes

```bash
pytest tests/
```

## Deploy Railway

O projeto inclui `railway.toml` configurado. Basta conectar o repositório no Railway e configurar as variáveis de ambiente listadas acima.

```toml
# railway.toml
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

## Health check

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "zdailyscan"}
```
