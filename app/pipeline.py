import logging

from app.models import ProductScore
from app.reporters.telegram_reporter import send_daily_report
from app.reporters.file_reporter import save_daily_report

logger = logging.getLogger(__name__)


async def run_daily_scan() -> list[ProductScore]:
    results: list[ProductScore] = []

    # TODO: populate results from AliExpress scan + ML analysis in future tasks

    if results:
        save_daily_report(results)
        sent = await send_daily_report(results)
        if not sent:
            logger.warning("Relatório não entregue via Telegram — verifique Mission Control")

    return results
