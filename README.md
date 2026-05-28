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
crawl4ai-setup  # instala Chromium para o scraper AliExpress

# 3. Configure as variáveis de ambiente
cp .env.example .env
# edite .env com suas credenciais

# 4. Inicie o servidor
uvicorn app.main:app --reload
```

## Env vars

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `ALIEXPRESS_APP_KEY` | ✅ | App Key da API AliExpress |
| `ALIEXPRESS_APP_SECRET` | ✅ | App Secret da API AliExpress |
| `ALIEXPRESS_TRACKING_ID` | ✅ | Tracking ID para afiliados |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token do bot Telegram para notificações |
| `MC_API_KEY` | ✅ | API Key do Mission Control |
| `MC_URL` | ✅ | URL do Mission Control (ex: https://orchestrator.zioncompanyai.com.br) |
| `SCRAPER_MODE` | — | Modo do scraper: `crawl4ai` (padrão) ou `mock` (testes sem rede) |
| `FIRECRAWL_URL` | — | URL do Firecrawl self-hosted (ex: `http://localhost:3002`). Se definido, usa como fallback do Crawl4AI |

## Scraper AliExpress

O módulo `app/scrapers/` expõe a função principal:

```python
from app.scrapers import get_hot_products, AliProduct

products: list[AliProduct] = await get_hot_products(
    category_id="200000783",  # Beauty
    min_rating=4.9,
    max_results=100,
)
```

Categorias suportadas inicialmente:

| Categoria | ID |
|-----------|-----|
| Beauty | `200000783` |
| Home & Garden | `200000828` |
| Sports | `200000790` |

Routing do scraper por env var:

| `SCRAPER_MODE` | `FIRECRAWL_URL` | Backend utilizado |
|----------------|-----------------|-------------------|
| `mock` | qualquer | `mock.py` (5 produtos fixos, sem rede) |
| `crawl4ai` | não definido | `aliexpress.py` via Crawl4AI + Chromium |
| `crawl4ai` | definido | `fallback_firecrawl.py` via Firecrawl self-hosted |

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
