"""Regression tests — gaps que deixaram #81/#82 passarem no CI.

Gap 1: default min_rating não verificado em test_scraper.py
Gap 2: SCRAPER_MODE=firecrawl nunca testado como modo primário
Gap 3: pipeline mockava get_hot_products por completo, defaults nunca exercitados
"""
import inspect
import os
from unittest.mock import AsyncMock, patch

from app.scrapers.aliexpress import get_hot_products


def test_get_hot_products_default_min_rating_is_zero():
    """get_hot_products default min_rating deve ser 0.0, não 4.9."""
    sig = inspect.signature(get_hot_products)
    default = sig.parameters["min_rating"].default
    assert default == 0.0, f"Expected min_rating default=0.0, got {default}"


async def test_scraper_mode_firecrawl_nao_chama_crawl4ai():
    """SCRAPER_MODE=firecrawl com FIRECRAWL_URL chama Firecrawl diretamente, nunca crawl4ai."""
    env = {"SCRAPER_MODE": "firecrawl", "FIRECRAWL_URL": "http://firecrawl.test"}
    with patch.dict(os.environ, env):
        with patch(
            "app.scrapers.aliexpress._scrape_with_crawl4ai", new_callable=AsyncMock
        ) as mock_c4a:
            with patch(
                "app.scrapers.aliexpress.get_products_via_firecrawl",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_fc:
                await get_hot_products("200000783")

    mock_c4a.assert_not_called()
    mock_fc.assert_called_once()


async def test_get_hot_products_default_inclui_produtos_baixo_rating():
    """Com min_rating default (0.0), produtos com rating < 4.9 devem ser incluídos."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "mock"}):
        results = await get_hot_products("200000783")

    ratings = [p.rating for p in results]
    assert any(r < 4.9 for r in ratings), (
        "Expected products with rating < 4.9 to be included when min_rating uses its default"
    )
