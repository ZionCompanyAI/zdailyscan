# TASK-005 Scraper AliExpress com Crawl4AI

## Objetivo
Implementar infraestrutura de scraping de produtos AliExpress usando Crawl4AI como motor
principal, com mock para testes e Firecrawl self-hosted como fallback.

## Pacote / Módulo
- `app/scrapers/__init__.py` — re-exports públicos
- `app/scrapers/aliexpress.py` — AliProduct model + dispatch logic + Crawl4AI scraper
- `app/scrapers/mock.py` — 5 produtos fixos (2 abaixo de 4.9 rating, para testar filtro)
- `app/scrapers/fallback_firecrawl.py` — fallback via FIRECRAWL_URL
- `tests/test_scraper.py` — 3 testes da spec

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
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
) -> list[AliProduct]:
    """Dispatch: SCRAPER_MODE=mock → mock.py | else Crawl4AI (+ Firecrawl se falhar e FIRECRAWL_URL set)"""

# mock.py
def get_mock_products(category_id: str) -> list[AliProduct]: ...

# fallback_firecrawl.py
async def scrape_with_firecrawl(category_id: str, max_results: int) -> list[AliProduct]: ...
```

## Detalhes de Implementação

### Dispatch em `get_hot_products`
1. `SCRAPER_MODE=mock` → `get_mock_products(category_id)` (sem importar crawl4ai)
2. Else → `_scrape_crawl4ai(category_id, max_results)`
3. Se Crawl4AI lançar exceção E `FIRECRAWL_URL` definida → `scrape_with_firecrawl(...)`
4. Filtrar `p.rating >= min_rating` antes de retornar

### Lazy import crawl4ai
Crawl4AI importado **dentro** de `_scrape_crawl4ai()` para não quebrar testes em ambiente sem o pacote.

### URL AliExpress
`https://www.aliexpress.com/wholesale?SearchText=&SortType=total_tranpro_desc&catId={category_id}`

### Mock products
5 produtos: rating [5.0, 4.9, 4.8, 4.7, 5.0] → com min_rating=4.9, retorna 3

## Tasks

- [x] Criar .openspec/changes/TASK-005-scraper-aliexpress-crawl4ai.md
- [x] RED: escrever tests/test_scraper.py (3 testes, FAIL esperado)
- [x] GREEN: criar app/scrapers/__init__.py, aliexpress.py, mock.py, fallback_firecrawl.py
- [x] REFACTOR: revisar imports, nomes e clean code
- [x] Atualizar requirements.txt com crawl4ai>=0.4.0 e playwright
- [x] Atualizar Dockerfile com RUN crawl4ai-setup
- [x] Archive spec + update progress.md

## Critérios de Verificação

```bash
pytest tests/test_scraper.py -v
# PASSED tests/test_scraper.py::test_get_hot_products_filters_low_rating
# PASSED tests/test_scraper.py::test_aliproduct_fields_complete
# PASSED tests/test_scraper.py::test_mock_mode_no_network
```
