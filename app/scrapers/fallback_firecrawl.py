import httpx

from app.scrapers import AliProduct

BESTSELLER_URL = "https://www.aliexpress.com/category/{category_id}/bestselling.html"


async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
    firecrawl_url: str = "",
) -> list[AliProduct]:
    target_url = BESTSELLER_URL.format(category_id=category_id)
    payload = {
        "url": target_url,
        "formats": ["json"],
        "jsonOptions": {
            "schema": {
                "type": "object",
                "properties": {
                    "products": {
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
            }
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{firecrawl_url}/v1/scrape", json=payload)
        response.raise_for_status()
        data = response.json()

    raw_products = data.get("data", {}).get("json", {}).get("products", [])
    products = []
    for item in raw_products:
        product_id = str(item.get("product_id") or "")
        title = str(item.get("title") or "").strip()
        price_usd = float(item.get("price_usd") or 0)
        if not product_id or not title or price_usd <= 0:
            continue
        products.append(
            AliProduct(
                product_id=product_id,
                title=title,
                price_usd=price_usd,
                sale_count_30d=int(item.get("sale_count_30d") or 0),
                rating=float(item.get("rating") or 0),
                image_url=str(item.get("image_url") or ""),
                product_url=str(item.get("product_url") or ""),
                category_id=category_id,
            )
        )
    return products
