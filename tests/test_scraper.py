import pytest


@pytest.fixture(autouse=True)
def scraper_mode_mock(monkeypatch):
    monkeypatch.setenv("SCRAPER_MODE", "mock")


@pytest.mark.asyncio
async def test_get_hot_products_filters_low_rating():
    from app.scrapers import get_hot_products

    results = await get_hot_products("200000783", min_rating=4.9)

    assert isinstance(results, list)
    assert len(results) > 0
    for product in results:
        assert product.rating >= 4.9


@pytest.mark.asyncio
async def test_aliproduct_fields_complete():
    from app.scrapers import get_hot_products

    results = await get_hot_products("200000783")

    assert len(results) > 0
    product = results[0]
    assert product.product_id != ""
    assert product.title != ""
    assert product.price_usd > 0
    assert product.sale_count_30d >= 0
    assert product.rating >= 0
    assert product.image_url != ""
    assert product.product_url != ""
    assert product.category_id == "200000783"


@pytest.mark.asyncio
async def test_mock_mode_no_network(monkeypatch):
    crawl4ai_called = []

    class FakeCrawler:
        async def __aenter__(self):
            crawl4ai_called.append(True)
            return self

        async def __aexit__(self, *args):
            pass

        async def arun(self, *args, **kwargs):
            crawl4ai_called.append(True)
            raise AssertionError("Crawl4AI should not be called in mock mode")

    monkeypatch.setattr("app.scrapers.aliexpress.AsyncWebCrawler", FakeCrawler, raising=False)

    from app.scrapers import get_hot_products

    results = await get_hot_products("200000783")

    assert len(crawl4ai_called) == 0, "Crawl4AI was called in mock mode"
    assert len(results) > 0
