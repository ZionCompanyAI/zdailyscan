import os
from unittest.mock import AsyncMock, patch

from app.scrapers.aliexpress import get_hot_products
from app.scrapers.models import AliProduct

_COOKIE_PRODUCT = AliProduct(
    product_id="c001",
    title="Cookie Product",
    price_usd=9.99,
    sale_count_30d=200,
    rating=5.0,
    image_url="https://ae01.alicdn.com/kf/cookie.jpg",
    product_url="https://www.aliexpress.com/item/c001.html",
    category_id="200000783",
)

_FIRE_PRODUCT = AliProduct(
    product_id="f001",
    title="Firecrawl Product",
    price_usd=12.50,
    sale_count_30d=150,
    rating=4.9,
    image_url="https://ae01.alicdn.com/kf/fire.jpg",
    product_url="https://www.aliexpress.com/item/f001.html",
    category_id="200000783",
)


async def test_cookies_set_uses_crawl4ai_primary():
    """When ALIEXPRESS_SESSION_COOKIES is set, crawl4ai is called (not firecrawl directly)."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "http://firecrawl:3002",
        "ALIEXPRESS_SESSION_COOKIES": '[{"name":"token","value":"abc"}]',
    }
    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[_COOKIE_PRODUCT],
        ) as mock_crawl:
            with patch(
                "app.scrapers.aliexpress.get_products_via_firecrawl",
                new_callable=AsyncMock,
                return_value=[_FIRE_PRODUCT],
            ) as mock_fire:
                results = await get_hot_products("200000783", min_rating=0.0)

    mock_crawl.assert_called_once()
    mock_fire.assert_not_called()
    assert len(results) == 1
    assert results[0].product_id == "c001"


async def test_cookies_set_crawl4ai_empty_falls_back_to_firecrawl():
    """With cookies, if crawl4ai returns [], firecrawl fallback is triggered."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "http://firecrawl:3002",
        "ALIEXPRESS_SESSION_COOKIES": '[{"name":"token","value":"abc"}]',
    }
    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_crawl:
            with patch(
                "app.scrapers.aliexpress.get_products_via_firecrawl",
                new_callable=AsyncMock,
                return_value=[_FIRE_PRODUCT],
            ) as mock_fire:
                results = await get_hot_products("200000783", min_rating=0.0)

    mock_crawl.assert_called_once()
    mock_fire.assert_called_once()
    assert len(results) == 1
    assert results[0].product_id == "f001"


async def test_no_cookies_uses_firecrawl_directly():
    """Without ALIEXPRESS_SESSION_COOKIES, crawl4ai is never called; firecrawl runs directly."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "http://firecrawl:3002",
        "ALIEXPRESS_SESSION_COOKIES": "",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[_COOKIE_PRODUCT],
        ) as mock_crawl:
            with patch(
                "app.scrapers.aliexpress.get_products_via_firecrawl",
                new_callable=AsyncMock,
                return_value=[_FIRE_PRODUCT],
            ) as mock_fire:
                results = await get_hot_products("200000783", min_rating=0.0)

    mock_crawl.assert_not_called()
    mock_fire.assert_called_once()
    assert results[0].product_id == "f001"


async def test_no_cookies_no_firecrawl_url_returns_empty():
    """Without cookies and without FIRECRAWL_URL, returns [] without crashing."""
    env = {
        "SCRAPER_MODE": "crawl4ai",
        "FIRECRAWL_URL": "",
        "ALIEXPRESS_SESSION_COOKIES": "",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
        ) as mock_crawl:
            results = await get_hot_products("200000783", min_rating=0.0)

    mock_crawl.assert_not_called()
    assert results == []
