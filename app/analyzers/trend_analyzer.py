import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

_FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
_1688_SEARCH_URL = "https://www.1688.com/page/search_product.html"

_trend_cache: dict[str, tuple[float, datetime]] = {}


def _cache_ttl_hours() -> int:
    try:
        return int(os.environ.get("TREND_CACHE_TTL_HOURS", "24"))
    except ValueError:
        return 24


@dataclass
class TrendSignal:
    title: str
    sales_volume: str


def _extract_keyword(product_title: str) -> str:
    return " ".join(product_title.split()[:3])


def fetch_google_trends_br(keywords: list[str]) -> dict[str, float]:
    """Return normalized 0-1 average interest for last 90 days, geo=BR.

    Retries 3 times with exponential backoff on failure.
    Returns {} on persistent failure.
    """
    if not keywords:
        return {}

    for attempt in range(3):
        try:
            tr = TrendReq(hl="pt-BR", geo="BR")
            tr.build_payload(keywords, timeframe="today 3-m")
            df = tr.interest_over_time()
            if df.empty:
                return {}
            result: dict[str, float] = {}
            for kw in keywords:
                try:
                    mean_val = df[kw].mean()
                    result[kw] = max(0.0, min(1.0, mean_val / 100.0))
                except KeyError:
                    pass
            return result
        except Exception as exc:
            if attempt < 2:
                wait = 2 ** attempt
                logger.warning("pytrends attempt %d failed: %r — retrying in %ds", attempt + 1, exc, wait)
                time.sleep(wait)
            else:
                logger.warning("pytrends all attempts failed: %r", exc)
    return {}


async def fetch_1688_trending(category_keyword: str) -> list[TrendSignal]:
    """Scrape 1688.com bestsellers via Firecrawl /v1/scrape.

    Returns [] on any failure.
    """
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        logger.warning("FIRECRAWL_API_KEY not set — skipping 1688 scrape")
        return []

    url = f"{_1688_SEARCH_URL}?keywords={category_keyword}"
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
                                "title": {"type": "string"},
                                "sales": {"type": "string"},
                            },
                        },
                    }
                },
            }
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _FIRECRAWL_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if resp.status_code != 200:
            logger.warning("1688 Firecrawl returned HTTP %d", resp.status_code)
            return []

        data = resp.json()
        items = data.get("data", {}).get("extract", [])
        if not isinstance(items, list):
            return []
        return [
            TrendSignal(title=item.get("title", ""), sales_volume=item.get("sales", ""))
            for item in items
            if item.get("title")
        ]
    except Exception as exc:
        logger.warning("fetch_1688_trending failed: %r", exc)
        return []


def compute_trend_score(product_title: str) -> float:
    """Return 0.0-1.0 trend score for a product title.

    Uses 24h in-memory cache per keyword. Falls back to 0.5 if all sources fail.
    """
    keyword = _extract_keyword(product_title)
    ttl = timedelta(hours=_cache_ttl_hours())

    cached = _trend_cache.get(keyword)
    if cached is not None:
        score, ts = cached
        if datetime.now(timezone.utc).replace(tzinfo=None) - ts < ttl:
            return score

    trends = fetch_google_trends_br([keyword])
    if keyword in trends:
        score = trends[keyword]
    else:
        score = 0.5

    _trend_cache[keyword] = (score, datetime.now(timezone.utc).replace(tzinfo=None))
    return score
