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
            raw = _json.loads(session_cookies)
            for c in raw:
                cookies.append({
                    **c,
                    "domain": c.get("domain", ".aliexpress.com"),
                    "path": c.get("path", "/"),
                })
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


_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.aliexpress.com/",
    "X-Requested-With": "XMLHttpRequest",
}

_FN_PARAMS = {
    "sortType": "total_tranpro_desc",
    "page": "1",
    "origin": "y",
}


def _parse_fn_json(data: dict, category_id: str, max_results: int) -> list[AliProduct]:
    items = (
        _deep_get(data, ["data", "result", "resultList"])
        or _deep_get(data, ["result", "resultList"])
        or _deep_get(data, ["data", "result", "mods", "itemList", "content"])
        or []
    )
    products: list[AliProduct] = []
    for entry in items[:max_results]:
        try:
            item = entry.get("item", entry)
            pid = str(item.get("itemId", item.get("productId", ""))).strip()
            if not pid:
                continue
            title = str(item.get("title", item.get("name", ""))).strip()
            prices = item.get("prices", {})
            sale_price = prices.get("salePrice", prices)
            price_raw = (
                str(sale_price.get("formattedPrice", "0"))
                .replace("US $", "")
                .replace(",", "")
                .strip()
            )
            trade_raw = (
                str(item.get("tradeDesc", item.get("tradeCount", "0")))
                .replace("+", "")
                .replace(",", "")
                .replace("sold", "")
                .strip()
            )
            # "2500 " → 2500, "2500.0" → 2500
            trade_num = trade_raw.split()[0] if trade_raw else "0"
            rating_raw = str(item.get("averageStar", item.get("avgStar", "0"))).strip()
            img = str(item.get("imageUrl", item.get("image", ""))).strip()
            if img.startswith("//"):
                img = "https:" + img
            products.append(
                AliProduct(
                    product_id=pid,
                    title=title,
                    price_usd=float(price_raw) if price_raw else 0.0,
                    sale_count_30d=int(float(trade_num)) if trade_num else 0,
                    rating=float(rating_raw) if rating_raw else 0.0,
                    image_url=img,
                    product_url=f"https://www.aliexpress.com/item/{pid}.html",
                    category_id=category_id,
                )
            )
        except (ValueError, TypeError):
            continue
    return products


def _deep_get(d: dict, keys: list) -> list | None:
    for key in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(key)
        if d is None:
            return None
    return d if isinstance(d, list) else None


def _find_product_list(data, _depth: int = 0) -> list | None:
    """Recursively search for a list of dicts containing 'productId'."""
    if _depth > 10:
        return None
    if isinstance(data, list) and data and isinstance(data[0], dict) and "productId" in data[0]:
        return data
    if isinstance(data, dict):
        for v in data.values():
            result = _find_product_list(v, _depth + 1)
            if result:
                return result
    if isinstance(data, list):
        for item in data:
            result = _find_product_list(item, _depth + 1)
            if result:
                return result
    return None


_SCRAPLING_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.aliexpress.com/",
}


async def _scrape_with_http(
    category_id: str, max_results: int, session_cookies: str = ""
) -> list[AliProduct]:
    import httpx

    cookies: dict[str, str] = {}
    if session_cookies:
        try:
            raw = _json.loads(session_cookies)
            cookies = {c["name"]: c["value"] for c in raw if "name" in c and "value" in c}
        except Exception:
            pass

    params = {**_FN_PARAMS, "categoryId": category_id}

    async def _fetch(url: str) -> list[AliProduct]:
        try:
            async with httpx.AsyncClient(
                timeout=30, follow_redirects=True, cookies=cookies
            ) as client:
                resp = await client.get(url, headers=_HTTP_HEADERS, params=params)
            body = resp.text
            if body.lstrip().startswith("<"):
                logger.warning(
                    "[scraper:http] category=%s returned HTML (IP blocked) from %s",
                    category_id,
                    url,
                )
                return []
            data = _json.loads(body)
            return _parse_fn_json(data, category_id, max_results)
        except Exception as exc:
            logger.warning("[scraper:http] category=%s fetch failed: %s", category_id, exc)
            return []

    products = await _fetch("https://www.aliexpress.com/fn/search-pc/index")
    if products:
        return products
    return await _fetch("https://m.aliexpress.com/fn/search-pc/index")


async def _scrape_with_firecrawl(
    category_id: str, max_results: int, session_cookies: str = "", keyword: str = ""
) -> list[AliProduct]:
    import httpx
    import urllib.parse

    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    firecrawl_url = os.environ.get("FIRECRAWL_URL", "https://api.firecrawl.dev")
    if keyword:
        url_to_scrape = f"https://www.aliexpress.com/wholesale?SearchText={urllib.parse.quote_plus(keyword)}&SortType=total_tranpro_desc"
    else:
        url_to_scrape = f"https://www.aliexpress.com/category/{category_id}/bestselling.html"

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body_headers: dict[str, str] = {}
    if session_cookies:
        try:
            raw_cookies = _json.loads(session_cookies)
            cookie_str = "; ".join(
                f"{c['name']}={c['value']}" for c in raw_cookies if c.get("value")
            )
            if cookie_str:
                body_headers["Cookie"] = cookie_str
        except Exception:
            pass

    try:
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
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 402:
            raise  # dispatcher handles 402 → scrapling fallback
        logger.warning("[scraper:firecrawl] category=%s failed: %r", category_id, exc)
        return []
    except Exception as exc:
        logger.warning("[scraper:firecrawl] category=%s failed: %r", category_id, exc)
        return []

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

    logger.info("[scraper:firecrawl] category=%s extracted=%d", category_id, len(products))
    return products


