import logging
from datetime import date

import httpx

from app.config import Settings
from app.scoring.scorer import ProductScore

logger = logging.getLogger(__name__)


def _format_message(results: list[ProductScore]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    top10 = results[:10]
    lines = [
        f"🛒 ZDailyScan — {today}",
        "Top 10 oportunidades AliExpress → LojaHi Select",
        "",
    ]
    for i, p in enumerate(top10, 1):
        product_url = f"https://www.aliexpress.com/item/{p.product_id}.html"
        lines += [
            f"{i}. {p.title} ⭐ score: {p.score_total:.2f}",
            f"   💰 Custo importação: R$ {p.import_cost_brl:.2f}",
            f"   🏷️ Sugestão de venda: R$ {p.sell_price_suggestion_brl:.2f}",
            f"   📦 Demanda ML: {p.demand_count} anúncios",
            f"   🔗 {product_url}",
            "",
        ]
    return "\n".join(lines).strip()


async def send_daily_report(results: list[ProductScore]) -> bool:
    settings = Settings()
    message = _format_message(results)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.mc_url}/telegram/reply",
                headers={"x-api-key": settings.mc_api_key},
                json={"chat_id": settings.telegram_chat_id, "text": message, "parse_mode": "Markdown"},
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("telegram reporter failed: %s", e)
        return False
