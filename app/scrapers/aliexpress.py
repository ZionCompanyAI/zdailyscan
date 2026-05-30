import json
import os

from app.scrapers.models import AliProduct

__all__ = ["AliProduct", "get_hot_products"]


async def _scrape_with_crawl4ai(category_id: str, max_results: int) -> list[AliProduct]:
    # Lazy import — crawl4ai only loaded when not in mock/test mode
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

    schema = {
        "name": "AliExpress Products",
        "baseSelector": ".list--gallery--C2f2tvm .list--item--G8aNaOa",
        "fields": [
            {
                "name": "product_id",
                "selector": "a",
                "type": "attribute",
                "attribute": "href",
            },
            {"name": "title", "selector": ".multi--titleText--nXeOvyr", "type": "text"},
            {"name": "price", "selector": ".multi--price-sale--U-S0jtj", "type": "text"},
            {"name": "sold", "selector": ".multi--trade--Ktbl2jB", "type": "text"},
            {"name": "rating", "selector": ".multi--evaluation--3d0e-Ey span", "type": "text"},
            {
                "name": "image_url",
                "selector": "img",
                "type": "attribute",
                "attribute": "src",
            },
        ],
    }

    url = f"https://www.aliexpress.com/category/{category_id}/bestselling.html"
    browser_config = BrowserConfig(headless=True)
    strategy = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

    raw_content = result.extracted_content or "[]"
    raw: list[dict] = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
    products: list[AliProduct] = []
    for item in raw[:max_results]:
        try:
            href = str(item.get("product_id", ""))
            pid = href.split("/item/")[-1].split(".")[0] if "/item/" in href else href

            price_raw = str(item.get("price", "0")).replace("US$", "").replace(",", "").strip()
            sold_raw = (
                str(item.get("sold", "0"))
                .replace("+", "")
                .replace(",", "")
                .replace("sold", "")
                .strip()
            )
            rating_raw = str(item.get("rating", "0")).strip()

            products.append(
                AliProduct(
                    product_id=pid,
                    title=str(item.get("title", "")).strip(),
                    price_usd=float(price_raw) if price_raw else 0.0,
                    sale_count_30d=int(float(sold_raw)) if sold_raw else 0,
                    rating=float(rating_raw) if rating_raw else 0.0,
                    image_url=str(item.get("image_url", "")),
                    product_url=f"https://www.aliexpress.com/item/{pid}.html",
                    category_id=category_id,
                )
            )
        except (ValueError, TypeError):
            continue

    return products


async def get_hot_products(
    category_id: str, min_rating: float = 4.9, max_results: int = 100
) -> list[AliProduct]:
    mode = os.environ.get("SCRAPER_MODE", "crawl4ai")

    if mode == "mock":
        from app.scrapers.mock import get_mock_products

        return get_mock_products(category_id, min_rating, max_results)

    firecrawl_url = os.environ.get("FIRECRAWL_URL", "")

    try:
        products = await _scrape_with_crawl4ai(category_id, max_results)
    except Exception:
        if firecrawl_url:
            from app.scrapers.fallback_firecrawl import get_products_via_firecrawl

            products = await get_products_via_firecrawl(category_id, firecrawl_url, max_results)
        else:
            raise

    filtered = [p for p in products if p.rating >= min_rating]
    return filtered[:max_results]
