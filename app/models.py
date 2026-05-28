from pydantic import BaseModel


class AliProduct(BaseModel):
    product_id: str
    title: str
    price_usd: float


class BRMarket(BaseModel):
    avg_price_brl: float
    result_count: int


class ImportCost(BaseModel):
    total_cost_brl: float


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
