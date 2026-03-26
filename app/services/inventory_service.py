"""Inventory service — automatic parts deduction from worklogs."""
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def deduct_parts_for_ticket(ticket_id: int, db: AsyncSession) -> None:
    """Aggregate all worklog parts for *ticket_id* and decrement inventory quantities.

    Quantities are clamped to 0 — they will never go negative.

    Args:
        ticket_id: The numeric ticket PK whose worklogs should be aggregated.
        db: Active async database session.  The caller is responsible for
            committing after this function returns.
    """
    from app.models.inventory_item import InventoryItem
    from app.models.worklog import Worklog, WorklogPart

    # Fetch all worklogs for the ticket
    wl_result = await db.execute(
        select(Worklog).where(Worklog.ticket_id == ticket_id)
    )
    worklogs = wl_result.scalars().all()

    if not worklogs:
        return

    worklog_ids = [wl.id for wl in worklogs]

    # Fetch all parts across those worklogs
    parts_result = await db.execute(
        select(WorklogPart).where(WorklogPart.worklog_id.in_(worklog_ids))
    )
    parts = parts_result.scalars().all()

    if not parts:
        return

    # Aggregate total quantity per inventory_id
    totals: dict[int, int] = defaultdict(int)
    for part in parts:
        if part.inventory_id:
            totals[part.inventory_id] += part.quantity

    # Apply deductions
    for inv_id, qty in totals.items():
        inv_result = await db.execute(
            select(InventoryItem).where(InventoryItem.id == inv_id)
        )
        item = inv_result.scalar_one_or_none()
        if item:
            item.quantity = max(0, item.quantity - qty)
            db.add(item)
            logger.debug(
                "Deducted %d unit(s) of inventory item %d for ticket %d",
                qty, inv_id, ticket_id,
            )
