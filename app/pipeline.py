import asyncio
import logging
import os
import re
import uuid
from datetime import date

from pydantic import BaseModel

from app.scrapers import get_hot_products
from app.analyzers.import_calculator import calculate_import_cost
from app.analyzers.mercado_livre import BRMarket, search_br_market
from app.analyzers.trend_analyzer import compute_trend_score
from app.scoring.scorer import AliProduct, ProductScore, score_product
from app.reporters.telegram_reporter import send_daily_report
from app.reporters.file_reporter import save_daily_report

logger = logging.getLogger(__name__)

TECH_KEYWORDS: list[str] = [
    "usb", "hdmi", "hub", "adapter", "charger", "cable", "bluetooth",
    "wifi", "laptop", "phone", "iphone", "android", "thunderbolt",
    "display", "port", "wireless", "earphone", "headphone", "speaker",
    "power bank", "screen", "monitor", "keyboard", "mouse", "ssd",
    "memory", "ram", "type-c", "type c", "lightning", "ethernet",
    "converter", "splitter", "docking", "stand", "mount",
]


_TECH_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in TECH_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def is_tech_product(title: str) -> bool:
    return bool(_TECH_PATTERN.search(title))


CATEGORIES: list[str] = [
    "200003655",  # Consumer Electronics
    "100003070",  # Phones & Telecommunications
    "200000783",  # Computer & Office
]

DEFAULT_KEYWORDS = "USB-C adapter,USB hub multiport,HDMI adapter,wireless charger,phone stand,laptop stand,bluetooth earphones,Thunderbolt hub,screen protector,power bank"


def get_active_keywords() -> list[str]:
    raw = os.getenv("SCAN_KEYWORDS", DEFAULT_KEYWORDS)
    return [k.strip() for k in raw.split(",") if k.strip()]


def get_active_categories() -> list[str]:
    """Return active category IDs from SCAN_CATEGORIES env var, or all defaults."""
    raw = os.environ.get("SCAN_CATEGORIES", "")
    if not raw.strip():
        return CATEGORIES
    valid = set(CATEGORIES)
    filtered = [c.strip() for c in raw.split(",") if c.strip() in valid]
    return filtered if filtered else CATEGORIES


class ScanResult(BaseModel):
    scan_id: str
    date: str
    products: list[ProductScore]
    total_scanned: int
    total_viable: int


async def run_daily_scan(
    scan_id: str | None = None,
    categories: list[str] | None = None,
) -> ScanResult:
    if scan_id is None:
        scan_id = str(uuid.uuid4())
    today = date.today().isoformat()
    all_scores: list[ProductScore] = []

    scan_targets: list[tuple[str, str]] = [
        (cat_id, "") for cat_id in (categories or get_active_categories())
    ] + [("", kw) for kw in get_active_keywords()]

    for category_id, keyword in scan_targets:
        try:
            products = await get_hot_products(category_id, keyword=keyword, max_results=10 if keyword else 100)
        except Exception as exc:
            logger.warning("scraper failed for category %s: %r", category_id, exc)
            continue
        await asyncio.sleep(2)  # rate limiting delay between AliExpress targets
        for product in products:
            if not keyword and not is_tech_product(product.title):
                all_scores.append(ProductScore(
                    product_id=product.product_id,
                    title=product.title,
                    score_total=0.0,
                    score_margem=0.0,
                    score_demanda_br=0.0,
                    score_oportunidade=0.0,
                    score_tendencia=0.0,
                    score_logistica=0.0,
                    margin_brl=0.0,
                    sell_price_suggestion_brl=0.0,
                    viavel=False,
                ))
                continue
            try:
                market = await search_br_market(product.title)
            except Exception as exc:
                logger.warning("market search failed: %s", exc)
                market = BRMarket(
                    found=False,
                    avg_price_brl=None,
                    min_price_brl=None,
                    max_price_brl=None,
                    result_count=0,
                    top_listings=[],
                )
            cost = calculate_import_cost(product.price_usd, product.freight_usd)
            ali = AliProduct(product_id=product.product_id, title=product.title)
            trend_score = compute_trend_score(product.title)
            score = score_product(ali, market, cost, trend_score=trend_score)
            all_scores.append(score)

    viable = [s for s in all_scores if s.viavel]
    top20 = sorted(viable, key=lambda s: s.score_total, reverse=True)[:20]

    result = ScanResult(
        scan_id=scan_id,
        date=today,
        products=top20,
        total_scanned=len(all_scores),
        total_viable=len(viable),
    )

    try:
        await send_daily_report(top20)
    except Exception as e:
        logger.error("telegram reporter failed: %s", e)

    try:
        save_daily_report(top20)
    except Exception as e:
        logger.error("file reporter failed: %s", e)

    return result
