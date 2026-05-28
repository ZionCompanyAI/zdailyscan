import pytest
from unittest.mock import AsyncMock, patch, MagicMock


ML_SEARCH_RESPONSE = {
    "results": [
        {"price": 150.0, "permalink": "https://www.mercadolivre.com.br/p1"},
        {"price": 200.0, "permalink": "https://www.mercadolivre.com.br/p2"},
        {"price": 100.0, "permalink": "https://www.mercadolivre.com.br/p3"},
        {"price": 175.0, "permalink": "https://www.mercadolivre.com.br/p4"},
    ]
}

ML_EMPTY_RESPONSE = {"results": []}


@pytest.mark.asyncio
async def test_ml_search_returns_prices():
    from app.analyzers.mercado_livre import search_br_market

    mock_response = MagicMock()
    mock_response.json.return_value = ML_SEARCH_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await search_br_market("fone bluetooth")

    assert result.found is True
    assert result.result_count == 4
    assert result.avg_price_brl is not None
    assert result.avg_price_brl > 0
    assert result.min_price_brl == 100.0
    assert result.max_price_brl == 200.0
    assert len(result.top_listings) <= 3
    assert "https://www.mercadolivre.com.br/p1" in result.top_listings


@pytest.mark.asyncio
async def test_ml_search_empty_returns_not_found():
    from app.analyzers.mercado_livre import search_br_market

    mock_response = MagicMock()
    mock_response.json.return_value = ML_EMPTY_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("app.analyzers.mercado_livre.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await search_br_market("produto inexistente xyzxyz")

    assert result.found is False
    assert result.result_count == 0
    assert result.avg_price_brl is None
    assert result.min_price_brl is None
    assert result.max_price_brl is None
    assert result.top_listings == []


def test_import_cost_remessa_conforme():
    from app.analyzers.import_calculator import calculate_import_cost

    # price_usd + freight_usd = 35.0 ≤ 50 → remessa_conforme
    result = calculate_import_cost(price_usd=30.0, freight_usd=5.0)

    assert result.regime == "remessa_conforme"
    assert result.price_usd == 30.0
    assert result.freight_usd == 5.0
    assert result.tax_brl > 0
    assert result.total_cost_brl > result.tax_brl

    # Verify math: base = 35 * 5.70 = 199.50, ii = 20% = 39.90, icms = 17% = 33.915
    rate = 5.70
    base = 35.0 * rate
    expected_ii = 0.20 * base
    expected_icms = 0.17 * base
    expected_tax = expected_ii + expected_icms
    expected_total = base + expected_tax

    assert abs(result.tax_brl - expected_tax) < 0.01
    assert abs(result.total_cost_brl - expected_total) < 0.01


def test_import_cost_normal_regime():
    from app.analyzers.import_calculator import calculate_import_cost

    # price_usd + freight_usd = 65.0 > 50 → normal
    result = calculate_import_cost(price_usd=60.0, freight_usd=5.0)

    assert result.regime == "normal"
    assert result.price_usd == 60.0
    assert result.freight_usd == 5.0
    assert result.tax_brl > 0
    assert result.total_cost_brl > result.tax_brl

    # Verify math: base = 65 * 5.70 = 370.50, ii = 60% = 222.30
    # icms = (base + ii) * 0.17 / (1 - 0.17)
    rate = 5.70
    base = 65.0 * rate
    expected_ii = 0.60 * base
    expected_icms = (base + expected_ii) * 0.17 / (1 - 0.17)
    expected_tax = expected_ii + expected_icms
    expected_total = base + expected_tax

    assert abs(result.tax_brl - expected_tax) < 0.01
    assert abs(result.total_cost_brl - expected_total) < 0.01


def test_import_cost_boundary_50_usd():
    from app.analyzers.import_calculator import calculate_import_cost

    # Exactly 50 → remessa_conforme
    result = calculate_import_cost(price_usd=45.0, freight_usd=5.0)
    assert result.regime == "remessa_conforme"


def test_import_cost_above_50_usd():
    from app.analyzers.import_calculator import calculate_import_cost

    # 50.01 → normal
    result = calculate_import_cost(price_usd=45.01, freight_usd=5.0)
    assert result.regime == "normal"
