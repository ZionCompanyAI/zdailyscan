from pydantic import BaseModel

from app.analyzers.mercado_livre import BRMarket
from app.analyzers.import_calculator import ImportCost


class AliProduct(BaseModel):
    product_id: str
    title: str


class ProductScore(BaseModel):
    product_id: str
    title: str
    score_total: float
    score_margem: float
    score_demanda_br: float
    score_oportunidade: float
    score_tendencia: float
    score_logistica: float
    margin_brl: float
    sell_price_suggestion_brl: float
    viavel: bool


def score_product(ali: AliProduct, market: BRMarket, cost: ImportCost) -> ProductScore:
    avg_price = market.avg_price_brl or 0.0

    if avg_price > 0:
        score_margem = max(0.0, min(1.0, (avg_price - cost.total_cost_brl) / avg_price))
    else:
        score_margem = 0.0

    score_demanda_br = min(market.result_count / 100, 1.0)
    score_oportunidade = 1.0 - min(market.result_count / 500, 1.0)
    score_tendencia = 0.5

    if cost.price_usd <= 50:
        score_logistica = 1.0
    elif cost.price_usd <= 100:
        score_logistica = 0.6
    else:
        score_logistica = 0.3

    score_total = (
        0.30 * score_margem
        + 0.25 * score_demanda_br
        + 0.20 * score_oportunidade
        + 0.15 * score_tendencia
        + 0.10 * score_logistica
    )

    margin_brl = avg_price - cost.total_cost_brl
    sell_price_suggestion_brl = cost.total_cost_brl * 2.5

    return ProductScore(
        product_id=ali.product_id,
        title=ali.title,
        score_total=round(score_total, 6),
        score_margem=round(score_margem, 6),
        score_demanda_br=round(score_demanda_br, 6),
        score_oportunidade=round(score_oportunidade, 6),
        score_tendencia=score_tendencia,
        score_logistica=score_logistica,
        margin_brl=round(margin_brl, 2),
        sell_price_suggestion_brl=round(sell_price_suggestion_brl, 2),
        viavel=score_total >= 0.60,
    )
