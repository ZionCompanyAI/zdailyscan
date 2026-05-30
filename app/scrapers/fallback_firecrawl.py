import httpx

from app.scrapers.models import AliProduct


async def get_products_via_firecrawl(
    category_id: str, firecrawl_url: str, max_results: int = 100
) -> list[AliProduct]:
    url_to_scrape = f"https://www.aliexpress.com/category/{category_id}/bestselling.html"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{firecrawl_url.rstrip('/')}/v1/scrape",
            json={
                "url": url_to_scrape,
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
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()

    raw: list[dict] = data.get("data", {}).get("extract", []) or []
    products: list[AliProduct] = []
    for item in raw[:max_results]:
        try:
            products.append(
                AliProduct(
                    product_id=str(item.get("product_id", "")),
                    title=str(item.get("title", "")),
                    price_usd=float(item.get("price_usd", 0)),
                    sale_count_30d=int(item.get("sale_count_30d", 0)),
                    rating=float(item.get("rating", 0)),
                    image_url=str(item.get("image_url", "")),
                    product_url=str(item.get("product_url", "")),
                    category_id=category_id,
                )
            )
        except (ValueError, TypeError):
            continue

    return products
