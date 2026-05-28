from app.models import AliProduct, BRMarket, ImportCost, ProductScore

_WEIGHTS = {
    "margem": 0.30,
    "demanda_br": 0.25,
    "oportunidade": 0.20,
    "tendencia": 0.15,
    "logistica": 0.10,
}


def _dim_margem(avg_price_brl: float, total_cost_brl: float) -> float:
    if avg_price_brl <= 0:
        return 0.0
    return max(0.0, min(1.0, (avg_price_brl - total_cost_brl) / avg_price_brl))


def _dim_demanda(result_count: int) -> float:
    return min(result_count / 100.0, 1.0)


def _dim_oportunidade(result_count: int) -> float:
    return 1.0 - min(result_count / 500.0, 1.0)


def _dim_logistica(price_usd: float) -> float:
    if price_usd <= 50:
        return 1.0
    if price_usd <= 100:
        return 0.6
    return 0.3


def score_product(ali: AliProduct, market: BRMarket, cost: ImportCost) -> ProductScore:
    s_margem = _dim_margem(market.avg_price_brl, cost.total_cost_brl)
    s_demanda = _dim_demanda(market.result_count)
    s_oportunidade = _dim_oportunidade(market.result_count)
    s_tendencia = 0.5
    s_logistica = _dim_logistica(ali.price_usd)

    score_total = (
        _WEIGHTS["margem"] * s_margem
        + _WEIGHTS["demanda_br"] * s_demanda
        + _WEIGHTS["oportunidade"] * s_oportunidade
        + _WEIGHTS["tendencia"] * s_tendencia
        + _WEIGHTS["logistica"] * s_logistica
    )

    return ProductScore(
        product_id=ali.product_id,
        title=ali.title,
        score_total=round(score_total, 6),
        score_margem=round(s_margem, 6),
        score_demanda_br=round(s_demanda, 6),
        score_oportunidade=round(s_oportunidade, 6),
        score_tendencia=round(s_tendencia, 6),
        score_logistica=round(s_logistica, 6),
        margin_brl=market.avg_price_brl - cost.total_cost_brl,
        sell_price_suggestion_brl=cost.total_cost_brl * 2.5,
        viavel=score_total >= 0.60,
    )
