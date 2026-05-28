import pytest
from app.models import AliProduct, BRMarket, ImportCost
from app.scoring.scorer import score_product


def _viable_inputs():
    ali = AliProduct(product_id="p1", title="Produto Viável", price_usd=30.0)
    market = BRMarket(avg_price_brl=150.0, result_count=80)
    cost = ImportCost(total_cost_brl=40.0)
    return ali, market, cost


def _unviable_inputs():
    ali = AliProduct(product_id="p2", title="Produto Inviável", price_usd=120.0)
    market = BRMarket(avg_price_brl=45.0, result_count=800)
    cost = ImportCost(total_cost_brl=42.0)
    return ali, market, cost


def test_viable_product_score():
    ali, market, cost = _viable_inputs()
    result = score_product(ali, market, cost)

    assert result.product_id == "p1"
    assert result.title == "Produto Viável"
    assert result.viavel is True
    assert result.score_total >= 0.60
    assert result.sell_price_suggestion_brl == pytest.approx(40.0 * 2.5)
    assert result.margin_brl == pytest.approx(150.0 - 40.0)


def test_unviable_product_score():
    ali, market, cost = _unviable_inputs()
    result = score_product(ali, market, cost)

    assert result.viavel is False
    assert result.score_total < 0.60


def test_score_bounds():
    for ali, market, cost in [_viable_inputs(), _unviable_inputs()]:
        result = score_product(ali, market, cost)
        assert 0.0 <= result.score_total <= 1.0
        assert 0.0 <= result.score_margem <= 1.0
        assert 0.0 <= result.score_demanda_br <= 1.0
        assert 0.0 <= result.score_oportunidade <= 1.0
        assert 0.0 <= result.score_tendencia <= 1.0
        assert 0.0 <= result.score_logistica <= 1.0


def test_score_dimensions_logistica_tiers():
    # price_usd <= 50 → 1.0
    ali_cheap = AliProduct(product_id="x", title="x", price_usd=50.0)
    market = BRMarket(avg_price_brl=200.0, result_count=50)
    cost = ImportCost(total_cost_brl=30.0)
    r = score_product(ali_cheap, market, cost)
    assert r.score_logistica == pytest.approx(1.0)

    # price_usd = 51 (> 50, <= 100) → 0.6
    ali_mid = AliProduct(product_id="x", title="x", price_usd=51.0)
    r2 = score_product(ali_mid, market, cost)
    assert r2.score_logistica == pytest.approx(0.6)

    # price_usd = 101 (> 100) → 0.3
    ali_heavy = AliProduct(product_id="x", title="x", price_usd=101.0)
    r3 = score_product(ali_heavy, market, cost)
    assert r3.score_logistica == pytest.approx(0.3)


def test_score_tendencia_fixed():
    ali, market, cost = _viable_inputs()
    result = score_product(ali, market, cost)
    assert result.score_tendencia == pytest.approx(0.5)
