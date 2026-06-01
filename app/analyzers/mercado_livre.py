import logging
import os

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ML_SEARCH_URL = "https://api.mercadolibre.com/sites/MLB/search"


class BRMarket(BaseModel):
    found: bool
    avg_price_brl: float | None
    min_price_brl: float | None
    max_price_brl: float | None
    result_count: int
    top_listings: list[str]


async def get_ml_token() -> str:
    """Return a fresh ML token from auth-bus, or fall back to the static env var."""
    bus_url = os.environ.get("AUTH_BUS_URL", "")
    bus_key = os.environ.get("AUTH_BUS_API_KEY", "")
    if bus_url and bus_key:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{bus_url}/tokens/mercadolibre",
                    headers={"x-api-key": bus_key, "User-Agent": "zdailyscan/1.0"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("access_token", "")
        except Exception as exc:
            logger.warning("auth-bus token fetch failed, using fallback: %s", exc)
    return os.environ.get("ML_USER_ACCESS_TOKEN", "")


async def search_br_market(query: str, ml_token: str = "") -> BRMarket:
    headers = {}
    if ml_token:
        headers["Authorization"] = f"Bearer {ml_token}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ML_SEARCH_URL,
                params={"q": query, "limit": 10},
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.warning("search_br_market failed for %r: %s", query[:60], exc)
        return BRMarket(
            found=False,
            avg_price_brl=None,
            min_price_brl=None,
            max_price_brl=None,
            result_count=0,
            top_listings=[],
        )

    results = data.get("results", [])
    count = data.get("paging", {}).get("total", len(results))

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
