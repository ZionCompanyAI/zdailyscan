import os
from pydantic import BaseModel


class AliProduct(BaseModel):
    product_id: str
    title: str
    price_usd: float
    sale_count_30d: int
    rating: float
    image_url: str
    product_url: str
    category_id: str


async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
) -> list[AliProduct]:
    mode = os.getenv("SCRAPER_MODE", "crawl4ai")
    firecrawl_url = os.getenv("FIRECRAWL_URL", "")

    if mode == "mock":
        from app.scrapers.mock import get_hot_products as _scrape
        products = await _scrape(category_id, min_rating, max_results)
    elif firecrawl_url:
        from app.scrapers.fallback_firecrawl import get_hot_products as _scrape
        products = await _scrape(category_id, min_rating, max_results, firecrawl_url)
    else:
        from app.scrapers.aliexpress import get_hot_products as _scrape
        products = await _scrape(category_id, min_rating, max_results)

    return [p for p in products if p.rating >= min_rating][:max_results]
