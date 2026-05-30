import json
from unittest.mock import AsyncMock, patch

from app.analyzers.import_calculator import ImportCost
from app.analyzers.mercado_livre import BRMarket


def _ali_products(n: int):
    from app.aliexpress import AliExpressProduct

    return [
        AliExpressProduct(product_id=f"p{i}", title=f"Product {i}", price_usd=10.0)
        for i in range(n)
    ]


def _market(result_count: int = 200) -> BRMarket:
    return BRMarket(
        found=True,
        avg_price_brl=500.0,
        min_price_brl=300.0,
        max_price_brl=700.0,
        result_count=result_count,
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


async def test_pipeline_returns_top20(monkeypatch):
    """run_daily_scan retorna no máximo 20 produtos viáveis."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1", "cat2"])

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_ali_products(15))),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
    ):
        from app.pipeline import run_daily_scan, ScanResult

        result = await run_daily_scan()

    assert isinstance(result, ScanResult)
    # 2 categories × 15 products = 30 total; top 20 after filter
    assert len(result.products) <= 20
    assert result.total_scanned == 30


async def test_results_sorted_by_score(monkeypatch):
    """Produtos retornados estão ordenados por score_total decrescente."""
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])

    markets = [
        _market(result_count=10),  # menor score_demanda → score mais baixo
        _market(result_count=50),
        _market(result_count=100),  # maior score_demanda → score mais alto
    ]

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_ali_products(3))),
        patch("app.pipeline.search_br_market", AsyncMock(side_effect=markets)),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
    ):
        from app.pipeline import run_daily_scan

        result = await run_daily_scan()

    scores = [p.score_total for p in result.products]
    assert scores == sorted(scores, reverse=True)
    assert len(scores) == 3  # todos viáveis com esses valores


async def test_scan_persisted_to_json(tmp_path, monkeypatch):
    """save_scan cria YYYY-MM-DD.json com estrutura correta."""
    import app.storage as storage_module

    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_ali_products(2))),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
    ):
        from app.pipeline import run_daily_scan
        from app.storage import save_scan

        result = await run_daily_scan()
        path = save_scan(result)

    assert path.exists()
    data = json.loads(path.read_text())
    assert data["date"] == result.date
    assert "products" in data
    assert data["scan_id"] == result.scan_id
