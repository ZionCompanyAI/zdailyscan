# ZDailyScan

Scanner diário de oportunidades AliExpress para LojaHi Select — produtos top-vendidos, análise de viabilidade e comparativo de mercado BR.

## Descrição

ZDailyScan é um serviço FastAPI que escaneia o AliExpress em busca de produtos com alto potencial para a loja LojaHi Select, gerando relatórios diários via Telegram e integrando-se ao Mission Control.

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

## Arquitetura

```
app/
├── config.py          — variáveis de ambiente (pydantic-settings)
├── models.py          — ProductScore (modelo de oportunidade avaliada)
├── pipeline.py        — run_daily_scan(): orquestra scan + reporters
├── analyzers/
│   ├── mercado_livre.py     — busca preços no ML para análise de demanda
│   └── import_calculator.py — calcula custo total de importação (II + ICMS)
└── reporters/
    ├── telegram_reporter.py — envia top 10 via Mission Control /telegram/reply
    └── file_reporter.py     — salva relatório em data/reports/YYYY-MM-DD.md
```

## Env vars

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `ALIEXPRESS_APP_KEY` | App Key da API AliExpress | — |
| `ALIEXPRESS_APP_SECRET` | App Secret da API AliExpress | — |
| `ALIEXPRESS_TRACKING_ID` | Tracking ID para afiliados | — |
| `TELEGRAM_BOT_TOKEN` | Token do bot Telegram para notificações | — |
| `MC_API_KEY` | API Key do Mission Control | — |
| `MC_URL` | URL do Mission Control (ex: https://orchestrator.zioncompanyai.com.br) | — |
| `USD_BRL_RATE` | Cotação USD/BRL para cálculo de importação | `5.70` |

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
