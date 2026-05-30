import pytest

from app.analyzers.mercado_livre import BRMarket
from app.analyzers.import_calculator import ImportCost
from app.scoring.scorer import AliProduct, ProductScore, score_product


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


def test_viable_product_score():
    # avg_price_brl=150, total_cost_brl=40, result_count=80 → viavel=True
    ali = AliProduct(product_id="p1", title="Fone Bluetooth")
    market = _make_market(avg_price=150.0, result_count=80)
    cost = _make_cost(price_usd=7.0, total_cost_brl=40.0)

    result = score_product(ali, market, cost)

    assert isinstance(result, ProductScore)
    assert result.product_id == "p1"
    assert result.title == "Fone Bluetooth"
    assert result.viavel is True
    assert result.score_total >= 0.60
    assert result.sell_price_suggestion_brl == pytest.approx(100.0, abs=0.01)


def test_unviable_product_score():
    # avg_price_brl=45, total_cost_brl=42, result_count=800 → viavel=False
    ali = AliProduct(product_id="p2", title="Produto saturado")
    market = _make_market(avg_price=45.0, result_count=800)
    cost = _make_cost(price_usd=7.0, total_cost_brl=42.0)

    result = score_product(ali, market, cost)

    assert result.viavel is False
    assert result.score_total < 0.60
    assert result.sell_price_suggestion_brl == pytest.approx(105.0, abs=0.01)


def test_score_bounds():
    # score_total must always be between 0.0 and 1.0
    for avg_price, cost_brl, count in [
        (1.0, 0.5, 0),
        (100.0, 99.0, 1000),
        (200.0, 10.0, 50),
        (50.0, 50.0, 500),  # zero margin → margem = 0
        (50.0, 55.0, 100),  # negative margin → clamp to 0
    ]:
        ali = AliProduct(product_id="px", title="Test")
        market = _make_market(avg_price=avg_price, result_count=count)
        cost = _make_cost(price_usd=7.0, total_cost_brl=cost_brl)
        result = score_product(ali, market, cost)
        assert (
            0.0 <= result.score_total <= 1.0
        ), f"score_total={result.score_total} out of bounds for avg={avg_price} cost={cost_brl}"


def test_score_dimensions_logistica():
    ali = AliProduct(product_id="px", title="Test")
    market = _make_market(avg_price=100.0, result_count=50)

    # price_usd ≤ 50 → logistica = 1.0
    cost_low = _make_cost(price_usd=30.0, total_cost_brl=40.0)
    r_low = score_product(ali, market, cost_low)
    assert r_low.score_logistica == 1.0

    # price_usd ≤ 100 (but > 50) → logistica = 0.6
    cost_mid = _make_cost(price_usd=75.0, total_cost_brl=40.0)
    r_mid = score_product(ali, market, cost_mid)
    assert r_mid.score_logistica == 0.6

    # price_usd > 100 → logistica = 0.3
    cost_high = _make_cost(price_usd=150.0, total_cost_brl=40.0)
    r_high = score_product(ali, market, cost_high)
    assert r_high.score_logistica == 0.3


def test_score_formula_weights():
    ali = AliProduct(product_id="px", title="Test")
    market = _make_market(avg_price=200.0, result_count=200)
    cost = _make_cost(price_usd=30.0, total_cost_brl=60.0)

    result = score_product(ali, market, cost)

    # Margem: (200-60)/200 = 0.70
    # Demanda: min(200/100, 1.0) = 1.0
    # Oportunidade: 1 - min(200/500, 1.0) = 1 - 0.40 = 0.60
    # Tendencia: 0.5
    # Logistica: 1.0 (price_usd=30 ≤ 50)
    expected = 0.30 * 0.70 + 0.25 * 1.0 + 0.20 * 0.60 + 0.15 * 0.5 + 0.10 * 1.0
    assert result.score_total == pytest.approx(expected, abs=0.001)
    assert result.score_margem == pytest.approx(0.70, abs=0.001)
    assert result.score_demanda_br == pytest.approx(1.0, abs=0.001)
    assert result.score_oportunidade == pytest.approx(0.60, abs=0.001)
    assert result.score_tendencia == pytest.approx(0.5, abs=0.001)
    assert result.score_logistica == pytest.approx(1.0, abs=0.001)
