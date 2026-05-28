import logging
import uuid
from datetime import date

from pydantic import BaseModel

from app.scrapers import get_hot_products
from app.analyzers.import_calculator import calculate_import_cost
from app.analyzers.mercado_livre import search_br_market
from app.scoring.scorer import AliProduct, ProductScore, score_product
from app.reporters.telegram_reporter import send_daily_report
from app.reporters.file_reporter import save_daily_report

logger = logging.getLogger(__name__)

CATEGORIES: list[str] = [
    "200003655",  # Consumer Electronics
    "100003070",  # Phones & Telecommunications
    "200000783",  # Computer & Office
    "200000828",  # Home & Garden
    "200000834",  # Sports & Entertainment
]


class ScanResult(BaseModel):
    scan_id: str
    date: str
    products: list[ProductScore]
    total_scanned: int
    total_viable: int


async def run_daily_scan(scan_id: str | None = None) -> ScanResult:
    if scan_id is None:
        scan_id = str(uuid.uuid4())
    today = date.today().isoformat()
    all_scores: list[ProductScore] = []

    for category_id in CATEGORIES:
        products = await get_hot_products(category_id)
        for product in products:
            market = await search_br_market(product.title)
            cost = calculate_import_cost(product.price_usd, product.freight_usd)
            ali = AliProduct(product_id=product.product_id, title=product.title)
            score = score_product(ali, market, cost)
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
