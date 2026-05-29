"""Tests for TASK-046: AliExpress login credentials in Settings page."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
# 1. config.py — novos campos
# ---------------------------------------------------------------------------

def test_config_has_aliexpress_username_field(monkeypatch):
    """Settings deve expor aliexpress_username lendo de ALIEXPRESS_USERNAME."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "user@example.com")
    from app.config import Settings
    s = Settings()
    assert s.aliexpress_username == "user@example.com"


def test_config_aliexpress_username_defaults_empty(monkeypatch):
    """aliexpress_username deve ter default vazio."""
    monkeypatch.delenv("ALIEXPRESS_USERNAME", raising=False)
    from app.config import Settings
    s = Settings()
    assert s.aliexpress_username == ""


def test_config_has_aliexpress_password_field(monkeypatch):
    """Settings deve expor aliexpress_password lendo de ALIEXPRESS_PASSWORD."""
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "senha123")
    from app.config import Settings
    s = Settings()
    assert s.aliexpress_password == "senha123"


def test_config_aliexpress_password_defaults_empty(monkeypatch):
    """aliexpress_password deve ter default vazio."""
    monkeypatch.delenv("ALIEXPRESS_PASSWORD", raising=False)
    from app.config import Settings
    s = Settings()
    assert s.aliexpress_password == ""


# ---------------------------------------------------------------------------
# 2. GET /dashboard/settings — exibe seção AliExpress
# ---------------------------------------------------------------------------

def test_settings_shows_aliexpress_section(monkeypatch):
    """GET /settings deve exibir card/seção AliExpress."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "AliExpress" in resp.text


def test_settings_shows_aliexpress_form_action(monkeypatch):
    """Formulário AliExpress deve POST para /dashboard/settings/aliexpress."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "settings/aliexpress" in resp.text


def test_settings_shows_aliexpress_username_value(monkeypatch):
    """GET /settings deve mostrar username configurado."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "user@example.com")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "user@example.com" in resp.text


def test_settings_shows_password_masked_not_plaintext(monkeypatch):
    """GET /settings nunca exibe senha em plaintext."""
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "senha_secreta_123")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "senha_secreta_123" not in resp.text


def test_settings_shows_password_masked_placeholder(monkeypatch):
    """GET /settings deve exibir senha como placeholder mascarado (não vazio)."""
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "senha_secreta_123")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    # senha mascarada: 4 chars visíveis + "***" → "senh***"
    assert "senh***" in resp.text or "***" in resp.text


def test_settings_aliexpress_password_field_type(monkeypatch):
    """Campo de senha deve ser type='password' no HTML."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert 'type="password"' in resp.text or "type='password'" in resp.text


# ---------------------------------------------------------------------------
# 3. POST /dashboard/settings/aliexpress — endpoint
# ---------------------------------------------------------------------------

def test_settings_aliexpress_post_without_auth_redirects(monkeypatch):
    """POST sem auth deve redirecionar para /login."""
    client = _make_client(monkeypatch)
    resp = client.post(
        "/dashboard/settings/aliexpress",
        data={"aliexpress_username": "user@example.com", "aliexpress_password": "abc"},
    )
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_settings_aliexpress_post_with_auth_redirects_to_settings(monkeypatch):
    """POST com auth deve retornar 303 para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("app.routers.dashboard._persist_railway_var", new_callable=AsyncMock):
        resp = client.post(
            "/dashboard/settings/aliexpress",
            data={"aliexpress_username": "user@example.com", "aliexpress_password": "senha123"},
            cookies={"session": cookie},
        )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard/settings"


def test_settings_aliexpress_post_saves_username_to_env(monkeypatch):
    """POST deve salvar ALIEXPRESS_USERNAME em os.environ."""
    monkeypatch.delenv("ALIEXPRESS_USERNAME", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("app.routers.dashboard._persist_railway_var", new_callable=AsyncMock):
        client.post(
            "/dashboard/settings/aliexpress",
            data={"aliexpress_username": "user@example.com", "aliexpress_password": ""},
            cookies={"session": cookie},
        )
    assert os.environ.get("ALIEXPRESS_USERNAME") == "user@example.com"


def test_settings_aliexpress_post_saves_password_to_env(monkeypatch):
    """POST deve salvar ALIEXPRESS_PASSWORD em os.environ."""
    monkeypatch.delenv("ALIEXPRESS_PASSWORD", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("app.routers.dashboard._persist_railway_var", new_callable=AsyncMock):
        client.post(
            "/dashboard/settings/aliexpress",
            data={"aliexpress_username": "", "aliexpress_password": "nova_senha"},
            cookies={"session": cookie},
        )
    assert os.environ.get("ALIEXPRESS_PASSWORD") == "nova_senha"


def test_settings_aliexpress_post_empty_username_does_not_overwrite(monkeypatch):
    """POST com username vazio não deve sobrescrever valor existente."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "original@example.com")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("app.routers.dashboard._persist_railway_var", new_callable=AsyncMock):
        client.post(
            "/dashboard/settings/aliexpress",
            data={"aliexpress_username": "", "aliexpress_password": "alguma_senha"},
            cookies={"session": cookie},
        )
    assert os.environ.get("ALIEXPRESS_USERNAME") == "original@example.com"


