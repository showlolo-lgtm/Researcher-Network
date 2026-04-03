import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import async_session
from app.services.ingestion import run_refresh

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_job():
    logger.info("Starting scheduled refresh")
    async with async_session() as db:
        await run_refresh(db)
    logger.info("Scheduled refresh complete")


def setup_scheduler():
    parts = settings.refresh_cron.split()
    if len(parts) == 5:
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1], day=parts[2],
            month=parts[3], day_of_week=parts[4],
        )
        scheduler.add_job(refresh_job, trigger, id="refresh", replace_existing=True)
        scheduler.start()
        logger.info(f"Scheduler started with cron: {settings.refresh_cron}")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
