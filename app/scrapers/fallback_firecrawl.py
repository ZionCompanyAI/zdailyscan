import os

import httpx

from app.scrapers.models import AliProduct


async def get_products_via_firecrawl(
    category_id: str, firecrawl_url: str, max_results: int = 100
) -> list[AliProduct]:
    url_to_scrape = f"https://www.aliexpress.us/category/{category_id}/bestselling.html"

    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    _cookie_str = ""
    _cookies_raw = os.environ.get("ALIEXPRESS_SESSION_COOKIES", "")
    if _cookies_raw:
        try:
            import json as _json
            _cookie_list = _json.loads(_cookies_raw)
            _cookie_str = "; ".join(
                f"{c['name']}={c['value']}"
                for c in _cookie_list
                if c.get("value")
            )
        except Exception:
            pass

    # body_headers is forwarded by Firecrawl to AliExpress (not used for auth)
    body_headers = {}
    if _cookie_str:
        body_headers["Cookie"] = _cookie_str

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            firecrawl_url.rstrip("/") + "/v1/scrape",
            headers=headers,
            json={
                "url": url_to_scrape,
                "headers": body_headers,
                "timeout": 150000,
                "formats": ["extract"],
                "extract": {
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "title": {"type": "string"},
                                "price_usd": {"type": "number"},
                                "sale_count_30d": {"type": "integer"},
                                "rating": {"type": "number"},
                                "image_url": {"type": "string"},
                                "product_url": {"type": "string"},
                            },
                        },
                    }
                },
            },
            timeout=180.0,
        )
        resp.raise_for_status()
        data = resp.json()

    # Support both {data: {extract: [...]}} and {data: [...]} response shapes
    payload = data.get("data") or {}
    if isinstance(payload, list):
        raw: list[dict] = payload
    else:
        raw = payload.get("extract") or []

    products: list[AliProduct] = []
    for item in raw[:max_results]:
        try:
            products.append(
                AliProduct(
                    product_id=str(item.get("product_id") or ""),
                    title=str(item.get("title") or ""),
                    price_usd=float(item.get("price_usd") or 0),
                    sale_count_30d=int(item.get("sale_count_30d") or 0),
                    rating=float(item.get("rating") or 0),
                    image_url=str(item.get("image_url") or ""),
                    product_url=str(item.get("product_url") or ""),
                    category_id=category_id,
                )
            )
        except (ValueError, TypeError):
            continue

    return products
