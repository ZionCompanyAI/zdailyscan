"""Issue #117 — crawl4ai stealth anti-bot para AliExpress (total_scanned=0 regression).

Verifica que _scrape_with_crawl4ai passa configurações stealth ao BrowserConfig
e CrawlerRunConfig para contornar detecção de bot do AliExpress.

crawl4ai usa lazy import dentro da função, então mockamos via sys.modules.
Os módulos originais são preservados e restaurados após cada teste.
"""
import asyncio
import logging
import sys
from contextlib import contextmanager
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock


def _make_crawl4ai_mock(html="<html><title>Test Page</title></html>"):
    """Cria módulos fake de crawl4ai com BrowserConfig/CrawlerRunConfig rastreáveis."""
    mock_bc = MagicMock(name="BrowserConfig")
    mock_rc = MagicMock(name="CrawlerRunConfig")

    mock_result = MagicMock()
    mock_result.extracted_content = "[]"
    mock_result.html = html

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
def _fake_crawl4ai_ctx(html="<html><title>Test Page</title></html>"):
    """Injeta crawl4ai fake e recarrega aliexpress; restaura tudo ao sair."""
    fake_crawl4ai, fake_strategy, mock_bc, mock_rc = _make_crawl4ai_mock(html)

    # Salvar estado original de sys.modules
    orig = {
        "crawl4ai": sys.modules.get("crawl4ai"),
        "crawl4ai.extraction_strategy": sys.modules.get("crawl4ai.extraction_strategy"),
        "app.scrapers.aliexpress": sys.modules.get("app.scrapers.aliexpress"),
    }

    # Injetar fakes e forçar reimport de aliexpress com o crawl4ai fake
    sys.modules["crawl4ai"] = fake_crawl4ai
    sys.modules["crawl4ai.extraction_strategy"] = fake_strategy
    sys.modules.pop("app.scrapers.aliexpress", None)

    try:
        import app.scrapers.aliexpress as mod
        yield mod, mock_bc, mock_rc
    finally:
        # Restaurar módulos originais (None → remover da cache)
        sys.modules.pop("app.scrapers.aliexpress", None)
        for key, original in orig.items():
            if original is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = original


def test_browser_config_has_random_user_agent():
    """BrowserConfig deve receber user_agent_mode='random'."""
    with _fake_crawl4ai_ctx() as (mod, mock_bc, _):
        asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    assert mock_bc.called, "BrowserConfig deve ser instanciado"
    bc_kwargs = mock_bc.call_args.kwargs
    assert bc_kwargs.get("user_agent_mode") == "random", (
        f"user_agent_mode deve ser 'random', got {bc_kwargs.get('user_agent_mode')!r}"
    )


def test_crawler_run_config_has_magic_true():
    """CrawlerRunConfig deve ter magic=True para ativar stealth Playwright."""
    with _fake_crawl4ai_ctx() as (mod, _, mock_rc):
        asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    assert mock_rc.called, "CrawlerRunConfig deve ser instanciado"
    rc_kwargs = mock_rc.call_args.kwargs
    assert rc_kwargs.get("magic") is True, (
        f"magic deve ser True, got {rc_kwargs.get('magic')!r}"
    )


def test_crawler_run_config_has_no_wait_for():
    """wait_for removido em #122 — lançava RuntimeError após 45s sem catch."""
    with _fake_crawl4ai_ctx() as (mod, _, mock_rc):
        asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    rc_kwargs = mock_rc.call_args.kwargs
    assert "wait_for" not in rc_kwargs, (
        f"wait_for não deve estar presente em CrawlerRunConfig; kwargs: {list(rc_kwargs.keys())}"
    )


def test_crawler_run_config_has_page_timeout_gte_30000():
    """CrawlerRunConfig deve ter page_timeout >= 30000ms."""
    with _fake_crawl4ai_ctx() as (mod, _, mock_rc):
        asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    rc_kwargs = mock_rc.call_args.kwargs
    timeout = rc_kwargs.get("page_timeout")
    assert timeout is not None, "page_timeout deve estar definido"
    assert timeout >= 30000, f"page_timeout deve ser >= 30000ms, got {timeout}"


def test_diagnostic_log_emits_page_title(caplog):
    """Após arun(), deve logar page_title para detectar bot-check pages."""
    html = "<html><title>Bot Detection Page</title><body></body></html>"
    with _fake_crawl4ai_ctx(html) as (mod, _, _rc):
        with caplog.at_level(logging.INFO, logger="app.scrapers.aliexpress"):
            asyncio.run(mod._scrape_with_crawl4ai("200003655", 10))

    log_messages = " ".join(caplog.messages)
    assert "page_title" in log_messages or "Bot Detection Page" in log_messages, (
        f"Deve logar page_title. Logs capturados: {caplog.messages!r}"
    )
