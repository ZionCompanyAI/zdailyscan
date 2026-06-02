"""Testes para filtro de produtos non-tech em scan de categorias (issue #137)."""
from unittest.mock import AsyncMock, patch

import pytest

from app.analyzers.import_calculator import ImportCost
from app.analyzers.mercado_livre import BRMarket


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ali_products(titles: list[str]):
    from app.aliexpress import AliExpressProduct

    return [
        AliExpressProduct(product_id=f"p{i}", title=title, price_usd=10.0)
        for i, title in enumerate(titles)
    ]


def _market() -> BRMarket:
    return BRMarket(
        found=True,
        avg_price_brl=500.0,
        min_price_brl=300.0,
        max_price_brl=700.0,
        result_count=200,
        top_listings=[],
    )


def _cost() -> ImportCost:
    return ImportCost(
        price_usd=10.0,
        freight_usd=5.0,
        tax_brl=25.65,
        total_cost_brl=100.0,
        regime="remessa_conforme",
    )


# ---------------------------------------------------------------------------
# Unit tests — is_tech_product()
# ---------------------------------------------------------------------------

class TestIsTechProduct:
    def test_usb_hub_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("USB-C Hub 7-in-1 Multiport Adapter") is True

    def test_hdmi_adapter_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("HDMI Adapter 4K 60Hz") is True

    def test_bluetooth_earphone_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Bluetooth Earphones Wireless") is True

    def test_wireless_charger_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Wireless Charger 15W Fast Charging") is True

    def test_type_c_cable_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Type-C to USB Cable 2m") is True

    def test_power_bank_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Power Bank 20000mAh PD45W") is True

    def test_men_fashion_pants_not_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Men Fashion Quick Dry Pants") is False

    def test_casual_pants_not_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Men's Casual Pants Baggy Streetwear") is False

    def test_women_cardigan_not_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Summer Women Thin Sunscreen Cardigan") is False

    def test_case_insensitive(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("BLUETOOTH SPEAKER") is True
        assert is_tech_product("bluetooth speaker") is True
        assert is_tech_product("Bluetooth Speaker") is True

    def test_type_c_with_space(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Type C Charging Cable Fast") is True

    def test_docking_station_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Docking Station USB-C 12-in-1") is True

    def test_laptop_stand_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Laptop Stand Adjustable Aluminum") is True

    def test_ssd_is_tech(self):
        from app.pipeline import is_tech_product
        assert is_tech_product("Portable SSD 1TB USB 3.2 Gen2") is True


# ---------------------------------------------------------------------------
# Integration tests — pipeline filter behaviour
# ---------------------------------------------------------------------------

async def test_category_scan_fashion_product_not_viable(monkeypatch):
    """Produto fashion em scan de categoria → viavel=False, score_total=0.0."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    fashion_titles = [
        "Men Fashion Quick Dry Pants",
        "Summer Women Thin Sunscreen Cardigan",
    ]

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_ali_products(fashion_titles))),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())) as mock_market,
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
        patch("app.pipeline.compute_trend_score", return_value=0.5),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    assert result.total_viable == 0, "Fashion products must not be viable"
    assert result.total_scanned == 2

    for p in result.products:
        assert p.viavel is False
        assert p.score_total == 0.0

    # search_br_market must NOT be called for non-tech products (no wasted API calls)
    mock_market.assert_not_called()


async def test_category_scan_tech_product_scored_normally(monkeypatch):
    """Produto tech em scan de categoria → scoring normal, pode ser viável."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    tech_titles = ["USB-C Hub 7-in-1 Multiport Adapter"]

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_ali_products(tech_titles))),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())) as mock_market,
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
        patch("app.pipeline.compute_trend_score", return_value=0.5),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    assert result.total_scanned == 1
    # search_br_market was called for tech products
    mock_market.assert_called_once()
    # Tech product with good market → should be viable
    assert result.total_viable == 1


async def test_category_scan_mixed_products(monkeypatch):
    """Scan de categoria com mistura: fashion bloqueado, tech pontuado."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    mixed_titles = [
        "USB Hub 4 Port USB 3.0",           # tech
        "Men Fashion Quick Dry Pants",       # fashion
        "HDMI Cable 2m 4K",                 # tech
        "Summer Women Cardigan",            # fashion
    ]

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_ali_products(mixed_titles))),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())) as mock_market,
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
        patch("app.pipeline.compute_trend_score", return_value=0.5),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    assert result.total_scanned == 4
    # Only 2 tech products should be viable
    assert result.total_viable == 2
    # search_br_market called only for tech products (2 times)
    assert mock_market.call_count == 2


async def test_keyword_scan_fashion_product_not_filtered(monkeypatch):
    """Produto fashion em scan de KEYWORD → sem filtro (comportamento atual mantido)."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", [])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: ["fashion pants"])

    fashion_titles = ["Men Fashion Quick Dry Pants"]

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_ali_products(fashion_titles))),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())) as mock_market,
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
        patch("app.pipeline.compute_trend_score", return_value=0.5),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    # Keyword scans are NOT filtered — market must be called
    mock_market.assert_called_once()
    assert result.total_scanned == 1
