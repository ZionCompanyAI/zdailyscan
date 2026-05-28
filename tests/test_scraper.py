import os
from unittest.mock import AsyncMock, patch

from app.scrapers.aliexpress import AliProduct, get_hot_products


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
