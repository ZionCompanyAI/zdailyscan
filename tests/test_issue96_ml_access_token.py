"""
Issue #96 — get_ml_access_token() integra auth-bus com fallback para env var.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import get_ml_access_token


@pytest.mark.asyncio
async def test_uses_auth_bus_when_api_key_configured():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "bus-token-abc"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    env = {"AUTH_BUS_API_KEY": "secret-key", "AUTH_BUS_URL": "https://auth-bus.example.com"}
    with patch("app.config.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_access_token()

    assert token == "bus-token-abc"
    mock_client.get.assert_awaited_once()
    call_args = mock_client.get.call_args
    assert "/tokens/mercadolibre" in call_args.args[0]
    assert call_args.kwargs["headers"]["x-api-key"] == "secret-key"
    assert call_args.kwargs["headers"]["User-Agent"] == "ZionCompanyAI/1.0"


@pytest.mark.asyncio
async def test_fallback_on_auth_bus_exception():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=Exception("connection refused"))

    env = {
        "AUTH_BUS_API_KEY": "secret-key",
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "ML_USER_ACCESS_TOKEN": "fallback-token",
    }
    with patch("app.config.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_access_token()

    assert token == "fallback-token"


@pytest.mark.asyncio
async def test_fallback_on_non_200_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    env = {
        "AUTH_BUS_API_KEY": "secret-key",
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "ML_USER_ACCESS_TOKEN": "fallback-token",
    }
    with patch("app.config.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_access_token()

    assert token == "fallback-token"


@pytest.mark.asyncio
async def test_no_api_key_skips_auth_bus_and_uses_env():
    import os

    env = {"ML_USER_ACCESS_TOKEN": "env-only-token"}
    with patch.dict("os.environ", env, clear=False):
        os.environ.pop("AUTH_BUS_API_KEY", None)
        token = await get_ml_access_token()

    assert token == "env-only-token"


@pytest.mark.asyncio
async def test_no_api_key_no_env_returns_empty():
    import os

    with patch.dict("os.environ", {}, clear=False):
        os.environ.pop("AUTH_BUS_API_KEY", None)
        os.environ.pop("ML_USER_ACCESS_TOKEN", None)
        token = await get_ml_access_token()

    assert token == ""


@pytest.mark.asyncio
async def test_uses_default_auth_bus_url_when_env_not_set():
    """Sem AUTH_BUS_URL, usa https://auth-bus.zioncompanyai.com.br por padrão."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "default-url-token"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    import os

    env = {"AUTH_BUS_API_KEY": "secret-key"}
    with patch("app.config.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            os.environ.pop("AUTH_BUS_URL", None)
            token = await get_ml_access_token()

    assert token == "default-url-token"
    called_url = mock_client.get.call_args.args[0]
    assert called_url.startswith("https://auth-bus.zioncompanyai.com.br")
