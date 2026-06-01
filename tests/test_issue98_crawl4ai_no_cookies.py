"""Issue #98 — crawl4ai deve ser chamado mesmo sem cookies."""
import os
from unittest.mock import AsyncMock, patch

from app.scrapers.aliexpress import get_hot_products
from app.scrapers.models import AliProduct

_CRAWL_PRODUCT = AliProduct(
    product_id="crawl001",
    title="Crawl4AI Product",
    price_usd=8.99,
    sale_count_30d=300,
    rating=4.8,
    image_url="https://ae01.alicdn.com/kf/crawl.jpg",
    product_url="https://www.aliexpress.com/item/crawl001.html",
    category_id="200000783",
)

_FIRE_PRODUCT = AliProduct(
    product_id="fire001",
    title="Firecrawl Fallback Product",
    price_usd=11.99,
    sale_count_30d=100,
    rating=4.7,
    image_url="https://ae01.alicdn.com/kf/fire.jpg",
    product_url="https://www.aliexpress.com/item/fire001.html",
    category_id="200000783",
)


async def test_no_cookies_calls_crawl4ai_first():
    """Issue #98: sem cookies → crawl4ai chamado (browser headless não precisa de cookies)."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "http://firecrawl:3002",
        "ALIEXPRESS_SESSION_COOKIES": "",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[_CRAWL_PRODUCT],
        ) as mock_crawl:
            results = await get_hot_products("200000783", min_rating=0.0)

    mock_crawl.assert_called_once()
    assert len(results) == 1
    assert results[0].product_id == "crawl001"


async def test_no_cookies_no_firecrawl_url_returns_empty():
    """Issue #98: sem cookies e sem FIRECRAWL_URL → crawl4ai tentado, retorna []."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "",
        "ALIEXPRESS_SESSION_COOKIES": "",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_crawl:
            results = await get_hot_products("200000783", min_rating=0.0)

    mock_crawl.assert_called_once()
    assert results == []
