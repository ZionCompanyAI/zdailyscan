"""Tests for issue #178: pipeline must pass min_rating=4.9 and use niche keywords."""
from unittest.mock import AsyncMock, call, patch

import pytest


def test_default_keywords_include_samsung():
    """DEFAULT_KEYWORDS must include Samsung niche terms."""
    from app.pipeline import DEFAULT_KEYWORDS

    assert "Samsung" in DEFAULT_KEYWORDS


def test_default_keywords_exclude_off_niche():
    """DEFAULT_KEYWORDS must not include out-of-niche terms."""
    from app.pipeline import DEFAULT_KEYWORDS

    off_niche = ["laptop stand", "bluetooth earphones", "screen protector"]
    for term in off_niche:
        assert term not in DEFAULT_KEYWORDS, f"Off-niche term found: {term!r}"


async def test_pipeline_passes_min_rating_49(monkeypatch):
    """run_daily_scan must call get_hot_products with min_rating=4.9."""
    from app.analyzers.import_calculator import ImportCost
    from app.analyzers.mercado_livre import BRMarket
    from app.aliexpress import AliExpressProduct

    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    market = BRMarket(
        found=True,
        avg_price_brl=500.0,
        min_price_brl=300.0,
        max_price_brl=700.0,
        result_count=200,
        top_listings=[],
    )
    cost = ImportCost(
        price_usd=10.0,
        freight_usd=5.0,
        tax_brl=25.65,
        total_cost_brl=100.0,
        regime="remessa_conforme",
    )

    mock_scraper = AsyncMock(return_value=[])
    with (
        patch("app.pipeline.get_hot_products", mock_scraper),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=market)),
        patch("app.pipeline.calculate_import_cost", return_value=cost),
        patch("app.pipeline.compute_trend_score", return_value=0.5),
    ):
        from app.pipeline import run_daily_scan

        await run_daily_scan()

    assert mock_scraper.called, "get_hot_products deve ser chamado"
    for c in mock_scraper.call_args_list:
        assert c.kwargs.get("min_rating") == 4.9, (
            f"Esperado min_rating=4.9, chamada foi: {c}"
        )
