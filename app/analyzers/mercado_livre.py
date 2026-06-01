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


def _not_found() -> BRMarket:
    return BRMarket(
        found=False,
        avg_price_brl=None,
        min_price_brl=None,
        max_price_brl=None,
        result_count=0,
        top_listings=[],
    )


async def get_ml_token() -> str:
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
        except Exception:
            pass
    return os.environ.get("ML_USER_ACCESS_TOKEN", "")


async def _fetch_ml_search(
    client: httpx.AsyncClient,
    url: str,
    query: str,
    headers: dict,
) -> dict:
    response = await client.get(
        url,
        params={"q": query, "limit": 10},
        headers=headers,
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


async def search_br_market_via_zoom(query: str) -> BRMarket:
    import json as _json
    import re as _re

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                "https://www.zoom.com.br/search",
                params={"q": query},
                headers=headers,
                timeout=20.0,
            )
            response.raise_for_status()
        html = response.text
    except Exception as exc:
        logger.warning("zoom search failed for %r: %s", query[:60], exc)
        return _not_found()

    m = _re.search(r'"__NEXT_DATA__"[^>]*>(.*?)</script>', html, _re.S)
    if not m:
        return _not_found()

    try:
        data = _json.loads(m.group(1))
        hits = data["props"]["initialReduxState"]["hits"]["hits"]
    except (KeyError, _json.JSONDecodeError):
        return _not_found()

    prices = [h["price"] for h in hits if isinstance(h.get("price"), (int, float)) and h["price"] > 0]
    if not prices:
        return _not_found()

    count_m = _re.search(r"([\d.]+)\s+resultado", html, _re.I)
    count = int(count_m.group(1).replace(".", "")) if count_m else len(hits)
    top = [f"https://www.zoom.com.br{h['url']}" for h in hits[:3] if h.get("url")]

    return BRMarket(
        found=True,
        avg_price_brl=sum(prices) / len(prices),
        min_price_brl=min(prices),
        max_price_brl=max(prices),
        result_count=count,
        top_listings=top,
    )


async def search_br_market(query: str) -> BRMarket:
    token = await get_ml_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    proxy_url = os.environ.get("ML_SEARCH_PROXY_URL", "")

    data: dict | None = None

    async with httpx.AsyncClient() as client:
        if proxy_url:
            try:
                data = await _fetch_ml_search(client, proxy_url, query, headers)
            except Exception as exc:
                logger.warning(
                    "search_br_market proxy failed for %r (%s), falling back to direct",
                    query[:60],
                    exc,
                )

        if data is None:
            try:
                data = await _fetch_ml_search(client, ML_SEARCH_URL, query, headers)
            except Exception as exc:
                logger.warning("search_br_market failed for %r: %s", query[:60], exc)
                return await search_br_market_via_zoom(query)

    results = data.get("results", [])
    count = data.get("paging", {}).get("total", len(results))

    if count == 0:
        return _not_found()

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
