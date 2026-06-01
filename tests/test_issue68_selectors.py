import os
import re
from unittest.mock import AsyncMock, patch


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


async def test_empty_crawl4ai_returns_empty_list():
    """When crawl4ai returns 0 products, result is [] — no Firecrawl fallback (issue #115)."""
    env = {"SCRAPER_MODE": "crawl4ai", "FIRECRAWL_URL": "http://firecrawl:3002"}

    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai",
            new_callable=AsyncMock,
            return_value=[],
        ):
            from app.scrapers.aliexpress import get_hot_products

            results = await get_hot_products("200000783", min_rating=0.0)

    assert results == []


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
