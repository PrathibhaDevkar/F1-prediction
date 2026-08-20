"""Embeds an APScheduler job in the FastAPI app's lifespan. Race weekends
are infrequent (~biweekly), so a 45-minute interval is cheap — each check
is just a calendar comparison unless it actually finds a new completed
round, which is the only case that triggers real work (a retrain).
"""
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pipeline.retrain import check_and_process_new_results

CHECK_INTERVAL_MINUTES = 45

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        check_and_process_new_results,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        next_run_time=datetime.now(),  # also run once immediately on startup
        id="check_new_race_results",
    )
    _scheduler.start()
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
