"""Notification service — creates in-app Notification rows."""
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)


async def _create_notification(
    db: AsyncSession, user_id: int, message: str, link: str | None = None
) -> None:
    """Insert a single Notification row for *user_id*."""
    notif = Notification(user_id=user_id, message=message, link=link)
    db.add(notif)


async def _get_users_by_roles(db: AsyncSession, roles: List[str]) -> List[User]:
    """Return all users whose role is in *roles*."""
    result = await db.execute(select(User).where(User.role.in_(roles)))
    return result.scalars().all()


async def notify_ticket_created(ticket, db: AsyncSession) -> None:
    """Create notifications for all admin and service_desk users when a ticket is opened."""
    admins = await _get_users_by_roles(db, ["admin", "service_desk"])
    link = f"/tickets/TKT-{ticket.id:04d}"
    for user in admins:
        await _create_notification(
            db,
            user.id,
            f"New ticket created: {ticket.title} [{ticket.priority.upper()}]",
            link,
        )
    await db.flush()
    logger.debug("Sent ticket-created notifications for ticket %d to %d users", ticket.id, len(admins))


async def notify_ticket_assigned(ticket, assignee_id: int, db: AsyncSession) -> None:
    """Create a notification for the technician/user the ticket was assigned to."""
    link = f"/tickets/TKT-{ticket.id:04d}"
    await _create_notification(
        db,
        assignee_id,
        f"Ticket assigned to you: {ticket.title}",
        link,
    )
    await db.flush()
    logger.debug("Sent assignment notification for ticket %d to user %d", ticket.id, assignee_id)


async def notify_sla_breach(ticket, db: AsyncSession) -> None:
    """Create notifications for all admin users when a ticket breaches its SLA."""
    admins = await _get_users_by_roles(db, ["admin"])
    link = f"/tickets/TKT-{ticket.id:04d}"
    for user in admins:
        await _create_notification(
            db,
            user.id,
            f"SLA BREACH — ticket escalated: {ticket.title} (TKT-{ticket.id:04d})",
            link,
        )
    await db.flush()
    logger.debug("Sent SLA-breach notifications for ticket %d to %d admins", ticket.id, len(admins))
