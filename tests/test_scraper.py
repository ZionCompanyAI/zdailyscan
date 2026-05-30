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


async def test_extracted_content_as_string_returns_products():
    """crawl4ai may return extracted_content as a JSON string — must be parsed, not iterated as chars."""
    import json
    import sys
    from unittest.mock import MagicMock

    fake_items = [
        {
            "product_id": "/item/123.html",
            "title": "Test Product",
            "price": "US$9.99",
            "sold": "1000+sold",
            "rating": "4.9",
            "image_url": "https://ae01.alicdn.com/kf/test.jpg",
        }
    ]
    fake_result = MagicMock()
    fake_result.extracted_content = json.dumps(fake_items)

    mock_crawler_instance = AsyncMock()
    mock_crawler_instance.arun = AsyncMock(return_value=fake_result)

    MockCrawlerCtx = MagicMock()
    MockCrawlerCtx.return_value.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
    MockCrawlerCtx.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_crawl4ai = MagicMock()
    mock_crawl4ai.AsyncWebCrawler = MockCrawlerCtx
    mock_crawl4ai.BrowserConfig = MagicMock()
    mock_crawl4ai.CrawlerRunConfig = MagicMock()

    mock_extraction = MagicMock()
    mock_extraction.JsonCssExtractionStrategy = MagicMock()

    with patch.dict(sys.modules, {
        "crawl4ai": mock_crawl4ai,
        "crawl4ai.extraction_strategy": mock_extraction,
    }):
        # Force re-import to pick up mocked modules
        import importlib
        import app.scrapers.aliexpress as ali_mod
        importlib.reload(ali_mod)

        results = await ali_mod._scrape_with_crawl4ai("200000783", max_results=10)

    assert len(results) == 1, f"Expected 1 product, got {len(results)} — extracted_content string was not parsed"
    assert results[0].product_id == "123"
    assert results[0].title == "Test Product"