def test_settings_aliexpress_post_empty_password_does_not_overwrite(monkeypatch):
    """POST com password vazio não deve sobrescrever valor existente."""
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "senha_original")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("app.routers.dashboard._persist_railway_var", new_callable=AsyncMock):
        client.post(
            "/dashboard/settings/aliexpress",
            data={"aliexpress_username": "user@example.com", "aliexpress_password": ""},
            cookies={"session": cookie},
        )
    assert os.environ.get("ALIEXPRESS_PASSWORD") == "senha_original"


# ---------------------------------------------------------------------------
# 4. _persist_railway_var — integração Railway API
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_persist_railway_var_calls_railway_api(monkeypatch):
    """_persist_railway_var deve chamar Railway GraphQL API quando token configurado."""
    monkeypatch.setenv("RAILWAY_API_TOKEN", "rw-token-123")
    monkeypatch.setenv("RAILWAY_SERVICE_ID", "svc-123")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "env-123")
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "proj-123")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = mock_post
        mock_client_cls.return_value = mock_client

        from app.routers.dashboard import _persist_railway_var
        await _persist_railway_var("ALIEXPRESS_USERNAME", "user@example.com")

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "backboard.railway.app" in call_kwargs[0][0]


@pytest.mark.asyncio
async def test_persist_railway_var_noop_without_token(monkeypatch):
    """_persist_railway_var deve ser no-op se RAILWAY_API_TOKEN não configurado."""
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)

    with patch("httpx.AsyncClient") as mock_client_cls:
        from app.routers.dashboard import _persist_railway_var
        await _persist_railway_var("ALIEXPRESS_USERNAME", "user@example.com")

    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_persist_railway_var_noop_without_service_id(monkeypatch):
    """_persist_railway_var deve ser no-op se RAILWAY_SERVICE_ID não configurado."""
    monkeypatch.setenv("RAILWAY_API_TOKEN", "rw-token-123")
    monkeypatch.delenv("RAILWAY_SERVICE_ID", raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT_ID", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_ID", raising=False)

    with patch("httpx.AsyncClient") as mock_client_cls:
        from app.routers.dashboard import _persist_railway_var
        await _persist_railway_var("ALIEXPRESS_USERNAME", "user@example.com")

    mock_client_cls.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Scraper — autenticação antes de crawl
# ---------------------------------------------------------------------------

def _make_crawl4ai_mocks():
    """Build sys.modules mocks for crawl4ai (not installed in dev env)."""
    mock_result = MagicMock()
    mock_result.extracted_content = []

    mock_crawler = AsyncMock()
    mock_crawler.arun = AsyncMock(return_value=mock_result)
    mock_crawler.authenticate = AsyncMock()

    mock_instance = AsyncMock()
    mock_instance.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_instance.__aexit__ = AsyncMock(return_value=False)

    mock_crawl4ai = MagicMock()
    mock_crawl4ai.AsyncWebCrawler.return_value = mock_instance
    mock_crawl4ai.BrowserConfig = MagicMock()
    mock_crawl4ai.CrawlerRunConfig = MagicMock()

    mock_extraction = MagicMock()
    mock_extraction.JsonCssExtractionStrategy = MagicMock()

    return mock_crawl4ai, mock_extraction, mock_crawler


@pytest.mark.asyncio
async def test_scraper_authenticates_when_credentials_set(monkeypatch):
    """_scrape_with_crawl4ai deve chamar crawler.authenticate quando credenciais configuradas."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "user@example.com")
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "senha123")

    mock_crawl4ai, mock_extraction, mock_crawler = _make_crawl4ai_mocks()
    with patch.dict(sys.modules, {
        "crawl4ai": mock_crawl4ai,
        "crawl4ai.extraction_strategy": mock_extraction,
    }):
        from app.scrapers.aliexpress import _scrape_with_crawl4ai
        await _scrape_with_crawl4ai("200003655", 10)

    mock_crawler.authenticate.assert_called_once()
    call_kwargs = mock_crawler.authenticate.call_args
    assert call_kwargs[1]["username"] == "user@example.com"
    assert call_kwargs[1]["password"] == "senha123"
    assert "aliexpress.com" in call_kwargs[1]["url"]


@pytest.mark.asyncio
async def test_scraper_skips_auth_when_no_credentials(monkeypatch):
    """_scrape_with_crawl4ai não deve chamar authenticate quando credenciais ausentes."""
    monkeypatch.delenv("ALIEXPRESS_USERNAME", raising=False)
    monkeypatch.delenv("ALIEXPRESS_PASSWORD", raising=False)

    mock_crawl4ai, mock_extraction, mock_crawler = _make_crawl4ai_mocks()
    with patch.dict(sys.modules, {
        "crawl4ai": mock_crawl4ai,
        "crawl4ai.extraction_strategy": mock_extraction,
    }):
        from app.scrapers.aliexpress import _scrape_with_crawl4ai
        await _scrape_with_crawl4ai("200003655", 10)

    mock_crawler.authenticate.assert_not_called()


@pytest.mark.asyncio
async def test_scraper_skips_auth_when_only_username_set(monkeypatch):
    """Autenticação requer AMBAS as variáveis — apenas username não autentica."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "user@example.com")
    monkeypatch.delenv("ALIEXPRESS_PASSWORD", raising=False)

    mock_crawl4ai, mock_extraction, mock_crawler = _make_crawl4ai_mocks()
    with patch.dict(sys.modules, {
        "crawl4ai": mock_crawl4ai,
        "crawl4ai.extraction_strategy": mock_extraction,
    }):
        from app.scrapers.aliexpress import _scrape_with_crawl4ai
        await _scrape_with_crawl4ai("200003655", 10)

    mock_crawler.authenticate.assert_not_called()
