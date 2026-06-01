import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from app.analyzers.mercado_livre import search_br_market


@pytest.mark.asyncio
async def test_search_br_market_returns_empty_on_403():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("403 Forbidden")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        result = await search_br_market("test product")

    assert result.found is False
    assert result.result_count == 0


@pytest.mark.asyncio
async def test_search_br_market_returns_empty_on_timeout():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        result = await search_br_market("test product")

    assert result.found is False


@pytest.mark.asyncio
async def test_search_br_market_sends_auth_token():
    """Token is now passed as ml_token param (resolved upstream by get_ml_token)."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"results": [], "paging": {"total": 0}}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient", return_value=mock_client):
        await search_br_market("test product", ml_token="tok-abc")

    call_kwargs = mock_client.get.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer tok-abc"
