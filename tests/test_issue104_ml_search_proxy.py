"""
TASK-104 — search_br_market() usa ML_SEARCH_PROXY_URL quando configurada;
fallback para ML direto quando proxy falha; trata 403 PolicyAgent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


ML_RESULTS = {
    "results": [
        {"price": 120.0, "permalink": "https://www.mercadolivre.com.br/a"},
        {"price": 180.0, "permalink": "https://www.mercadolivre.com.br/b"},
    ],
    "paging": {"total": 2},
}

ML_EMPTY = {"results": [], "paging": {"total": 0}}


def _make_mock_client(responses: dict):
    """responses: {url_substring: mock_response | Exception}"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, **kwargs):
        for substr, resp in responses.items():
            if substr in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp
        raise AssertionError(f"Unexpected URL in fake_get: {url}")

    mock_client.get = fake_get
    return mock_client


def _mock_resp(json_body, status=200):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_body
    if status >= 400:
        import httpx
        r.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"{status}", request=MagicMock(), response=MagicMock()
        )
    else:
        r.raise_for_status = MagicMock()
    return r


# ---------------------------------------------------------------------------
# 1. Proxy usado quando ML_SEARCH_PROXY_URL configurada
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_uses_proxy_url_when_configured():
    """Quando ML_SEARCH_PROXY_URL set, chamada vai ao proxy, não direto ao ML."""
    from app.analyzers.mercado_livre import search_br_market

    proxy_resp = _mock_resp(ML_RESULTS)
    urls_called = []

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, **kwargs):
        urls_called.append(url)
        return proxy_resp

    mock_client.get = fake_get

    env = {
        "ML_SEARCH_PROXY_URL": "https://proxy.example.com/ml-search",
        "ML_USER_ACCESS_TOKEN": "tok",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            result = await search_br_market("tênis")

    assert result.found is True
    assert result.result_count == 2
    assert len(urls_called) >= 1
    assert any("proxy.example.com" in u for u in urls_called), (
        f"Proxy não chamado; URLs chamadas: {urls_called}"
    )
    assert not any("mercadolibre.com" in u for u in urls_called), (
        "ML direto chamado quando proxy deveria ser usado"
    )


# ---------------------------------------------------------------------------
# 2. Proxy falha → fallback para ML direto
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proxy_failure_falls_back_to_direct_ml():
    """Quando proxy levanta exceção, fallback para ML direto sem propagar erro."""
    from app.analyzers.mercado_livre import search_br_market

    ml_resp = _mock_resp(ML_RESULTS)
    urls_called = []

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, **kwargs):
        urls_called.append(url)
        if "proxy.example.com" in url:
            raise Exception("proxy down")
        return ml_resp

    mock_client.get = fake_get

    env = {
        "ML_SEARCH_PROXY_URL": "https://proxy.example.com/ml-search",
        "ML_USER_ACCESS_TOKEN": "tok",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            result = await search_br_market("camiseta")

    assert result.found is True
    assert any("proxy.example.com" in u for u in urls_called), "Proxy deve ter sido tentado"
    assert any("mercadolibre.com" in u for u in urls_called), "ML direto deve ser fallback"


# ---------------------------------------------------------------------------
# 3. ML direto retorna 403 (PolicyAgent) → BRMarket(found=False)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_direct_ml_403_returns_not_found():
    """403 PA_UNAUTHORIZED da ML direto → BRMarket(found=False), sem exceção."""
    from app.analyzers.mercado_livre import search_br_market
    import httpx

    mock_resp_403 = MagicMock()
    mock_resp_403.status_code = 403
    mock_resp_403.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403", request=MagicMock(), response=MagicMock()
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp_403)

    env = {"ML_USER_ACCESS_TOKEN": "tok"}
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            import os
            os.environ.pop("ML_SEARCH_PROXY_URL", None)
            result = await search_br_market("produto bloqueado")

    assert result.found is False
    assert result.result_count == 0
    assert result.avg_price_brl is None


# ---------------------------------------------------------------------------
# 4. Sem ML_SEARCH_PROXY_URL → comportamento direto intacto
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_proxy_uses_direct_ml_url():
    """Quando ML_SEARCH_PROXY_URL ausente, chama api.mercadolibre.com diretamente."""
    from app.analyzers.mercado_livre import search_br_market

    ml_resp = _mock_resp(ML_RESULTS)
    urls_called = []

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def fake_get(url, **kwargs):
        urls_called.append(url)
        return ml_resp

    mock_client.get = fake_get

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("ML_SEARCH_PROXY_URL", None)
            os.environ.pop("AUTH_BUS_URL", None)
            os.environ.pop("AUTH_BUS_API_KEY", None)
            result = await search_br_market("notebook")

    assert result.found is True
    assert all("mercadolibre.com" in u for u in urls_called), (
        f"Esperado ML direto; URLs chamadas: {urls_called}"
    )


# ---------------------------------------------------------------------------
# 5. Proxy retorna non-2xx → fallback para ML direto
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proxy_non_2xx_falls_back_to_direct_ml():
    """Quando proxy retorna 502, fallback para ML direto."""
    from app.analyzers.mercado_livre import search_br_market
    import httpx

    ml_resp = _mock_resp(ML_RESULTS)
    urls_called = []

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    proxy_resp_502 = MagicMock()
    proxy_resp_502.status_code = 502
    proxy_resp_502.raise_for_status.side_effect = httpx.HTTPStatusError(
        "502", request=MagicMock(), response=MagicMock()
    )

    async def fake_get(url, **kwargs):
        urls_called.append(url)
        if "proxy.example.com" in url:
            return proxy_resp_502
        return ml_resp

    mock_client.get = fake_get

    env = {
        "ML_SEARCH_PROXY_URL": "https://proxy.example.com/ml-search",
        "ML_USER_ACCESS_TOKEN": "tok",
    }
    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", env, clear=False):
            result = await search_br_market("monitor")

    assert result.found is True
    assert any("proxy.example.com" in u for u in urls_called)
    assert any("mercadolibre.com" in u for u in urls_called)
