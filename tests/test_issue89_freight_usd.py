"""Tests for issue #89: AliProduct missing freight_usd crashes pipeline."""
import pytest
from unittest.mock import AsyncMock, patch

from app.scrapers.models import AliProduct
from app.analyzers.import_calculator import calculate_import_cost, ImportCost
from app.analyzers.mercado_livre import BRMarket


# --- Layer 1: direct attribute test ---

def test_aliproduct_has_freight_usd_default():
    """AliProduct must have freight_usd with default 0.0."""
    product = AliProduct(
        product_id="p1",
        title="Test Product",
        price_usd=25.0,
        sale_count_30d=100,
        rating=4.5,
        image_url="https://example.com/img.jpg",
        product_url="https://aliexpress.com/item/p1.html",
        category_id="200003655",
    )
    assert hasattr(product, "freight_usd")
    assert product.freight_usd == 0.0


def test_aliproduct_freight_usd_can_be_set():
    """freight_usd can be overridden when provided."""
    product = AliProduct(
        product_id="p2",
        title="Test Product",
        price_usd=25.0,
        sale_count_30d=50,
        rating=4.0,
        image_url="https://example.com/img.jpg",
        product_url="https://aliexpress.com/item/p2.html",
        category_id="200003655",
        freight_usd=3.5,
    )
    assert product.freight_usd == 3.5


# --- Layer 2: pipeline contract test ---

def test_aliproduct_real_passes_calculate_import_cost():
    """Real AliProduct can be passed to calculate_import_cost without AttributeError."""
    product = AliProduct(
        product_id="p3",
        title="Test Product",
        price_usd=20.0,
        sale_count_30d=80,
        rating=4.2,
        image_url="https://example.com/img.jpg",
        product_url="https://aliexpress.com/item/p3.html",
        category_id="200003655",
    )
    cost = calculate_import_cost(product.price_usd, product.freight_usd)
    assert isinstance(cost, ImportCost)
    assert cost.price_usd == 20.0
    assert cost.freight_usd == 0.0


# --- Layer 3: integration test (mock only external HTTP) ---

def _make_ali_product(i: int) -> AliProduct:
    return AliProduct(
        product_id=f"p{i}",
        title=f"Product {i}",
        price_usd=15.0,
        sale_count_30d=120,
        rating=4.3,
        image_url=f"https://example.com/img{i}.jpg",
        product_url=f"https://aliexpress.com/item/p{i}.html",
        category_id="200003655",
    )


def _make_market() -> BRMarket:
    return BRMarket(
        found=True,
        avg_price_brl=300.0,
        min_price_brl=200.0,
        max_price_brl=400.0,
        result_count=150,
        top_listings=[],
    )


@pytest.mark.asyncio
async def test_run_daily_scan_no_attributeerror_with_real_aliproduct(monkeypatch):
    """run_daily_scan must complete without AttributeError using real AliProduct instances."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["200003655"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    real_products = [_make_ali_product(i) for i in range(3)]

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=real_products)),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_make_market())),
        patch("app.pipeline.send_daily_report", AsyncMock()),
        patch("app.pipeline.save_daily_report", return_value=None),
    ):
        from app.pipeline import run_daily_scan, ScanResult

        result = await run_daily_scan()

    assert isinstance(result, ScanResult)
    assert result.total_scanned == 3
