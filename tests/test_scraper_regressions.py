"""Regression tests — gaps que deixaram #81/#82/#100 passarem no CI.

Gap 1: default min_rating não verificado em test_scraper.py
Gap 2: SCRAPER_MODE=firecrawl nunca testado como modo primário
Gap 3: pipeline mockava get_hot_products por completo, defaults nunca exercitados
Gap 4 (issue #100): CrawlerRunConfig não aceita mais cookies= kwarg
"""
import inspect
import os
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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


@pytest.mark.asyncio
async def test_crawl4ai_no_cookies_kwarg_in_run_config():
    """_scrape_with_crawl4ai não deve passar cookies= para CrawlerRunConfig (issue #100).

    Usa um stub de CrawlerRunConfig que levanta TypeError se receber cookies=,
    replicando o comportamento da versão instalada do crawl4ai.
    """
    from app.scrapers.aliexpress import _scrape_with_crawl4ai

    def strict_run_config(*args, **kwargs):
        if "cookies" in kwargs:
            raise TypeError(
                "CrawlerRunConfig.__init__() got an unexpected keyword argument 'cookies'"
            )
        return MagicMock()

    mock_result = MagicMock()
    mock_result.extracted_content = "[]"
    mock_crawler = AsyncMock()
    mock_crawler.arun = AsyncMock(return_value=mock_result)
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=None)

    fake_crawl4ai = ModuleType("crawl4ai")
    fake_crawl4ai.BrowserConfig = MagicMock(return_value=MagicMock())
    fake_crawl4ai.CrawlerRunConfig = strict_run_config
    fake_crawl4ai.AsyncWebCrawler = MagicMock(return_value=mock_crawler)

    fake_extraction = ModuleType("crawl4ai.extraction_strategy")
    fake_extraction.JsonCssExtractionStrategy = MagicMock(return_value=MagicMock())

    with patch.dict(sys.modules, {
        "crawl4ai": fake_crawl4ai,
        "crawl4ai.extraction_strategy": fake_extraction,
    }):
        result = await _scrape_with_crawl4ai(
            "200000783", 10, '[{"name":"x","value":"y"}]'
        )

    assert isinstance(result, list)
