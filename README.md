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

## Env vars

| Variável | Descrição |
|----------|-----------|
| `ALIEXPRESS_APP_KEY` | App Key da API AliExpress |
| `ALIEXPRESS_APP_SECRET` | App Secret da API AliExpress |
| `ALIEXPRESS_TRACKING_ID` | Tracking ID para afiliados |
| `TELEGRAM_BOT_TOKEN` | Token do bot Telegram para notificações |
| `MC_API_KEY` | API Key do Mission Control |
| `MC_URL` | URL do Mission Control (ex: https://orchestrator.zioncompanyai.com.br) |

## Módulos

| Módulo | Descrição |
|--------|-----------|
| `app/analyzers/mercado_livre.py` | Busca preços e contagem de resultados no Mercado Livre BR |
| `app/analyzers/import_calculator.py` | Calcula custo total de importação (II + ICMS, regimes remessa_conforme e normal) |
| `app/scoring/scorer.py` | Score de viabilidade composto (margem, demanda, oportunidade, tendência, logística) |

### Score de viabilidade

```python
from app.scoring.scorer import score_product, AliProduct

score = score_product(ali, market, cost)
# score.viavel: True se score_total >= 0.60
# score.sell_price_suggestion_brl: total_cost_brl × 2.5
```

Fórmula: `score = 0.30×Margem + 0.25×Demanda_BR + 0.20×Oportunidade + 0.15×Tendencia + 0.10×Logistica`

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
