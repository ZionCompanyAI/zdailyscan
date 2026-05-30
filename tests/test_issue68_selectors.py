import os
import re
from unittest.mock import AsyncMock, patch

from app.scrapers.models import AliProduct

# Mirrors the acceptance criterion grep from issue #68:
# grep -E "list--gallery--|list--item--|multi--|C2f2tvm|G8aNaOa|nXeOvyr|U-S0jtj|Ktbl2jB"
STALE_SELECTOR_RE = re.compile(
    r"list--gallery--|list--item--|multi--|C2f2tvm|G8aNaOa|nXeOvyr|U-S0jtj|Ktbl2jB"
)


def test_product_schema_no_dynamic_hashes():
    """Schema must not contain stale webpack-hash CSS class names (issue #68 criterion 2)."""
    from app.scrapers.aliexpress import _PRODUCT_SCHEMA

    schema_str = str(_PRODUCT_SCHEMA)
    match = STALE_SELECTOR_RE.search(schema_str)
    assert not match, f"Schema contains stale/hash-based selector: '{match.group()}'"


async def test_empty_crawl4ai_triggers_firecrawl():
    """When crawl4ai returns 0 products and FIRECRAWL_URL is set, firecrawl fallback runs."""
    fallback_product = AliProduct(
        product_id="789",
        title="Fallback Product",
        price_usd=15.0,
        sale_count_30d=100,
        rating=5.0,
        image_url="https://ae01.alicdn.com/kf/fallback.jpg",
        product_url="https://www.aliexpress.com/item/789.html",
        category_id="200000783",
    )
    env = {"SCRAPER_MODE": "crawl4ai", "FIRECRAWL_URL": "http://firecrawl:3002"}

    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with patch(
                "app.scrapers.aliexpress.get_products_via_firecrawl",
                new_callable=AsyncMock,
                return_value=[fallback_product],
            ) as mock_fire:
                from app.scrapers.aliexpress import get_hot_products

                results = await get_hot_products("200000783", min_rating=0.0)

    mock_fire.assert_called_once()
    assert len(results) == 1
    assert results[0].product_id == "789"


async def test_empty_crawl4ai_no_firecrawl_url_returns_empty():
    """When crawl4ai returns [] and FIRECRAWL_URL is absent, return empty list (no crash)."""
    env = {"SCRAPER_MODE": "crawl4ai", "FIRECRAWL_URL": ""}

    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[],
        ):
            from app.scrapers.aliexpress import get_hot_products

            results = await get_hot_products("200000783", min_rating=0.0)

    assert results == []
