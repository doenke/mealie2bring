from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .sync import sync_mealie_to_bring

def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_mealie_to_bring, "interval", minutes=3, id="mealie-bring-sync", max_instances=1, coalesce=True)
    return scheduler
