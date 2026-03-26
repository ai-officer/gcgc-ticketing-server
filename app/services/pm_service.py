"""Preventive Maintenance service — due-date checking and auto-ticket generation."""
import logging
from datetime import datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Mapping from frequency string to relativedelta / timedelta kwargs
_FREQUENCY_DELTAS = {
    "daily": {"days": 1},
    "weekly": {"weeks": 1},
    "monthly": {"months": 1},
    "quarterly": {"months": 3},
    "biannually": {"months": 6},
    "annually": {"years": 1},
}


async def advance_date(dt: datetime, frequency: str) -> datetime:
    """Return *dt* incremented by the amount dictated by *frequency*.

    Args:
        dt: The current next_due_date.
        frequency: One of daily|weekly|monthly|quarterly|biannually|annually.

    Returns:
        New datetime advanced by one period.
    """
    delta_kwargs = _FREQUENCY_DELTAS.get(frequency.lower(), {"months": 1})
    try:
        return dt + relativedelta(**delta_kwargs)
    except TypeError:
        # relativedelta doesn't support weeks directly in all versions
        return dt + timedelta(weeks=delta_kwargs.get("weeks", 1))


async def check_pm_due_dates(db: AsyncSession) -> None:
    """Find all active PMs whose next_due_date has passed and create work tickets.

    Deduplication: only creates a new ticket when no open/in-progress ticket
    with ``source_pm_id`` matching the PM already exists.
    """
    from app.models.preventive_maintenance import PreventiveMaintenance
    from app.models.ticket import Ticket

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(PreventiveMaintenance).where(
            PreventiveMaintenance.status == "active",
            PreventiveMaintenance.next_due_date <= now,
        )
    )
    due_pms = result.scalars().all()

    for pm in due_pms:
        # Check deduplication: is there already an open/in-progress ticket for this PM?
        dup_result = await db.execute(
            select(Ticket).where(
                Ticket.source_pm_id == pm.id,
                Ticket.status.in_(["open", "assigned", "in-progress"]),
            )
        )
        existing = dup_result.scalar_one_or_none()
        if existing:
            # Only advance the date; do not create a duplicate ticket
            pm.next_due_date = await advance_date(pm.next_due_date, pm.frequency)
            db.add(pm)
            continue

        # Create the auto-generated ticket
        ticket = Ticket(
            title=f"[PM] {pm.title}",
            description=pm.description,
            category="Preventive Maintenance",
            priority="medium",
            status="open",
            property_id=pm.property_id,
            location_id=pm.location_id,
            asset_id=pm.asset_id,
            assignee_id=pm.assigned_to_id,
            source_pm_id=pm.id,
        )
        db.add(ticket)

        # Advance the PM's next_due_date
        pm.next_due_date = await advance_date(pm.next_due_date, pm.frequency)
        db.add(pm)

    if due_pms:
        await db.commit()
        logger.info("Processed %d due PM schedule(s)", len(due_pms))


async def check_pm_due_dates_job() -> None:
    """Scheduler entry-point: opens its own DB session then calls check_pm_due_dates."""
    async with AsyncSessionLocal() as db:
        try:
            await check_pm_due_dates(db)
        except Exception:
            logger.exception("Error in check_pm_due_dates scheduled job")
            await db.rollback()
