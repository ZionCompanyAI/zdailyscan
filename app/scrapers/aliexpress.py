import json
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
    mode = os.environ.get("SCRAPER_MODE", "crawl4ai")

    if mode == "mock":
        from app.scrapers.mock import get_mock_products
        products = get_mock_products(category_id)
    else:
        try:
            products = await _scrape_crawl4ai(category_id, max_results)
        except Exception:
            firecrawl_url = os.environ.get("FIRECRAWL_URL", "")
            if firecrawl_url:
                from app.scrapers.fallback_firecrawl import scrape_with_firecrawl
                products = await scrape_with_firecrawl(category_id, max_results)
            else:
                products = []

    return [p for p in products if p.rating >= min_rating]


async def _scrape_crawl4ai(category_id: str, max_results: int) -> list[AliProduct]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

    schema = {
        "name": "AliExpress Products",
        "baseSelector": ".list-item, [class*='product-item'], [class*='manhattan--container']",
        "fields": [
            {
                "name": "title",
                "selector": "[class*='title'], h3",
                "type": "text",
            },
            {
                "name": "price",
                "selector": "[class*='price'], [class*='sale-price']",
                "type": "text",
            },
            {
                "name": "rating",
                "selector": "[class*='eval'], [class*='rating'], [class*='star']",
                "type": "text",
            },
            {
                "name": "sales",
                "selector": "[class*='sold'], [class*='trade']",
                "type": "text",
            },
            {
                "name": "image",
                "selector": "img[src]",
                "type": "attribute",
                "attribute": "src",
            },
            {
                "name": "link",
                "selector": "a[href]",
                "type": "attribute",
                "attribute": "href",
            },
        ],
    }

    url = (
        f"https://www.aliexpress.com/wholesale"
        f"?SearchText=&SortType=total_tranpro_desc&catId={category_id}"
    )

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)
    extraction_strategy = JsonCssExtractionStrategy(schema=schema, verbose=False)
    run_config = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

    if not result.success or not result.extracted_content:
        return []

    raw = json.loads(result.extracted_content)
    products: list[AliProduct] = []

    for i, item in enumerate(raw[:max_results]):
        try:
            price_usd = _parse_price(item.get("price", "0"))
            rating = _parse_rating(item.get("rating", "0"))
            sales = _parse_sales(item.get("sales", "0"))
            link = item.get("link", "")
            if link and not link.startswith("http"):
                link = "https:" + link
            product_id = _extract_product_id(link) or str(i)

            products.append(
                AliProduct(
                    product_id=product_id,
                    title=item.get("title", "").strip(),
                    price_usd=price_usd,
                    sale_count_30d=sales,
                    rating=rating,
                    image_url=item.get("image", ""),
                    product_url=link,
                    category_id=category_id,
                )
            )
        except Exception:
            continue

    return products


def _parse_price(raw: str) -> float:
    cleaned = raw.replace("$", "").replace(",", "").replace("US", "").strip()
    try:
        return float(cleaned.split()[0])
    except (ValueError, IndexError):
        return 0.0


def _parse_rating(raw: str) -> float:
    try:
        return float(raw.strip().split()[0])
    except (ValueError, IndexError):
        return 0.0


def _parse_sales(raw: str) -> int:
    cleaned = raw.lower().replace(",", "").replace("+", "").strip()
    # "1000 sold" → 1000
    parts = cleaned.split()
    for part in parts:
        try:
            return int(float(part))
        except ValueError:
            continue
    return 0


def _extract_product_id(url: str) -> str:
    # https://www.aliexpress.com/item/1234567890.html
    if "/item/" in url:
        segment = url.split("/item/")[-1]
        return segment.split(".")[0].split("?")[0]
    return ""
