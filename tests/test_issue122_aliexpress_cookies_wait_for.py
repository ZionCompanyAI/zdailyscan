"""Tests for issue #122: inject ALIEXPRESS_SESSION_COOKIES into BrowserConfig + remove wait_for."""
import ast
import asyncio
import json
import sys
from contextlib import contextmanager
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import app.scrapers.aliexpress as _ali_mod


# ---------------------------------------------------------------------------
# Helper — fake crawl4ai module (lazy imports require sys.modules patching)
# ---------------------------------------------------------------------------

def _make_crawl4ai_mock(cookies_capture: dict | None = None, raise_exc: Exception | None = None):
    """Build fake crawl4ai module. Optionally capture BrowserConfig kwargs or raise on arun."""
    captured = cookies_capture if cookies_capture is not None else {}

    class _FakeBrowserConfig:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    mock_result = MagicMock()
    mock_result.extracted_content = "[]"
    mock_result.html = ""

    mock_crawler_instance = AsyncMock()
    mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
    mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
    if raise_exc:
        mock_crawler_instance.arun = AsyncMock(side_effect=raise_exc)
    else:
        mock_crawler_instance.arun = AsyncMock(return_value=mock_result)

    fake_crawl4ai = ModuleType("crawl4ai")
    fake_crawl4ai.AsyncWebCrawler = MagicMock(return_value=mock_crawler_instance)
    fake_crawl4ai.BrowserConfig = _FakeBrowserConfig
    fake_crawl4ai.CrawlerRunConfig = MagicMock(return_value=MagicMock())

    fake_strategy_mod = ModuleType("crawl4ai.extraction_strategy")
    fake_strategy_mod.JsonCssExtractionStrategy = MagicMock(return_value=MagicMock())

    return fake_crawl4ai, fake_strategy_mod, captured


@contextmanager
def _crawl4ai_ctx(cookies_capture=None, raise_exc=None):
    fake_crawl4ai, fake_strategy, captured = _make_crawl4ai_mock(cookies_capture, raise_exc)
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
        yield mod, captured
    finally:
        sys.modules.pop("app.scrapers.aliexpress", None)
        for key, original in orig.items():
            if original is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = original


# ---------------------------------------------------------------------------
# Critério 1 — wait_for removido do código fonte
# ---------------------------------------------------------------------------

def test_no_wait_for_in_source():
    """wait_for must not appear anywhere in aliexpress.py (causes RuntimeError on timeout)."""
    src = open(_ali_mod.__file__).read()
    assert "wait_for" not in src, "wait_for still present in aliexpress.py"


# ---------------------------------------------------------------------------
# Critério 2 — cookies=cookies passado ao BrowserConfig
# ---------------------------------------------------------------------------

def test_cookies_kwarg_in_source():
    """BrowserConfig must receive cookies= kwarg in aliexpress.py."""
    src = open(_ali_mod.__file__).read()
    assert "cookies=cookies" in src, "cookies= kwarg not passed to BrowserConfig"


# ---------------------------------------------------------------------------
# Critério 3 — try/except ao redor do AsyncWebCrawler
# ---------------------------------------------------------------------------

def test_except_exception_present_in_source():
    """AsyncWebCrawler.arun must be wrapped in try/except Exception."""
    src = open(_ali_mod.__file__).read()
    assert "except Exception" in src, "No try/except Exception wrapping the crawler"


# ---------------------------------------------------------------------------
# Critério 4 — arquivo parse-able (sem erros de sintaxe)
# ---------------------------------------------------------------------------

def test_aliexpress_py_parses_cleanly():
    src = open(_ali_mod.__file__).read()
    tree = ast.parse(src)
    assert tree is not None


# ---------------------------------------------------------------------------
# Comportamento — cookies JSON válido → BrowserConfig recebe lista de dicts
# ---------------------------------------------------------------------------

def test_valid_cookies_passed_to_browser_config():
    """Valid JSON cookies must be parsed and forwarded to BrowserConfig."""
    cookies_json = json.dumps([{"name": "aep_usuc_f", "value": "site=glo"}])
    captured = {}

    with _crawl4ai_ctx(cookies_capture=captured) as (mod, _):
        asyncio.run(mod._scrape_with_crawl4ai("200000783", 10, cookies_json))

    assert "cookies" in captured, "BrowserConfig not called with cookies= kwarg"
    # issue #124: domain e path são injetados com defaults quando ausentes
    assert captured["cookies"] == [
        {"name": "aep_usuc_f", "value": "site=glo", "domain": ".aliexpress.com", "path": "/"}
    ]


# ---------------------------------------------------------------------------
# Comportamento — cookies JSON inválido → continua sem cookies (não lança)
# ---------------------------------------------------------------------------

def test_invalid_cookies_json_does_not_raise():
    """Invalid cookies JSON must be silently ignored — scraper continues without cookies."""
    captured = {}

    with _crawl4ai_ctx(cookies_capture=captured) as (mod, _):
        result = asyncio.run(mod._scrape_with_crawl4ai("200000783", 10, "NOT_VALID_JSON{{{"))

    assert isinstance(result, list)
    assert captured.get("cookies", []) == []


# ---------------------------------------------------------------------------
# Comportamento — exception do crawler → retorna lista vazia (não propaga)
# ---------------------------------------------------------------------------

def test_crawler_exception_returns_empty_list():
    """RuntimeError from crawler must be caught and return [] gracefully."""
    exc = RuntimeError("Wait condition failed: Timeout after 45000ms")

    with _crawl4ai_ctx(raise_exc=exc) as (mod, _):
        result = asyncio.run(mod._scrape_with_crawl4ai("200000783", 10, ""))

    assert result == [], f"Expected [], got {result}"


# ---------------------------------------------------------------------------
# Comportamento — sem cookies → BrowserConfig recebe lista vazia
# ---------------------------------------------------------------------------

def test_empty_cookies_string_passes_empty_list():
    """Empty session_cookies string must pass cookies=[] to BrowserConfig."""
    captured = {}

    with _crawl4ai_ctx(cookies_capture=captured) as (mod, _):
        asyncio.run(mod._scrape_with_crawl4ai("200000783", 10, ""))

    assert captured.get("cookies") == []


# ---------------------------------------------------------------------------
# Garantias de integridade — magic=True, page_timeout e js_code intactos
# ---------------------------------------------------------------------------

def test_run_config_preserves_magic_and_timeout():
    """magic=True, page_timeout=45000 and js_code must remain unchanged."""
    fake_crawl4ai, fake_strategy, _ = _make_crawl4ai_mock()
    mock_rc = MagicMock(return_value=MagicMock())
    fake_crawl4ai.CrawlerRunConfig = mock_rc

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
        asyncio.run(mod._scrape_with_crawl4ai("200000783", 10, ""))
    finally:
        sys.modules.pop("app.scrapers.aliexpress", None)
        for key, original in orig.items():
            if original is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = original

    rc_kwargs = mock_rc.call_args.kwargs
    assert rc_kwargs.get("magic") is True
    assert rc_kwargs.get("page_timeout") == 45000
    assert "window.scrollTo" in (rc_kwargs.get("js_code") or "")
    assert "wait_for" not in rc_kwargs, "wait_for must not be passed to CrawlerRunConfig"
