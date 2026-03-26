"""Worklog routes — activity logs with parts and photos."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db, require_role
from app.models.ticket import Ticket
from app.models.user import User
from app.models.worklog import Worklog, WorklogPart, WorklogPhoto
from app.schemas.common import PaginatedResponse
from app.schemas.worklog import WorklogCreate, WorklogResponse, WorklogUpdate

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


def _worklog_query():
    return (
        select(Worklog)
        .options(
            selectinload(Worklog.parts),
            selectinload(Worklog.photos),
        )
    )


@router.get("", response_model=PaginatedResponse[WorklogResponse])
async def list_worklogs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    ticket_id: Optional[int] = Query(default=None),
    technician_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List worklogs with optional filters."""
    count_query = select(func.count(Worklog.id))
    query = _worklog_query()

    if ticket_id:
        query = query.where(Worklog.ticket_id == ticket_id)
        count_query = count_query.where(Worklog.ticket_id == ticket_id)
    if technician_id:
        query = query.where(Worklog.technician_id == technician_id)
        count_query = count_query.where(Worklog.technician_id == technician_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Worklog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    worklogs = result.scalars().all()

    return PaginatedResponse(
        items=worklogs,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=WorklogResponse, status_code=status.HTTP_201_CREATED)
async def create_worklog(
    payload: WorklogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a worklog entry. The technician is set to the current user unless overridden."""
    # Validate the ticket exists
    ticket_result = await db.execute(select(Ticket).where(Ticket.id == payload.ticket_id))
    if not ticket_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    technician_id = current_user.id if current_user.role in ("technician", "admin") else None

    worklog = Worklog(
        ticket_id=payload.ticket_id,
        technician_id=technician_id,
        activity=payload.activity,
        time_spent_minutes=payload.time_spent_minutes,
    )
    db.add(worklog)
    await db.flush()

    if payload.parts_used:
        for part in payload.parts_used:
            wp = WorklogPart(
                worklog_id=worklog.id,
                inventory_id=part.inventory_id,
                quantity=part.quantity,
            )
            db.add(wp)

    if payload.photos:
        for url in payload.photos:
            photo = WorklogPhoto(worklog_id=worklog.id, url=url)
            db.add(photo)

    # Auto-advance ticket status to in-progress if it is still assigned
    ticket_result2 = await db.execute(select(Ticket).where(Ticket.id == payload.ticket_id))
    ticket = ticket_result2.scalar_one_or_none()
    if ticket and ticket.status == "assigned":
        ticket.status = "in-progress"
        db.add(ticket)

    await db.commit()

    result = await db.execute(_worklog_query().where(Worklog.id == worklog.id))
    return result.scalar_one()


@router.get("/{worklog_id}", response_model=WorklogResponse)
async def get_worklog(
    worklog_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get a single worklog by ID."""
    result = await db.execute(_worklog_query().where(Worklog.id == worklog_id))
    worklog = result.scalar_one_or_none()
    if not worklog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worklog not found")
    return worklog


@router.patch("/{worklog_id}", response_model=WorklogResponse)
async def update_worklog(
    worklog_id: int,
    payload: WorklogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a worklog. Technicians can only edit their own; admins can edit any."""
    result = await db.execute(_worklog_query().where(Worklog.id == worklog_id))
    worklog = result.scalar_one_or_none()
    if not worklog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worklog not found")

    if current_user.role not in ("admin",) and worklog.technician_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(worklog, field, value)

    db.add(worklog)
    await db.commit()

    result = await db.execute(_worklog_query().where(Worklog.id == worklog_id))
    return result.scalar_one()


@router.delete("/{worklog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worklog(
    worklog_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    """Delete a worklog (admin only)."""
    result = await db.execute(select(Worklog).where(Worklog.id == worklog_id))
    worklog = result.scalar_one_or_none()
    if not worklog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worklog not found")
    await db.delete(worklog)
    await db.commit()
