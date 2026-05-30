"""Tests for TASK-072: AliExpress session cookie injection replacing username/password."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("ALIEXPRESS_APP_KEY", "test")
os.environ.setdefault("ALIEXPRESS_APP_SECRET", "test")
os.environ.setdefault("ALIEXPRESS_TRACKING_ID", "testtrack")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("MC_API_KEY", "test")
os.environ.setdefault("MC_URL", "http://localhost")
os.environ.setdefault("DASHBOARD_USERNAME", "admin")
os.environ.setdefault("DASHBOARD_PASSWORD", "secret")
os.environ.setdefault("DASHBOARD_SESSION_SECRET", "test-secret-key")


def _make_client(monkeypatch):
    monkeypatch.setenv("DASHBOARD_USERNAME", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("DASHBOARD_SESSION_SECRET", "test-secret-key")
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app, follow_redirects=False)


def _signed_cookie(username: str = "admin") -> str:
    from itsdangerous import URLSafeSerializer

    s = URLSafeSerializer("test-secret-key", salt="session")
    return s.dumps({"user": username})


# ---------------------------------------------------------------------------
# 1. GET /dashboard/settings — template has SESSION_COOKIES, not username/password
# ---------------------------------------------------------------------------


def test_settings_has_session_cookies_field(monkeypatch):
    """Settings page deve conter ALIEXPRESS_SESSION_COOKIES no HTML."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "SESSION_COOKIES" in resp.text or "session_cookies" in resp.text


def test_settings_no_longer_has_username_field(monkeypatch):
    """Settings page não deve conter input de aliexpress_username."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert 'name="aliexpress_username"' not in resp.text


def test_settings_no_longer_has_password_field(monkeypatch):
    """Settings page não deve conter input de aliexpress_password."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert 'name="aliexpress_password"' not in resp.text


def test_settings_shows_cookies_status_empty(monkeypatch):
    """Quando ALIEXPRESS_SESSION_COOKIES vazio, mostra ○ Vazio."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "○" in resp.text or "Vazio" in resp.text


def test_settings_shows_cookies_status_filled(monkeypatch):
    """Quando ALIEXPRESS_SESSION_COOKIES preenchido, mostra ● Preenchido."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", '{"ali_apache_id":"abc123"}')
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "●" in resp.text or "Preenchido" in resp.text


def test_settings_cookies_card_has_textarea(monkeypatch):
    """Card de session cookies deve ter um textarea."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "<textarea" in resp.text
    assert "session_cookies" in resp.text


def test_settings_does_not_expose_cookie_values(monkeypatch):
    """Settings não deve exibir os valores dos cookies."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", '{"secret_token":"supersecretvalue"}')
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "supersecretvalue" not in resp.text


# ---------------------------------------------------------------------------
# 2. POST /dashboard/settings — saves SESSION_COOKIES
# ---------------------------------------------------------------------------


def test_post_settings_saves_session_cookies_to_env(monkeypatch):
    """POST /dashboard/settings salva ALIEXPRESS_SESSION_COOKIES em os.environ."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    payload = json.dumps({"ali_apache_id": "abc", "_tb_token_": "xyz"})
    client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": payload},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_SESSION_COOKIES") == payload


def test_post_settings_empty_cookies_do_not_overwrite(monkeypatch):
    """POST com campo vazio não sobrescreve ALIEXPRESS_SESSION_COOKIES existente."""
    existing = '{"ali_apache_id":"existing"}'
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", existing)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": ""},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_SESSION_COOKIES") == existing


def test_post_settings_with_cookies_redirects_to_settings(monkeypatch):
    """POST /dashboard/settings com cookies válidos redireciona para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": '{"test":"val"}'},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard/settings"


# ---------------------------------------------------------------------------
# 3. Scraper — cookies injected into Crawl4AI
# ---------------------------------------------------------------------------


def _fake_crawl4ai_modules(mock_crawler):
    """Return a sys.modules patch dict for crawl4ai (not installed in test env)."""
    mock_result = MagicMock()
    mock_result.extracted_content = "[]"
    mock_crawler.arun = AsyncMock(return_value=mock_result)

    mock_strategy = MagicMock()
    mock_extraction_mod = MagicMock()
    mock_extraction_mod.JsonCssExtractionStrategy = MagicMock(return_value=mock_strategy)

    mock_crawl4ai_mod = MagicMock()
    mock_crawl4ai_mod.AsyncWebCrawler = MagicMock(return_value=mock_crawler)
    mock_crawl4ai_mod.BrowserConfig = MagicMock(return_value=MagicMock())
    mock_crawl4ai_mod.CrawlerRunConfig = MagicMock(return_value=MagicMock())

    return {
        "crawl4ai": mock_crawl4ai_mod,
        "crawl4ai.extraction_strategy": mock_extraction_mod,
    }


async def test_scraper_injects_cookies_into_crawl4ai(monkeypatch):
    """Scraper deve injetar ALIEXPRESS_SESSION_COOKIES no arun() do Crawl4AI."""
    import sys
    import importlib

    cookies_json = '{"ali_apache_id":"abc","_tb_token_":"xyz"}'
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", cookies_json)

    mock_crawler = AsyncMock()
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=None)

    fake_mods = _fake_crawl4ai_modules(mock_crawler)
    with patch.dict(sys.modules, fake_mods):
        if "app.scrapers.aliexpress" in sys.modules:
            del sys.modules["app.scrapers.aliexpress"]
        from app.scrapers.aliexpress import _scrape_with_crawl4ai
        await _scrape_with_crawl4ai("200003655", 10)

    call_kwargs = mock_crawler.arun.call_args
    assert call_kwargs is not None
    passed_cookies = call_kwargs.kwargs.get("cookies")
    assert passed_cookies == {"ali_apache_id": "abc", "_tb_token_": "xyz"}


async def test_scraper_uses_empty_dict_when_no_cookies(monkeypatch):
    """Scraper usa cookies={} quando ALIEXPRESS_SESSION_COOKIES não definido."""
    import sys

    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)

    mock_crawler = AsyncMock()
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=None)

    fake_mods = _fake_crawl4ai_modules(mock_crawler)
    with patch.dict(sys.modules, fake_mods):
        if "app.scrapers.aliexpress" in sys.modules:
            del sys.modules["app.scrapers.aliexpress"]
        from app.scrapers.aliexpress import _scrape_with_crawl4ai
        await _scrape_with_crawl4ai("200003655", 10)

    call_kwargs = mock_crawler.arun.call_args
    passed_cookies = call_kwargs.kwargs.get("cookies")
    assert passed_cookies == {}


async def test_scraper_handles_invalid_json_cookies_gracefully(monkeypatch):
    """Scraper trata JSON inválido em ALIEXPRESS_SESSION_COOKIES sem crashar."""
    import sys

    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", "not-valid-json{")

    mock_crawler = AsyncMock()
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=None)

    fake_mods = _fake_crawl4ai_modules(mock_crawler)
    with patch.dict(sys.modules, fake_mods):
        if "app.scrapers.aliexpress" in sys.modules:
            del sys.modules["app.scrapers.aliexpress"]
        from app.scrapers.aliexpress import _scrape_with_crawl4ai
        result = await _scrape_with_crawl4ai("200003655", 10)

    assert isinstance(result, list)
    passed_cookies = mock_crawler.arun.call_args.kwargs.get("cookies")
    assert passed_cookies == {}
