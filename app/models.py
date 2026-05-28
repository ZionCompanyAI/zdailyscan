from pydantic import BaseModel


class ProductScore(BaseModel):
    name: str
    score: float
    import_cost_brl: float
    suggested_price_brl: float
    ml_listing_count: int
    aliexpress_url: str
