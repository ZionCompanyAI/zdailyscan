"""
Tests for app/scrapers — issue #2 acceptance criteria.
All tests use SCRAPER_MODE=mock to avoid network/crawl4ai dependency.
"""

import pytest


def test_aliproduct_fields_complete():
    """AliProduct model must accept all 8 required fields."""
    from app.scrapers.aliexpress import AliProduct

    p = AliProduct(
        product_id="123456789",
        title="Wireless Earbuds Pro",
        price_usd=19.99,
        sale_count_30d=3200,
        rating=4.9,
        image_url="https://ae01.alicdn.com/img123.jpg",
        product_url="https://www.aliexpress.com/item/123456789.html",
        category_id="200000783",
    )

    assert p.product_id == "123456789"
    assert p.title == "Wireless Earbuds Pro"
    assert p.price_usd == 19.99
    assert p.sale_count_30d == 3200
    assert p.rating == 4.9
    assert p.image_url == "https://ae01.alicdn.com/img123.jpg"
    assert p.product_url == "https://www.aliexpress.com/item/123456789.html"
    assert p.category_id == "200000783"


async def test_get_hot_products_filters_low_rating(monkeypatch):
    """Products with rating < min_rating=4.9 must be excluded."""
    monkeypatch.setenv("SCRAPER_MODE", "mock")

    from app.scrapers.aliexpress import get_hot_products

    products = await get_hot_products("200000783", min_rating=4.9)

    assert len(products) > 0
    assert all(p.rating >= 4.9 for p in products), "All returned products must have rating >= 4.9"

    # mock has 5 products: ratings [5.0, 4.9, 4.8, 4.7, 5.0] → 3 pass filter
    assert len(products) == 3


async def test_mock_mode_no_network(monkeypatch):
    """SCRAPER_MODE=mock must return products without calling _scrape_crawl4ai."""
    monkeypatch.setenv("SCRAPER_MODE", "mock")

    import app.scrapers.aliexpress as scraper_mod

    crawl4ai_called: list[bool] = []

    async def _fake_crawl4ai(category_id: str, max_results: int):
        crawl4ai_called.append(True)
        return []

    monkeypatch.setattr(scraper_mod, "_scrape_crawl4ai", _fake_crawl4ai)

    products = await scraper_mod.get_hot_products("200000783")

    assert len(crawl4ai_called) == 0, "_scrape_crawl4ai must NOT be called in mock mode"
    assert len(products) > 0, "Mock must return products"
    assert all(hasattr(p, "rating") for p in products)
