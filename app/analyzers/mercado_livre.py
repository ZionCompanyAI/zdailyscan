import httpx
from pydantic import BaseModel


ML_SEARCH_URL = "https://api.mercadolibre.com/sites/MLB/search"


class BRMarket(BaseModel):
    found: bool
    avg_price_brl: float | None
    min_price_brl: float | None
    max_price_brl: float | None
    result_count: int
    top_listings: list[str]


async def search_br_market(query: str) -> BRMarket:
    async with httpx.AsyncClient() as client:
        response = await client.get(ML_SEARCH_URL, params={"q": query, "limit": 10})
        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])
    count = len(results)

    if count == 0:
        return BRMarket(
            found=False,
            avg_price_brl=None,
            min_price_brl=None,
            max_price_brl=None,
            result_count=0,
            top_listings=[],
        )

    prices = [r["price"] for r in results if "price" in r]
    top_listings = [r["permalink"] for r in results[:3] if "permalink" in r]

    return BRMarket(
        found=True,
        avg_price_brl=sum(prices) / len(prices) if prices else None,
        min_price_brl=min(prices) if prices else None,
        max_price_brl=max(prices) if prices else None,
        result_count=count,
        top_listings=top_listings,
    )
