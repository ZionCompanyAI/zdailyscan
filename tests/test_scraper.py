import os
from unittest.mock import AsyncMock, patch

import pytest

from app.scrapers.aliexpress import AliProduct, get_hot_products

_FAKE_PRODUCT = AliProduct(
    product_id="999",
    title="Fake",
    price_usd=1.0,
    sale_count_30d=10,
    rating=4.8,
    image_url="https://ae01.alicdn.com/kf/fake.jpg",
    product_url="https://www.aliexpress.com/item/999.html",
    category_id="200000783",
)


async def test_get_hot_products_filters_low_rating():
    """Products with rating below min_rating are excluded from results."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "mock"}):
        results = await get_hot_products("200000783", min_rating=4.9)
    assert len(results) > 0
    assert all(p.rating >= 4.9 for p in results)


def test_aliproduct_fields_complete():
    """AliProduct exposes all 8 required fields."""
    p = AliProduct(
        product_id="123",
        title="Test Product",
        price_usd=10.0,
        sale_count_30d=500,
        rating=4.9,
        image_url="https://ae01.alicdn.com/kf/test.jpg",
        product_url="https://www.aliexpress.com/item/123.html",
        category_id="200000783",
    )
    assert p.product_id == "123"
    assert p.title == "Test Product"
    assert p.price_usd == 10.0
    assert p.sale_count_30d == 500
    assert p.rating == 4.9
    assert p.image_url == "https://ae01.alicdn.com/kf/test.jpg"
    assert p.product_url == "https://www.aliexpress.com/item/123.html"
    assert p.category_id == "200000783"


async def test_mock_mode_no_network():
    """SCRAPER_MODE=mock returns mock data without invoking Crawl4AI."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "mock"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai", new_callable=AsyncMock
        ) as mock_crawl:
            results = await get_hot_products("200000783")
    mock_crawl.assert_not_called()
    assert isinstance(results, list)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_firecrawl_mode_uses_scrape_with_firecrawl():
    """SCRAPER_MODE=firecrawl chama _scrape_with_firecrawl (issue #126)."""
    env = {
        "SCRAPER_MODE": "firecrawl",
        "FIRECRAWL_API_KEY": "fc-test",
        "ALIEXPRESS_SESSION_COOKIES": '[{"name":"x","value":"y"}]',
    }
    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_firecrawl",
            new_callable=AsyncMock,
            return_value=[_FAKE_PRODUCT],
        ) as mock_fc:
            results = await get_hot_products("200000783")

    mock_fc.assert_called_once()
    assert results == [_FAKE_PRODUCT]


@pytest.mark.asyncio
async def test_crawl4ai_mode_applies_min_rating_filter():
    """crawl4ai filtra resultados por min_rating."""
    low_rated = AliProduct(
        product_id="1",
        title="Low",
        price_usd=1.0,
        sale_count_30d=5,
        rating=3.0,
        image_url="",
        product_url="",
        category_id="200000783",
    )
    with patch.dict(os.environ, {"SCRAPER_MODE": "crawl4ai"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[_FAKE_PRODUCT, low_rated],
        ):
            results = await get_hot_products("200000783", min_rating=4.5)

    assert all(p.rating >= 4.5 for p in results)
    assert low_rated not in results


@pytest.mark.asyncio
async def test_get_hot_products_filters_zero_price():
    """Products with price_usd=0 are excluded — prevents zero import cost inflating the score."""
    zero_price = AliProduct(
        product_id="0",
        title="No Price",
        price_usd=0.0,
        sale_count_30d=100,
        rating=4.9,
        image_url="",
        product_url="",
        category_id="200000783",
    )
    with patch.dict(os.environ, {"SCRAPER_MODE": "crawl4ai"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[_FAKE_PRODUCT, zero_price],
        ):
            results = await get_hot_products("200000783")

    assert zero_price not in results
    assert _FAKE_PRODUCT in results
