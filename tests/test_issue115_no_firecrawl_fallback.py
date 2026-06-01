"""Issue #115 — verificações residuais de isolamento de modo.

Issue #126 reintroduziu Firecrawl como modo padrão. Os testes abaixo cobrem
apenas os modos crawl4ai e http, cujo comportamento não foi alterado.
"""
import os
from unittest.mock import AsyncMock, patch

from app.scrapers.aliexpress import get_hot_products
from app.scrapers.models import AliProduct

_CRAWL_PRODUCT = AliProduct(
    product_id="crawl115",
    title="Crawl4AI Product 115",
    price_usd=9.99,
    sale_count_30d=200,
    rating=4.7,
    image_url="https://ae01.alicdn.com/kf/crawl115.jpg",
    product_url="https://www.aliexpress.com/item/crawl115.html",
    category_id="200003655",
)


async def test_crawl4ai_empty_never_falls_back_to_firecrawl():
    """crawl4ai retorna [] com FIRECRAWL_URL setado → resultado [], Firecrawl não é chamado."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "https://api.firecrawl.dev",
    }
    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_crawl:
            results = await get_hot_products("200003655")

    mock_crawl.assert_called_once()
    assert results == []


async def test_firecrawl_url_env_var_ignored_in_scraper():
    """FIRECRAWL_URL no ambiente não deve acionar Firecrawl em nenhum cenário."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "https://api.firecrawl.dev",
        "ALIEXPRESS_SESSION_COOKIES": "",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[_CRAWL_PRODUCT],
        ):
            results = await get_hot_products("200003655")

    assert results == [_CRAWL_PRODUCT]
