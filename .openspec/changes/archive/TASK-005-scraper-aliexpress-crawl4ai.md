# TASK-005 feat: scraper AliExpress com Crawl4AI

## Objetivo
Criar módulo de scraping web para AliExpress usando Crawl4AI como biblioteca principal,
com mock para testes e fallback Firecrawl self-hosted. Paralelo ao scraper de API existente
(app/aliexpress.py) — pipeline existente não é modificado nesta task.

## Pacote / Módulo
- `app/scrapers/models.py` — AliProduct Pydantic (8 campos)
- `app/scrapers/__init__.py` — vazio
- `app/scrapers/aliexpress.py` — entrada principal, routing por SCRAPER_MODE + Crawl4AI
- `app/scrapers/mock.py` — 5 produtos fixos (2 com rating < 4.9 para testar filtro)
- `app/scrapers/fallback_firecrawl.py` — fallback via FIRECRAWL_URL

## Contratos

```python
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
    category_id: str, min_rating: float = 4.9, max_results: int = 100
) -> list[AliProduct]: ...

def get_mock_products(
    category_id: str, min_rating: float = 4.9, max_results: int = 100
) -> list[AliProduct]: ...

async def get_products_via_firecrawl(
    category_id: str, firecrawl_url: str, max_results: int = 100
) -> list[AliProduct]: ...
```

## Detalhes de Implementação
- `crawl4ai` importado LAZILY dentro de `_scrape_with_crawl4ai` (evita ImportError em testes sem Chromium)
- `get_hot_products` lê `SCRAPER_MODE` em call time (não import time) → patch.dict funciona nos testes
- `mock.py` importa `AliProduct` de `models.py` (sem circular import)
- Filtro `rating >= min_rating` aplicado APÓS scraping (não dentro do scraper)
- URLs de scraping: `https://www.aliexpress.com/category/{category_id}/bestselling.html`
- Categorias iniciais: Beauty (200000783), Home & Garden (200000828), Sports (200000790)

## Tasks
- [x] Criar app/scrapers/models.py
- [x] Criar app/scrapers/__init__.py
- [x] Criar app/scrapers/aliexpress.py
- [x] Criar app/scrapers/mock.py (2 produtos com rating < 4.9)
- [x] Criar app/scrapers/fallback_firecrawl.py
- [x] Update requirements.txt: crawl4ai>=0.4.0
- [x] Update Dockerfile: RUN crawl4ai-setup
- [x] Criar tests/test_scraper.py com 3 testes
- [x] pytest tests/test_scraper.py -v → todos PASSED

## Critérios de Verificação
```bash
pytest tests/test_scraper.py -v
# PASSED test_get_hot_products_filters_low_rating
# PASSED test_aliproduct_fields_complete
# PASSED test_mock_mode_no_network
```
