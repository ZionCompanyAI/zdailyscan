"""TASK-137: filtrar produtos não-tech do scan de categorias."""
from unittest.mock import AsyncMock, patch

from app.analyzers.import_calculator import ImportCost
from app.analyzers.mercado_livre import BRMarket


def _cost() -> ImportCost:
    return ImportCost(
        price_usd=10.0,
        freight_usd=5.0,
        tax_brl=25.65,
        total_cost_brl=100.0,
        regime="remessa_conforme",
    )


def _market(result_count: int = 200) -> BRMarket:
    return BRMarket(
        found=True,
        avg_price_brl=500.0,
        min_price_brl=300.0,
        max_price_brl=700.0,
        result_count=result_count,
        top_listings=[],
    )


# --- unit tests for is_tech_product ---

def test_is_tech_product_usb_hub_passes():
    from app.pipeline import is_tech_product
    assert is_tech_product("USB Hub Multiport 7 Port USB 3.0 Hub with SD Card Reader") is True


def test_is_tech_product_hdmi_adapter_passes():
    from app.pipeline import is_tech_product
    assert is_tech_product("4K HDMI Adapter Type-C to HDMI 60Hz") is True


def test_is_tech_product_charger_passes():
    from app.pipeline import is_tech_product
    assert is_tech_product("65W GaN Wireless Charger Fast Charging") is True


def test_is_tech_product_bluetooth_earphone_passes():
    from app.pipeline import is_tech_product
    assert is_tech_product("Bluetooth Earphone TWS Pro Active Noise Cancelling") is True


def test_is_tech_product_keyboard_passes():
    from app.pipeline import is_tech_product
    assert is_tech_product("Mechanical Keyboard RGB Backlit TKL") is True


def test_is_tech_product_power_bank_passes():
    from app.pipeline import is_tech_product
    assert is_tech_product("20000mAh Power Bank Slim Fast Charge") is True


def test_is_tech_product_fashion_pants_blocked():
    from app.pipeline import is_tech_product
    assert is_tech_product("Men Fashion Quick Dry Pants Casual Streetwear") is False


def test_is_tech_product_streetwear_blocked():
    from app.pipeline import is_tech_product
    assert is_tech_product("Men's Casual Pants Baggy Streetwear Hip Hop") is False


def test_is_tech_product_cardigan_blocked():
    from app.pipeline import is_tech_product
    assert is_tech_product("Summer Women Thin Sunscreen Cardigan Long Sleeve") is False


def test_is_tech_product_case_insensitive():
    from app.pipeline import is_tech_product
    assert is_tech_product("USB-C ADAPTER THUNDERBOLT 4") is True


# --- pipeline integration tests ---

def _fashion_products():
    from app.aliexpress import AliExpressProduct
    return [
        AliExpressProduct(product_id="f1", title="Men Fashion Quick Dry Pants", price_usd=12.0),
        AliExpressProduct(product_id="f2", title="Summer Women Sunscreen Cardigan", price_usd=8.0),
        AliExpressProduct(product_id="f3", title="Casual Baggy Streetwear Joggers", price_usd=10.0),
    ]


def _tech_products():
    from app.aliexpress import AliExpressProduct
    return [
        AliExpressProduct(product_id="t1", title="USB Hub 7-Port 3.0 with Ethernet", price_usd=15.0),
        AliExpressProduct(product_id="t2", title="HDMI Adapter 4K Type-C Thunderbolt", price_usd=12.0),
    ]


async def test_pipeline_fashion_products_not_viable(monkeypatch):
    """Produtos fashion nunca aparecem como viáveis no resultado."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_fashion_products())),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    assert result.total_viable == 0
    assert len(result.products) == 0


async def test_pipeline_fashion_counted_in_total_scanned(monkeypatch):
    """Produtos fashion contam em total_scanned mesmo sendo filtrados."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_fashion_products())),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    assert result.total_scanned == 3


async def test_pipeline_tech_products_still_viable(monkeypatch):
    """Produtos tech com boa margem continuam viáveis."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_tech_products())),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    assert result.total_viable == 2
    assert len(result.products) == 2


async def test_pipeline_mixed_only_tech_viable(monkeypatch):
    """Scan misto: só os tech aparecem como viáveis."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    mixed = _fashion_products() + _tech_products()

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=mixed)),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    assert result.total_scanned == 5
    assert result.total_viable == 2
    assert all(p.viavel for p in result.products)
    titles = [p.title for p in result.products]
    assert all("usb" in t.lower() or "hdmi" in t.lower() or "adapter" in t.lower()
               or "hub" in t.lower() or "ethernet" in t.lower() or "thunderbolt" in t.lower()
               for t in titles)
