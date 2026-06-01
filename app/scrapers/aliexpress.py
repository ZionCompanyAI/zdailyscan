import json as _json
import logging
import os

from app.scrapers.models import AliProduct

logger = logging.getLogger(__name__)

__all__ = ["AliProduct", "get_hot_products"]

# Selectors use data-* and itemprop attributes — stable across AliExpress bundler deploys.
# Replaced hash-suffixed class names (e.g. .multi--titleText--nXeOvyr) that change on every
# webpack release. Firecrawl fallback is triggered when this schema returns 0 products.
_PRODUCT_SCHEMA = {
    "name": "AliExpress Products",
    "baseSelector": "[data-item-id]",
    "fields": [
        {
            "name": "product_id",
            "selector": "a[href*='/item/']",
            "type": "attribute",
            "attribute": "href",
        },
        {"name": "title", "selector": "[itemprop='name'], h3", "type": "text"},
        {"name": "price", "selector": "[itemprop='price'], [data-price]", "type": "text"},
        {"name": "sold", "selector": "[data-sold], [data-trade]", "type": "text"},
        {
            "name": "rating",
            "selector": "[itemprop='ratingValue'], [data-rating]",
            "type": "text",
        },
        {
            "name": "image_url",
            "selector": "img",
            "type": "attribute",
            "attribute": "src",
        },
    ],
}


async def _scrape_with_crawl4ai(
    category_id: str, max_results: int, session_cookies: str = ""
) -> list[AliProduct]:
    # Lazy import — crawl4ai only loaded when not in mock/test mode
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

    url = f"https://www.aliexpress.com/category/{category_id}/bestselling.html"

    cookies: list[dict] = []
    if session_cookies:
        try:
            cookies = _json.loads(session_cookies)
        except Exception:
            pass

    browser_config = BrowserConfig(
        headless=True,
        user_agent_mode="random",
        cookies=cookies,
    )
    strategy = JsonCssExtractionStrategy(_PRODUCT_SCHEMA)

    run_config = CrawlerRunConfig(
        extraction_strategy=strategy,
        magic=True,
        page_timeout=45000,
        js_code="window.scrollTo(0, document.body.scrollHeight);",
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
    except Exception as exc:
        logger.warning("[scraper] category=%s crawl failed: %s", category_id, exc)
        return []

    if hasattr(result, "html") and isinstance(result.html, str) and result.html:
        import re as _re
        title_m = _re.search(r"<title[^>]*>(.*?)</title>", result.html[:2000], _re.I | _re.S)
        page_title = title_m.group(1).strip() if title_m else "(sem título)"
        logger.info(
            "[scraper] category=%s page_title=%r extracted=%s",
            category_id,
            page_title[:80],
            len(_json.loads(result.extracted_content or "[]")),
        )

    raw_content = result.extracted_content or "[]"
    if isinstance(raw_content, str):
        raw: list[dict] = _json.loads(raw_content)
    else:
        raw = raw_content
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
    category_id: str, min_rating: float = 0.0, max_results: int = 100
) -> list[AliProduct]:
    mode = os.environ.get("SCRAPER_MODE", "crawl4ai")
    session_cookies = os.environ.get("ALIEXPRESS_SESSION_COOKIES", "")

    if mode == "mock":
        from app.scrapers.mock import get_mock_products

        return get_mock_products(category_id, min_rating, max_results)

    products = await _scrape_with_crawl4ai(category_id, max_results, session_cookies)
    filtered = [p for p in products if p.rating >= min_rating]
    return filtered[:max_results]
