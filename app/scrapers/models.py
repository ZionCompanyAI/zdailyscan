from pydantic import BaseModel


class AliProduct(BaseModel):
    product_id: str
    title: str
    price_usd: float
    sale_count_30d: int
    rating: float
    freight_usd: float = 0.0
    image_url: str
    product_url: str
    category_id: str
