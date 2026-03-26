"""SLA service — deadline calculation and breach detection."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def calculate_sla_deadlines(
    priority: str, db: AsyncSession
) -> Tuple[datetime, datetime]:
    """Derive SLA and response-SLA deadlines for a given priority string.

    Looks up the matching :class:`~app.models.incident_type.IncidentType` by
    name (case-insensitive match against *priority*).  Falls back to sensible
    defaults when no matching incident type exists.

    Args:
        priority: One of ``low``, ``medium``, ``high``, ``critical``.
        db: Active async database session.

    Returns:
        ``(sla_deadline, response_sla_deadline)`` as timezone-aware datetimes.
    """
    from app.models.incident_type import IncidentType  # avoid circular imports

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(IncidentType).where(
            IncidentType.name.ilike(priority)
        )
    )
    incident_type = result.scalar_one_or_none()

    if incident_type:
        sla_deadline = now + timedelta(hours=incident_type.sla_hours)
        response_sla_deadline = now + timedelta(hours=incident_type.response_sla_hours)
    else:
        # Fallback defaults when no incident_type row matches
        fallback_hours = {"critical": 4, "high": 8, "medium": 24, "low": 72}
        fallback_response = {"critical": 1, "high": 2, "medium": 4, "low": 8}
        p = priority.lower()
        sla_deadline = now + timedelta(hours=fallback_hours.get(p, 24))
        response_sla_deadline = now + timedelta(hours=fallback_response.get(p, 4))

    return sla_deadline, response_sla_deadline


async def check_sla_breaches(db: AsyncSession) -> None:
    """Scan for non-resolved tickets past their SLA deadline and escalate them.

    For each breached ticket:
    - Sets ``escalated = True``
    - Bumps ``priority`` to ``'critical'``
    - Creates admin notifications via the notification service
    """
    from app.models.ticket import Ticket
    from app.services.notification_service import notify_sla_breach

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Ticket).where(
            Ticket.sla_deadline < now,
            Ticket.escalated.is_(False),
            Ticket.status.notin_(["resolved", "closed"]),
        )
    )
    breached_tickets = result.scalars().all()

    if not breached_tickets:
        return

    for ticket in breached_tickets:
        ticket.escalated = True
        ticket.priority = "critical"
        db.add(ticket)
        await notify_sla_breach(ticket, db)

    await db.commit()
    logger.info("Escalated %d SLA-breached ticket(s)", len(breached_tickets))


async def check_sla_breaches_job() -> None:
    """Scheduler entry-point: opens its own DB session then calls check_sla_breaches."""
    async with AsyncSessionLocal() as db:
        try:
            await check_sla_breaches(db)
        except Exception:
            logger.exception("Error in check_sla_breaches scheduled job")
            await db.rollback()
