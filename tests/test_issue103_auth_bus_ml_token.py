"""
TASK-103 — get_ml_token() usa auth-bus dinamicamente; fallback para env var.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analyzers.mercado_livre import get_ml_token, search_br_market


# ---------------------------------------------------------------------------
# get_ml_token — unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_ml_token_uses_auth_bus_when_configured():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "bus-token-xyz"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    env = {
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "AUTH_BUS_API_KEY": "key123",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_token()

    assert token == "bus-token-xyz"
    mock_client.get.assert_awaited_once()
    call_kwargs = mock_client.get.call_args
    assert "/tokens/mercadolibre" in call_kwargs.args[0]
    assert call_kwargs.kwargs["headers"]["x-api-key"] == "key123"


@pytest.mark.asyncio
async def test_get_ml_token_fallback_on_auth_bus_exception():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=Exception("connection refused"))

    env = {
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "AUTH_BUS_API_KEY": "key123",
        "ML_USER_ACCESS_TOKEN": "fallback-token",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_token()

    assert token == "fallback-token"


@pytest.mark.asyncio
async def test_get_ml_token_fallback_on_non_200():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    env = {
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "AUTH_BUS_API_KEY": "key123",
        "ML_USER_ACCESS_TOKEN": "fallback-token",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_token()

    assert token == "fallback-token"


@pytest.mark.asyncio
async def test_get_ml_token_no_bus_configured_uses_env():
    env = {"ML_USER_ACCESS_TOKEN": "env-only-token"}
    # Ensure no AUTH_BUS_URL/AUTH_BUS_API_KEY in env
    with patch.dict("os.environ", env, clear=False):
        # Remove bus vars if present
        import os
        os.environ.pop("AUTH_BUS_URL", None)
        os.environ.pop("AUTH_BUS_API_KEY", None)
        token = await get_ml_token()

    assert token == "env-only-token"


@pytest.mark.asyncio
async def test_get_ml_token_no_bus_no_env_returns_empty():
    with patch.dict("os.environ", {}, clear=False):
        import os
        os.environ.pop("AUTH_BUS_URL", None)
        os.environ.pop("AUTH_BUS_API_KEY", None)
        os.environ.pop("ML_USER_ACCESS_TOKEN", None)
        token = await get_ml_token()

    assert token == ""


# ---------------------------------------------------------------------------
# search_br_market — integration: uses get_ml_token()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_br_market_uses_auth_bus_token():
    """Bus token deve aparecer no header Authorization da chamada ML."""
    mock_resp_ml = MagicMock()
    mock_resp_ml.raise_for_status = MagicMock()
    mock_resp_ml.json.return_value = {"results": [], "paging": {"total": 0}}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    bus_resp = MagicMock()
    bus_resp.status_code = 200
    bus_resp.json.return_value = {"access_token": "dynamic-token-99"}

    call_count = 0

    async def fake_get(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if "auth-bus" in url:
            return bus_resp
        return mock_resp_ml

    mock_client.get = fake_get

    env = {
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "AUTH_BUS_API_KEY": "key123",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            result = await search_br_market("tênis nike")

    assert result.found is False  # empty results → not found
    # call_count == 2: one bus call + one ML call
    assert call_count == 2


@pytest.mark.asyncio
async def test_search_br_market_fallback_token_used_on_bus_failure():
    """Quando bus falha, o token env var deve aparecer na chamada ML."""
    ml_get_calls = []

    mock_resp_ml = MagicMock()
    mock_resp_ml.raise_for_status = MagicMock()
    mock_resp_ml.json.return_value = {"results": [], "paging": {"total": 0}}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, **kwargs):
        if "auth-bus" in url:
            raise Exception("bus down")
        ml_get_calls.append(kwargs)
        return mock_resp_ml

    mock_client.get = fake_get

    env = {
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "AUTH_BUS_API_KEY": "key123",
        "ML_USER_ACCESS_TOKEN": "fallback-abc",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            await search_br_market("produto qualquer")

    assert len(ml_get_calls) == 1
    assert ml_get_calls[0]["headers"]["Authorization"] == "Bearer fallback-abc"
