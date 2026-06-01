"""Issue #120 — remover user_agent_generator_config inválido do BrowserConfig.

crawl4ai >=0.4.0 não aceita device_type/os_type em user_agent_generator_config.
Verifica que o argumento não está mais presente na chamada a BrowserConfig.
"""
import asyncio
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock
from contextlib import contextmanager


def _make_crawl4ai_mock():
    mock_bc = MagicMock(name="BrowserConfig")
    mock_rc = MagicMock(name="CrawlerRunConfig")

    mock_result = MagicMock()
    mock_result.extracted_content = "[]"
    mock_result.html = "<html><title>Test</title></html>"

    mock_crawler_instance = AsyncMock()
    mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
    mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
    mock_crawler_instance.arun = AsyncMock(return_value=mock_result)

    fake_crawl4ai = ModuleType("crawl4ai")
    fake_crawl4ai.AsyncWebCrawler = MagicMock(return_value=mock_crawler_instance)
    fake_crawl4ai.BrowserConfig = mock_bc
    fake_crawl4ai.CrawlerRunConfig = mock_rc

    fake_strategy = ModuleType("crawl4ai.extraction_strategy")
    fake_strategy.JsonCssExtractionStrategy = MagicMock(name="JsonCssExtractionStrategy")

    return fake_crawl4ai, fake_strategy, mock_bc, mock_rc


@contextmanager
def _fake_crawl4ai_ctx():
    fake_crawl4ai, fake_strategy, mock_bc, mock_rc = _make_crawl4ai_mock()
    orig = {
        "crawl4ai": sys.modules.get("crawl4ai"),
        "crawl4ai.extraction_strategy": sys.modules.get("crawl4ai.extraction_strategy"),
        "app.scrapers.aliexpress": sys.modules.get("app.scrapers.aliexpress"),
    }
    sys.modules["crawl4ai"] = fake_crawl4ai
    sys.modules["crawl4ai.extraction_strategy"] = fake_strategy
    sys.modules.pop("app.scrapers.aliexpress", None)
    try:
        import app.scrapers.aliexpress as mod
        yield mod, mock_bc, mock_rc
    finally:
        sys.modules.pop("app.scrapers.aliexpress", None)
        for key, original in orig.items():
            if original is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = original


def test_browser_config_no_user_agent_generator_config():
    """BrowserConfig não deve receber user_agent_generator_config — inválido em crawl4ai >=0.4.0."""
    with _fake_crawl4ai_ctx() as (mod, mock_bc, _):
        asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    assert mock_bc.called, "BrowserConfig deve ser instanciado"
    bc_kwargs = mock_bc.call_args.kwargs
    assert "user_agent_generator_config" not in bc_kwargs, (
        f"user_agent_generator_config não deve estar presente em BrowserConfig; "
        f"kwargs recebidos: {list(bc_kwargs.keys())}"
    )


def test_browser_config_keeps_user_agent_mode_random():
    """user_agent_mode='random' deve ser mantido após remoção do user_agent_generator_config."""
    with _fake_crawl4ai_ctx() as (mod, mock_bc, _):
        asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    bc_kwargs = mock_bc.call_args.kwargs
    assert bc_kwargs.get("user_agent_mode") == "random", (
        f"user_agent_mode deve permanecer 'random', got {bc_kwargs.get('user_agent_mode')!r}"
    )


def test_crawler_run_config_keeps_magic_true():
    """magic=True deve permanecer intacto após a remoção."""
    with _fake_crawl4ai_ctx() as (mod, _, mock_rc):
        asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    rc_kwargs = mock_rc.call_args.kwargs
    assert rc_kwargs.get("magic") is True, (
        f"magic deve permanecer True, got {rc_kwargs.get('magic')!r}"
    )
