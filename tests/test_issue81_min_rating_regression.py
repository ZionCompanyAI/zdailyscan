"""Regression test for issue #81: min_rating default must be 0.0, not 4.9.

PR #77 regressed the fix from PR #71. Firecrawl returns products with
rating=0.0 by default; a default of 4.9 filters all of them out.
"""

import inspect
import os
from unittest.mock import AsyncMock, patch

from app.scrapers.aliexpress import AliProduct, get_hot_products


def test_get_hot_products_default_min_rating_is_zero():
    """get_hot_products default min_rating must be 0.0, not 4.9."""
    sig = inspect.signature(get_hot_products)
    default = sig.parameters["min_rating"].default
    assert default == 0.0, f"Expected min_rating default=0.0, got {default}"


async def test_firecrawl_zero_rating_products_not_filtered_by_default():
    """Without explicit min_rating, products returned by Firecrawl with rating=0.0 must survive."""
    zero_rating_product = AliProduct(
        product_id="z1",
        title="Firecrawl Product No Rating",
        price_usd=9.99,
        sale_count_30d=2000,
        rating=0.0,
        image_url="https://ae01.alicdn.com/kf/z1.jpg",
        product_url="https://www.aliexpress.com/item/z1.html",
        category_id="200000783",
    )
    with patch(
        "app.scrapers.aliexpress.get_products_via_firecrawl",
        new_callable=AsyncMock,
        return_value=[zero_rating_product],
    ):
        env = {"FIRECRAWL_URL": "http://mock-firecrawl"}
        env.pop("ALIEXPRESS_SESSION_COOKIES", None)
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("ALIEXPRESS_SESSION_COOKIES", None)
            results = await get_hot_products("200000783")
    assert len(results) == 1, (
        "Products with rating=0.0 from Firecrawl must not be filtered when "
        "min_rating uses its default value"
    )
