"""Tests for TASK-078: persist Railway env vars on settings save."""

import os

os.environ.setdefault("ALIEXPRESS_APP_KEY", "test")
os.environ.setdefault("ALIEXPRESS_APP_SECRET", "test")
os.environ.setdefault("ALIEXPRESS_TRACKING_ID", "testtrack")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("MC_API_KEY", "test")
os.environ.setdefault("MC_URL", "http://localhost")
os.environ.setdefault("DASHBOARD_USERNAME", "admin")
os.environ.setdefault("DASHBOARD_PASSWORD", "secret")
os.environ.setdefault("DASHBOARD_SESSION_SECRET", "test-secret-key")

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _signed_cookie(username: str = "admin") -> str:
    from itsdangerous import URLSafeSerializer

    s = URLSafeSerializer("test-secret-key", salt="session")
    return s.dumps({"user": username})


def _make_client(monkeypatch):
    monkeypatch.setenv("DASHBOARD_USERNAME", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("DASHBOARD_SESSION_SECRET", "test-secret-key")
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# 1. _persist_railway_env — unit tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_persist_railway_env_noop_when_vars_missing(monkeypatch):
    """Quando Railway vars ausentes, função retorna sem chamar HTTP."""
    railway_vars = [
        "RAILWAY_API_TOKEN", "RAILWAY_PROJECT_ID",
        "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID",
    ]
    for var in railway_vars:
        monkeypatch.delenv(var, raising=False)

    from app.routers.dashboard import _persist_railway_env

    with patch("httpx.AsyncClient") as mock_client_cls:
        await _persist_railway_env("MY_KEY", "my_value")
        mock_client_cls.assert_not_called()


@pytest.mark.anyio
async def test_persist_railway_env_calls_graphql_when_vars_present(monkeypatch):
    """Quando Railway vars presentes, faz POST GraphQL com a mutation correta."""
    monkeypatch.setenv("RAILWAY_API_TOKEN", "tok123")
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "proj-id")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "env-id")
    monkeypatch.setenv("RAILWAY_SERVICE_ID", "svc-id")

    from app.routers.dashboard import _persist_railway_env

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await _persist_railway_env("ALIEXPRESS_SESSION_COOKIES", "abc123")

    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    assert "backboard.railway.app/graphql/v2" in call_kwargs[0][0]
    body = call_kwargs[1]["json"]
    assert "variableCollectionUpsert" in body["query"]
    assert "ALIEXPRESS_SESSION_COOKIES" in body["query"]
    assert "tok123" in call_kwargs[1]["headers"]["Authorization"]


@pytest.mark.anyio
async def test_persist_railway_env_swallows_http_exception(monkeypatch):
    """Exceção HTTP não propaga — log apenas."""
    monkeypatch.setenv("RAILWAY_API_TOKEN", "tok")
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "p")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "e")
    monkeypatch.setenv("RAILWAY_SERVICE_ID", "s")

    from app.routers.dashboard import _persist_railway_env

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        # Must not raise
        await _persist_railway_env("KEY", "val")


# ---------------------------------------------------------------------------
# 2. POST /settings — calls _persist_railway_env for cookies
# ---------------------------------------------------------------------------


def test_post_settings_calls_persist_for_cookies(monkeypatch):
    """POST /settings deve chamar _persist_railway_env para ALIEXPRESS_SESSION_COOKIES."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()

    persist_calls = []

    async def fake_persist(key: str, value: str) -> None:
        persist_calls.append((key, value))

    with patch("app.routers.dashboard._persist_railway_env", side_effect=fake_persist):
        resp = client.post(
            "/dashboard/settings",
            data={"aliexpress_session_cookies": '[{"name":"sid","value":"tok"}]'},
            cookies={"session": cookie},
        )

    assert resp.status_code == 303
    assert any(k == "ALIEXPRESS_SESSION_COOKIES" for k, _ in persist_calls)


# ---------------------------------------------------------------------------
# 3. POST /settings/categories — calls _persist_railway_env for categories
# ---------------------------------------------------------------------------


def test_post_settings_categories_calls_persist(monkeypatch):
    """POST /settings/categories deve chamar _persist_railway_env para SCAN_CATEGORIES."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()

    persist_calls = []

    async def fake_persist(key: str, value: str) -> None:
        persist_calls.append((key, value))

    with patch("app.routers.dashboard._persist_railway_env", side_effect=fake_persist):
        resp = client.post(
            "/dashboard/settings/categories",
            data={"categories": ["200003655", "100003070"]},
            cookies={"session": cookie},
        )

    assert resp.status_code == 303
    assert any(k == "SCAN_CATEGORIES" for k, _ in persist_calls)
