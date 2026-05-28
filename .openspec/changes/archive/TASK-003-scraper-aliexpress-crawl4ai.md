# TASK-003 Scraper AliExpress com Crawl4AI

## Objetivo
Implementar scraper de produtos AliExpress usando Crawl4AI como biblioteca principal,
mock para testes (SCRAPER_MODE=mock) e Firecrawl self-hosted como fallback opcional.

## Pacote / Módulo
- `app/scrapers/__init__.py` — factory `get_scraper()`
- `app/scrapers/aliexpress.py` — implementação Crawl4AI
- `app/scrapers/mock.py` — 5 produtos fixos para testes
- `app/scrapers/fallback_firecrawl.py` — fallback Firecrawl self-hosted
- `app/config.py` — adicionar `scraper_mode` e `firecrawl_url`
- `requirements.txt` — adicionar `crawl4ai>=0.4.0`
- `Dockerfile` — adicionar `RUN crawl4ai-setup`
- `tests/test_scraper.py` — suite de testes

## Contratos

```python
# app/scrapers/__init__.py
from pydantic import BaseModel

class AliProduct(BaseModel):
    product_id: str
    title: str
    price_usd: float
    sale_count_30d: int
    rating: float
    image_url: str
    product_url: str
    category_id: str

async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
) -> list[AliProduct]: ...
```

```python
# app/config.py — novos campos
scraper_mode: str = "crawl4ai"   # "crawl4ai" | "mock"
firecrawl_url: str | None = None  # se definido, usa Firecrawl como fallback
```

```python
# app/scrapers/mock.py
async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
) -> list[AliProduct]: ...
# retorna 5 produtos fixos, com ratings mistos para testar filtro
```

```python
# app/scrapers/aliexpress.py — Crawl4AI
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
) -> list[AliProduct]: ...

SCRAPING_URLS = {
    "bestseller": "https://www.aliexpress.com/category/{category_id}/bestselling.html",
    "wholesale": "https://www.aliexpress.com/wholesale?SearchText=&SortType=total_tranpro_desc&catId={category_id}",
}
```

```python
# app/scrapers/fallback_firecrawl.py
import httpx

async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
    firecrawl_url: str = "",
) -> list[AliProduct]: ...
```

## Detalhes de Implementação
- `app/scrapers/__init__.py` expõe `AliProduct` e `get_hot_products()`
- `get_hot_products` delega para mock/crawl4ai/firecrawl via `SCRAPER_MODE` env var
- Mock retorna 5 produtos fixos: 3 com rating >= 4.9, 2 com rating < 4.9 (para testar filtro)
- Filtro `min_rating` aplicado ANTES de retornar (qualquer mode)
- Categorias iniciais: Beauty=200000783, Home=200000828, Sports=200000790

## Tasks (checklist de execução)
- [x] Criar `tests/test_scraper.py` com 3 testes (RED)
- [x] Rodar testes — devem FALHAR
- [x] Criar `app/scrapers/__init__.py` com `AliProduct` + factory
- [x] Criar `app/scrapers/mock.py`
- [x] Criar `app/scrapers/aliexpress.py`
- [x] Criar `app/scrapers/fallback_firecrawl.py`
- [x] Atualizar `app/config.py` com novos campos
- [x] Atualizar `requirements.txt`
- [x] Atualizar `Dockerfile`
- [x] Rodar testes — devem PASSAR (GREEN)
- [x] REFACTOR + retestar

## Critérios de Verificação
```bash
pytest tests/test_scraper.py -v
# PASSED tests/test_scraper.py::test_get_hot_products_filters_low_rating
# PASSED tests/test_scraper.py::test_aliproduct_fields_complete
# PASSED tests/test_scraper.py::test_mock_mode_no_network
```