async def _scrape_with_scrapling(
    category_id: str, max_results: int, keyword: str = ""
) -> list[AliProduct]:
    import re
    import urllib.parse
    import httpx

    if keyword:
        url = f"https://www.aliexpress.com/wholesale?SearchText={urllib.parse.quote_plus(keyword)}&SortType=total_tranpro_desc"
    else:
        url = f"https://www.aliexpress.com/category/{category_id}/bestselling.html"

    try:
        resp = httpx.get(url, headers=_SCRAPLING_HEADERS, follow_redirects=True, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.warning("[scraper:scrapling] category=%s keyword=%r failed: %r", category_id, keyword, exc)
        return []

    _JS_PATTERNS = [
        r"window\._dida_config_\._init_data_\s*=\s*",
        r"window\.runParams\s*=\s*",
        r"window\.__INITIAL_STATE__\s*=\s*",
    ]
    m = None
    for _pat in _JS_PATTERNS:
        m = re.search(_pat, html)
        if m:
            break
    if not m:
        logger.warning("[scraper:scrapling] category=%s keyword=%r no JS data found", category_id, keyword)
        return []

    raw = html[m.end():]
    raw = re.sub(r"\bundefined\b", "null", raw)

    try:
        data, _ = _json.JSONDecoder().raw_decode(raw)
    except Exception as exc:
        logger.warning("[scraper:scrapling] category=%s keyword=%r json parse failed: %r", category_id, keyword, exc)
        return []

    items = _find_product_list(data) or []
    products: list[AliProduct] = []
    for item in items[:max_results]:
        try:
            pid = str(item.get("productId", "")).strip()
            if not pid:
                continue
            title_obj = item.get("title", {})
            title = (
                title_obj.get("displayTitle", "") if isinstance(title_obj, dict) else str(title_obj)
            )
            prices = item.get("prices", {})
            sale_price = prices.get("salePrice", {}) if isinstance(prices, dict) else {}
            price_raw = str(sale_price.get("minPrice", 0) if isinstance(sale_price, dict) else 0)
            rating_raw = str(item.get("star_rating") or item.get("starRating") or "0").strip()
            trade_raw = (
                str(item.get("real_trade_count") or item.get("tradeCount") or "0")
                .replace("+", "")
                .replace(",", "")
                .strip()
            )
            trade_num = trade_raw.split()[0] if trade_raw else "0"
            img_obj = item.get("image", {})
            img = (
                img_obj.get("imgUrl", "") if isinstance(img_obj, dict) else str(img_obj)
            ).strip()
            if img.startswith("//"):
                img = "https:" + img
            products.append(
                AliProduct(
                    product_id=pid,
                    title=str(title).strip(),
                    price_usd=float(price_raw) if price_raw else 0.0,
                    sale_count_30d=int(float(trade_num)) if trade_num else 0,
                    rating=float(rating_raw) if rating_raw else 0.0,
                    image_url=img,
                    product_url=f"https://www.aliexpress.com/item/{pid}.html",
                    category_id=category_id,
                )
            )
        except (ValueError, TypeError):
            continue

    logger.info("[scraper:scrapling] category=%s extracted=%d", category_id, len(products))
    return products


async def get_hot_products(
    category_id: str, min_rating: float = 0.0, max_results: int = 100, keyword: str = ""
) -> list[AliProduct]:
    mode = os.environ.get("SCRAPER_MODE", "firecrawl")
    session_cookies = os.environ.get("ALIEXPRESS_SESSION_COOKIES", "")

    if mode == "mock":
        from app.scrapers.mock import get_mock_products

        return get_mock_products(category_id, min_rating, max_results)

    if mode == "firecrawl":
        try:
            products = await _scrape_with_firecrawl(
                category_id, max_results, session_cookies, keyword=keyword
            )
        except Exception as exc:
            exc_str = str(exc)
            if "402" in exc_str or "Payment" in exc_str:
                logger.warning(
                    "[scraper] Firecrawl sem créditos (402), fallback para scrapling"
                )
                products = await _scrape_with_scrapling(category_id, max_results, keyword=keyword)
            else:
                logger.warning("[scraper:firecrawl] unhandled error: %r", exc)
                products = []
    elif mode == "scrapling":
        products = await _scrape_with_scrapling(category_id, max_results, keyword=keyword)
    elif mode == "crawl4ai":
        products = await _scrape_with_crawl4ai(category_id, max_results, session_cookies)
    else:
        products = await _scrape_with_http(category_id, max_results, session_cookies)
        if not products:
            logger.info(
                "[scraper] http mode returned 0 products for category=%s, falling back to crawl4ai",
                category_id,
            )
            products = await _scrape_with_crawl4ai(category_id, max_results, session_cookies)

    filtered = [p for p in products if p.rating >= min_rating]
    return filtered[:max_results]
