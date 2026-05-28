import json
import re
from typing import Any

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
except ImportError:
    AsyncWebCrawler = None
    BrowserConfig = None
    CrawlerRunConfig = None
    JsonCssExtractionStrategy = None

from app.scrapers import AliProduct

BESTSELLER_URL = "https://www.aliexpress.com/category/{category_id}/bestselling.html"
WHOLESALE_URL = (
    "https://www.aliexpress.com/wholesale"
    "?SearchText=&SortType=total_tranpro_desc&catId={category_id}"
)

_SCHEMA = {
    "name": "AliExpress Products",
    "baseSelector": (
        "div[class*='product-item'], "
        "div[class*='list--gallery'], "
        "div[class*='search-card-item']"
    ),
    "fields": [
        {"name": "product_id", "selector": "a", "type": "attribute", "attribute": "data-product-id"},
        {"name": "title", "selector": "[class*='title']", "type": "text"},
        {"name": "price_raw", "selector": "[class*='price']", "type": "text"},
        {"name": "rating_raw", "selector": "[class*='rating']", "type": "text"},
        {"name": "sold_raw", "selector": "[class*='sold'], [class*='orders']", "type": "text"},
        {"name": "image_url", "selector": "img[src]", "type": "attribute", "attribute": "src"},
        {"name": "product_url", "selector": "a[href*='aliexpress.com/item']", "type": "attribute", "attribute": "href"},
    ],
}


def _parse_float(text: str | None) -> float:
    if not text:
        return 0.0
    numbers = re.findall(r"[\d.]+", text.replace(",", ""))
    return float(numbers[0]) if numbers else 0.0


def _parse_int(text: str | None) -> int:
    if not text:
        return 0
    numbers = re.findall(r"[\d]+", text.replace(",", ""))
    return int(numbers[0]) if numbers else 0


def _normalize_url(url: str, product_id: str) -> str:
    if url.startswith("http"):
        return url
    if url.startswith("//"):
        return f"https:{url}"
    return f"https://www.aliexpress.com/item/{product_id}.html"


def _parse_items(raw: list[dict[str, Any]], category_id: str) -> list[AliProduct]:
    products = []
    for item in raw:
        product_id = item.get("product_id") or ""
        title = (item.get("title") or "").strip()
        price_usd = _parse_float(item.get("price_raw"))
        rating = _parse_float(item.get("rating_raw"))
        sale_count_30d = _parse_int(item.get("sold_raw"))
        image_url = item.get("image_url") or ""
        product_url = _normalize_url(item.get("product_url") or "", product_id)

        if not product_id or not title or price_usd <= 0:
            continue

        products.append(
            AliProduct(
                product_id=product_id,
                title=title,
                price_usd=price_usd,
                sale_count_30d=sale_count_30d,
                rating=rating,
                image_url=image_url,
                product_url=product_url,
                category_id=category_id,
            )
        )
    return products


async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
) -> list[AliProduct]:
    if AsyncWebCrawler is None:
        raise RuntimeError("crawl4ai is not installed. Run: pip install crawl4ai && crawl4ai-setup")

    url = BESTSELLER_URL.format(category_id=category_id)
    strategy = JsonCssExtractionStrategy(_SCHEMA, verbose=False)
    run_config = CrawlerRunConfig(extraction_strategy=strategy)
    browser_config = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

    raw = json.loads(result.extracted_content or "[]")
    return _parse_items(raw, category_id)
