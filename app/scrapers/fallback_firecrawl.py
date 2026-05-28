import os

import httpx

from app.scrapers.aliexpress import AliProduct, _parse_price, _parse_rating, _parse_sales


async def scrape_with_firecrawl(category_id: str, max_results: int) -> list[AliProduct]:
    firecrawl_url = os.environ.get("FIRECRAWL_URL", "").rstrip("/")
    url = (
        f"https://www.aliexpress.com/wholesale"
        f"?SearchText=&SortType=total_tranpro_desc&catId={category_id}"
    )

    payload = {
        "url": url,
        "formats": ["extract"],
        "extract": {
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
                                "price": {"type": "string"},
                                "rating": {"type": "string"},
                                "sales": {"type": "string"},
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
    raw_products = data.get("data", {}).get("extract", {}).get("products", [])

    products: list[AliProduct] = []
    for item in raw_products[:max_results]:
        try:
            link = item.get("product_url", "")
            if link and not link.startswith("http"):
                link = "https:" + link
            products.append(
                AliProduct(
                    product_id=item.get("product_id", ""),
                    title=item.get("title", "").strip(),
                    price_usd=_parse_price(item.get("price", "0")),
                    sale_count_30d=_parse_sales(item.get("sales", "0")),
                    rating=_parse_rating(item.get("rating", "0")),
                    image_url=item.get("image_url", ""),
                    product_url=link,
                    category_id=category_id,
                )
            )
        except Exception:
            continue

    return products
