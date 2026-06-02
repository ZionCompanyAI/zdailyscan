"""Tests for TASK-128: trend_analyzer — 1688.com + Google Trends BR."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.analyzers.trend_analyzer import (
    TrendSignal,
    _extract_keyword,
    compute_trend_score,
    fetch_1688_trending,
    fetch_google_trends_br,
)
from app.scoring.scorer import AliProduct, score_product
from app.analyzers.mercado_livre import BRMarket
from app.analyzers.import_calculator import ImportCost


# ---------------------------------------------------------------------------
# _extract_keyword
# ---------------------------------------------------------------------------

def test_extract_keyword_three_words():
    assert _extract_keyword("USB-C Hub Adapter 7-in-1") == "USB-C Hub Adapter"


def test_extract_keyword_short_title():
    assert _extract_keyword("Fone") == "Fone"


def test_extract_keyword_two_words():
    assert _extract_keyword("Smart Watch") == "Smart Watch"


def test_extract_keyword_strips_extra_spaces():
    assert _extract_keyword("  LED Strip  Light RGB") == "LED Strip Light"


# ---------------------------------------------------------------------------
# TrendSignal dataclass
# ---------------------------------------------------------------------------

def test_trend_signal_creation():
    ts = TrendSignal(title="USB-C Hub", sales_volume="1234+")
    assert ts.title == "USB-C Hub"
    assert ts.sales_volume == "1234+"


# ---------------------------------------------------------------------------
# fetch_google_trends_br
# ---------------------------------------------------------------------------

def test_fetch_google_trends_br_returns_normalized_score():
    """Returns dict with float 0-1 for each keyword."""
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.__getitem__ = MagicMock(return_value=MagicMock(mean=MagicMock(return_value=75.0)))

    with patch("app.analyzers.trend_analyzer.TrendReq") as MockTrendReq:
        mock_tr = MockTrendReq.return_value
        mock_tr.interest_over_time.return_value = mock_df
        result = fetch_google_trends_br(["USB-C Hub"])

    assert "USB-C Hub" in result
    assert 0.0 <= result["USB-C Hub"] <= 1.0


def test_fetch_google_trends_br_returns_empty_on_error():
    """Returns {} if pytrends raises any exception."""
    with patch("app.analyzers.trend_analyzer.TrendReq") as MockTrendReq:
        mock_tr = MockTrendReq.return_value
        mock_tr.interest_over_time.side_effect = Exception("rate limit")
        result = fetch_google_trends_br(["USB-C Hub"])

    assert result == {}


def test_fetch_google_trends_br_empty_dataframe():
    """Returns {} if the dataframe is empty (no data for keyword)."""
    mock_df = MagicMock()
    mock_df.empty = True

    with patch("app.analyzers.trend_analyzer.TrendReq") as MockTrendReq:
        mock_tr = MockTrendReq.return_value
        mock_tr.interest_over_time.return_value = mock_df
        result = fetch_google_trends_br(["obscure keyword"])

    assert result == {}


def test_fetch_google_trends_br_score_clamped():
    """Score stays in [0,1] even if mean exceeds 100 due to mock."""
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.__getitem__ = MagicMock(return_value=MagicMock(mean=MagicMock(return_value=150.0)))

    with patch("app.analyzers.trend_analyzer.TrendReq") as MockTrendReq:
        mock_tr = MockTrendReq.return_value
        mock_tr.interest_over_time.return_value = mock_df
        result = fetch_google_trends_br(["keyword"])

    if result:
        for v in result.values():
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# fetch_1688_trending
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_1688_trending_returns_list():
    """Returns list[TrendSignal] on successful Firecrawl response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "extract": [
                {"title": "USB Hub Adapter", "sales": "5000+"},
                {"title": "Type-C Dock", "sales": "3200+"},
            ]
        }
    }

    with patch("app.analyzers.trend_analyzer.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value
        mock_client.post = AsyncMock(return_value=mock_response)
        result = await fetch_1688_trending("USB hub")

    assert isinstance(result, list)
    assert all(isinstance(ts, TrendSignal) for ts in result)


@pytest.mark.asyncio
async def test_fetch_1688_trending_returns_empty_on_error():
    """Returns [] if Firecrawl request fails."""
    with patch("app.analyzers.trend_analyzer.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value
        mock_client.post = AsyncMock(side_effect=Exception("connection error"))
        result = await fetch_1688_trending("USB hub")

    assert result == []


@pytest.mark.asyncio
async def test_fetch_1688_trending_non_200_returns_empty():
    """Returns [] on non-200 HTTP status."""
    mock_response = MagicMock()
    mock_response.status_code = 403

    with patch("app.analyzers.trend_analyzer.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value
        mock_client.post = AsyncMock(return_value=mock_response)
        result = await fetch_1688_trending("USB hub")

    assert result == []


# ---------------------------------------------------------------------------
# compute_trend_score — cache + fallback
# ---------------------------------------------------------------------------

def test_compute_trend_score_returns_float_in_range():
    """compute_trend_score returns float 0-1."""
    with patch("app.analyzers.trend_analyzer.fetch_google_trends_br") as mock_gt:
        mock_gt.return_value = {"USB-C Hub": 0.75}
        score = compute_trend_score("USB-C Hub Adapter 7-in-1")

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_compute_trend_score_fallback_on_failure():
    """Falls back to 0.5 when all trend sources fail."""
    with patch("app.analyzers.trend_analyzer.fetch_google_trends_br") as mock_gt:
        mock_gt.return_value = {}
        score = compute_trend_score("Some obscure product XYZ 999")

    assert score == pytest.approx(0.5)


def test_compute_trend_score_cache_hit(monkeypatch):
    """Second call for same keyword uses cached value without calling pytrends again."""
    import app.analyzers.trend_analyzer as ta

    # Use a single-word title so _extract_keyword returns it unchanged
    keyword = "__testcachekw__"
    ta._trend_cache[keyword] = (0.88, datetime.now(timezone.utc).replace(tzinfo=None))

    with patch("app.analyzers.trend_analyzer.fetch_google_trends_br") as mock_gt:
        score = compute_trend_score(keyword)
        mock_gt.assert_not_called()

    assert score == pytest.approx(0.88)
    del ta._trend_cache[keyword]


def test_compute_trend_score_cache_expired(monkeypatch):
    """Expired cache entry triggers fresh fetch."""
    import app.analyzers.trend_analyzer as ta

    keyword = "__testexpiredkw__"
    ta._trend_cache[keyword] = (0.88, datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=25))

    with patch("app.analyzers.trend_analyzer.fetch_google_trends_br") as mock_gt:
        mock_gt.return_value = {keyword: 0.42}
        compute_trend_score(keyword)
        mock_gt.assert_called_once()

    ta._trend_cache.pop(keyword, None)


# ---------------------------------------------------------------------------
# scorer.py integration — trend_score param
# ---------------------------------------------------------------------------

def _make_market(avg_price: float, result_count: int) -> BRMarket:
    return BRMarket(
        found=True,
        avg_price_brl=avg_price,
        min_price_brl=avg_price * 0.8,
        max_price_brl=avg_price * 1.2,
        result_count=result_count,
        top_listings=[],
    )


def _make_cost(price_usd: float, total_cost_brl: float) -> ImportCost:
    return ImportCost(
        price_usd=price_usd,
        freight_usd=5.0,
        tax_brl=total_cost_brl * 0.3,
        total_cost_brl=total_cost_brl,
        regime="remessa_conforme",
    )


def test_score_product_accepts_custom_trend_score():
    """score_product uses provided trend_score instead of hardcoded 0.5."""
    ali = AliProduct(product_id="p1", title="USB-C Hub")
    market = _make_market(avg_price=200.0, result_count=200)
    cost = _make_cost(price_usd=30.0, total_cost_brl=60.0)

    result_low = score_product(ali, market, cost, trend_score=0.0)
    result_high = score_product(ali, market, cost, trend_score=1.0)

    assert result_low.score_tendencia == pytest.approx(0.0)
    assert result_high.score_tendencia == pytest.approx(1.0)
    assert result_high.score_total > result_low.score_total


def test_score_product_default_trend_score_is_half():
    """Default trend_score=0.5 keeps backward-compat."""
    ali = AliProduct(product_id="p1", title="Fone Bluetooth")
    market = _make_market(avg_price=150.0, result_count=80)
    cost = _make_cost(price_usd=7.0, total_cost_brl=40.0)

    result = score_product(ali, market, cost)

    assert result.score_tendencia == pytest.approx(0.5)


def test_score_product_trend_score_in_formula():
    """score_total accounts for trend_score at 0.15 weight."""
    ali = AliProduct(product_id="px", title="Test Product")
    market = _make_market(avg_price=200.0, result_count=200)
    cost = _make_cost(price_usd=30.0, total_cost_brl=60.0)

    result_05 = score_product(ali, market, cost, trend_score=0.5)
    result_10 = score_product(ali, market, cost, trend_score=1.0)

    # Difference should be 0.15 * (1.0 - 0.5) = 0.075
    diff = result_10.score_total - result_05.score_total
    assert diff == pytest.approx(0.075, abs=0.001)