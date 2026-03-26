"""APScheduler configuration — background jobs that run every 60 seconds."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.pm_service import check_pm_due_dates_job
from app.services.sla_service import check_sla_breaches_job

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _setup_jobs() -> None:
    """Register recurring jobs on the scheduler."""
    scheduler.add_job(
        check_sla_breaches_job,
        trigger="interval",
        seconds=60,
        id="sla_breach_check",
        replace_existing=True,
        misfire_grace_time=30,
    )
    scheduler.add_job(
        check_pm_due_dates_job,
        trigger="interval",
        seconds=60,
        id="pm_due_date_check",
        replace_existing=True,
        misfire_grace_time=30,
    )
    logger.info("Scheduled jobs registered: sla_breach_check, pm_due_date_check")


# Register jobs immediately when this module is first imported so that
# scheduler.start() called in main.py lifespan has them ready.
_setup_jobs()
