"""RED tests for issue #96 — auth-bus integration for ML_USER_ACCESS_TOKEN renewal."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── get_ml_token() contract ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_ml_token_returns_auth_bus_token():
    """When AUTH_BUS_URL and AUTH_BUS_API_KEY are set, return token from auth-bus."""
    from app.analyzers.mercado_livre import get_ml_token

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "APP_USR-fresh-token-abc"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    env = {"AUTH_BUS_URL": "https://auth-bus.example.com", "AUTH_BUS_API_KEY": "key-123"}
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_token()

    assert token == "APP_USR-fresh-token-abc"


@pytest.mark.asyncio
async def test_get_ml_token_fallback_when_not_configured():
    """When AUTH_BUS_URL is not set, fall back to ML_USER_ACCESS_TOKEN env var."""
    from app.analyzers.mercado_livre import get_ml_token

    env = {"ML_USER_ACCESS_TOKEN": "static-token-xyz"}
    # Remove auth-bus vars
    with patch.dict("os.environ", env, clear=False):
        import os
        os.environ.pop("AUTH_BUS_URL", None)
        os.environ.pop("AUTH_BUS_API_KEY", None)
        token = await get_ml_token()

    assert token == "static-token-xyz"


@pytest.mark.asyncio
async def test_get_ml_token_fallback_on_auth_bus_non_200():
    """When auth-bus returns non-200, fall back to ML_USER_ACCESS_TOKEN env var."""
    from app.analyzers.mercado_livre import get_ml_token

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.json.return_value = {}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    env = {
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "AUTH_BUS_API_KEY": "key-123",
        "ML_USER_ACCESS_TOKEN": "fallback-token",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_token()

    assert token == "fallback-token"


@pytest.mark.asyncio
async def test_get_ml_token_fallback_on_network_error():
    """When auth-bus raises an exception, fall back to ML_USER_ACCESS_TOKEN env var."""
    from app.analyzers.mercado_livre import get_ml_token

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=Exception("connection refused"))

    env = {
        "AUTH_BUS_URL": "https://auth-bus.example.com",
        "AUTH_BUS_API_KEY": "key-123",
        "ML_USER_ACCESS_TOKEN": "fallback-token",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            token = await get_ml_token()

    assert token == "fallback-token"


@pytest.mark.asyncio
async def test_get_ml_token_sends_user_agent_header():
    """get_ml_token() must send User-Agent: zdailyscan/1.0 to avoid WAF block."""
    from app.analyzers.mercado_livre import get_ml_token

    captured_headers = {}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "tok"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, *, headers, timeout):
        captured_headers.update(headers)
        return mock_resp

    mock_client.get = AsyncMock(side_effect=fake_get)

    env = {"AUTH_BUS_URL": "https://auth-bus.example.com", "AUTH_BUS_API_KEY": "key-123"}
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            await get_ml_token()

    assert captured_headers.get("User-Agent") == "zdailyscan/1.0"


@pytest.mark.asyncio
async def test_get_ml_token_sends_api_key_header():
    """get_ml_token() must send x-api-key header for auth-bus authentication."""
    from app.analyzers.mercado_livre import get_ml_token

    captured_headers = {}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "tok"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, *, headers, timeout):
        captured_headers.update(headers)
        return mock_resp

    mock_client.get = AsyncMock(side_effect=fake_get)

    env = {"AUTH_BUS_URL": "https://auth-bus.example.com", "AUTH_BUS_API_KEY": "my-secret-key"}
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            await get_ml_token()

    assert captured_headers.get("x-api-key") == "my-secret-key"


@pytest.mark.asyncio
async def test_get_ml_token_calls_correct_endpoint():
    """get_ml_token() must call /tokens/mercadolibre on the auth-bus URL."""
    from app.analyzers.mercado_livre import get_ml_token

    captured_url = {}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "tok"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, *, headers, timeout):
        captured_url["url"] = url
        return mock_resp

    mock_client.get = AsyncMock(side_effect=fake_get)

    env = {"AUTH_BUS_URL": "https://auth-bus.example.com", "AUTH_BUS_API_KEY": "key"}
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            await get_ml_token()

    assert captured_url["url"] == "https://auth-bus.example.com/tokens/mercadolibre"


# ── search_br_market() ml_token param ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_br_market_uses_ml_token_param():
    """When ml_token is passed directly, use it as Authorization header."""
    from app.analyzers.mercado_livre import search_br_market

    captured_headers = {}

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [], "paging": {"total": 0}}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, *, params, headers, timeout):
        captured_headers.update(headers)
        return mock_resp

    mock_client.get = AsyncMock(side_effect=fake_get)

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        await search_br_market("test product", ml_token="direct-token-xyz")

    assert captured_headers.get("Authorization") == "Bearer direct-token-xyz"


@pytest.mark.asyncio
async def test_search_br_market_no_auth_when_no_token():
    """When ml_token is empty and ML_USER_ACCESS_TOKEN is unset, send no Authorization."""
    from app.analyzers.mercado_livre import search_br_market

    captured_headers = {}

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [], "paging": {"total": 0}}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, *, params, headers, timeout):
        captured_headers.update(headers)
        return mock_resp

    mock_client.get = AsyncMock(side_effect=fake_get)

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", {}, clear=True):
            await search_br_market("test product", ml_token="")

    assert "Authorization" not in captured_headers


# ── pipeline integration ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_calls_get_ml_token_once():
    """run_daily_scan() must call get_ml_token() exactly once per scan."""
    import app.pipeline as pipeline_mod

    # Minimal product stub
    fake_product = MagicMock()
    fake_product.title = "Widget"
    fake_product.price_usd = 10.0
    fake_product.freight_usd = 2.0
    fake_product.product_id = "p1"

    from app.analyzers.mercado_livre import BRMarket
    fake_market = BRMarket(
        found=False,
        avg_price_brl=None,
        min_price_brl=None,
        max_price_brl=None,
        result_count=0,
        top_listings=[],
    )

    get_ml_token_mock = AsyncMock(return_value="pipeline-token")

    with patch("app.pipeline.get_hot_products", AsyncMock(return_value=[fake_product])):
        with patch("app.pipeline.search_br_market", AsyncMock(return_value=fake_market)) as mock_search:
            with patch("app.pipeline.get_ml_token", get_ml_token_mock):
                with patch("app.pipeline.send_daily_report", AsyncMock()):
                    with patch("app.pipeline.save_daily_report", MagicMock()):
                        await pipeline_mod.run_daily_scan(categories=["200003655"])

    get_ml_token_mock.assert_called_once()
    # Token must be passed to search_br_market
    call_kwargs = mock_search.call_args.kwargs
    assert call_kwargs.get("ml_token") == "pipeline-token"
