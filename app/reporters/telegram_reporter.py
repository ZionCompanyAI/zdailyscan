import logging
from datetime import date

import httpx

from app.models import ProductScore

logger = logging.getLogger(__name__)

TELEGRAM_CHAT_ID = 7041182277


def _format_message(results: list[ProductScore]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [
        f"🛒 ZDailyScan — {today}",
        "Top 10 oportunidades AliExpress → LojaHi Select",
        "",
    ]
    for i, p in enumerate(results[:10], start=1):
        cost = f"{p.import_cost_brl:.2f}".replace(".", ",")
        price = f"{p.suggested_price_brl:.2f}".replace(".", ",")
        lines += [
            f"{i}. {p.name} ⭐ score: {p.score:.2f}",
            f"   💰 Custo importação: R$ {cost}",
            f"   🏷️ Sugestão de venda: R$ {price}",
            f"   📦 Demanda ML: {p.ml_listing_count} anúncios",
            f"   🔗 {p.aliexpress_url}",
            "",
        ]
    return "\n".join(lines).strip()


async def send_daily_report(
    results: list[ProductScore],
    mc_url: str | None = None,
    mc_api_key: str | None = None,
) -> bool:
    if mc_url is None or mc_api_key is None:
        try:
            from app.config import Settings
            settings = Settings()
            mc_url = mc_url or settings.mc_url
            mc_api_key = mc_api_key or settings.mc_api_key
        except Exception as exc:
            logger.error("Falha ao carregar settings para Telegram reporter: %s", exc)
            return False

    message = _format_message(results)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{mc_url}/telegram/reply",
                headers={"x-api-key": mc_api_key},
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            )
            response.raise_for_status()
            return True
    except Exception as exc:
        logger.error("Falha ao enviar relatório Telegram via Mission Control: %s", exc)
        return False
