from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.pipeline import run_daily_scan
from app.storage import save_scan


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def _daily_scan_job() -> None:
        result = await run_daily_scan()
        save_scan(result)

    scheduler.add_job(_daily_scan_job, "cron", hour=9, minute=0)
    return scheduler
