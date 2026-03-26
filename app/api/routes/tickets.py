"""Ticket CRUD and lifecycle routes."""
import json
import math
import os
import shutil
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db, require_role
from app.models.ticket import Ticket, TicketRating, TicketTask
from app.models.user import User
from app.models.worklog import Worklog, WorklogPart, WorklogPhoto
from app.schemas.common import PaginatedResponse
from app.schemas.ticket import (
    TicketAssignRequest,
    TicketCreate,
    TicketRateRequest,
    TicketResponse,
    TicketStatusRequest,
    TicketUpdate,
)
from app.schemas.worklog import WorklogResponse
from app.services.inventory_service import deduct_parts_for_ticket
from app.services.notification_service import notify_ticket_assigned, notify_ticket_created
from app.services.sla_service import calculate_sla_deadlines

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _parse_ticket_id(ticket_id: str) -> int:
    """Convert 'TKT-1001' → 1001, raising 404 on malformed input."""
    try:
        return int(ticket_id.replace("TKT-", ""))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")


def _ticket_query():
    """Return a select statement with all eager-loaded relationships."""
    return (
        select(Ticket)
        .options(
            selectinload(Ticket.tasks),
            selectinload(Ticket.rating),
        )
    )


@router.get("", response_model=PaginatedResponse[TicketResponse])
async def list_tickets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    property_id: Optional[int] = Query(default=None),
    assignee_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tickets with optional filters. Requestors see only their own tickets."""
    query = _ticket_query()

    # Role-based filtering
    if current_user.role == "requestor":
        query = query.where(Ticket.requestor_id == current_user.id)

    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if priority:
        query = query.where(Ticket.priority == priority)
    if category:
        query = query.where(Ticket.category == category)
    if property_id:
        query = query.where(Ticket.property_id == property_id)
    if assignee_id:
        query = query.where(Ticket.assignee_id == assignee_id)
    if search:
        query = query.where(
            or_(
                Ticket.title.ilike(f"%{search}%"),
                Ticket.id.cast(String).ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count(Ticket.id))
    if current_user.role == "requestor":
        count_query = count_query.where(Ticket.requestor_id == current_user.id)
    if status_filter:
        count_query = count_query.where(Ticket.status == status_filter)
    if priority:
        count_query = count_query.where(Ticket.priority == priority)
    if category:
        count_query = count_query.where(Ticket.category == category)
    if property_id:
        count_query = count_query.where(Ticket.property_id == property_id)
    if assignee_id:
        count_query = count_query.where(Ticket.assignee_id == assignee_id)
    if search:
        count_query = count_query.where(
            or_(
                Ticket.title.ilike(f"%{search}%"),
                Ticket.id.cast(String).ilike(f"%{search}%"),
            )
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Ticket.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    tickets = result.scalars().all()

    return PaginatedResponse(
        items=tickets,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new ticket. SLA deadlines are computed automatically."""
    requestor_id = payload.requestor_id or current_user.id
    sla_deadline, response_sla_deadline = await calculate_sla_deadlines(payload.priority, db)

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        status="open",
        requestor_id=requestor_id,
        property_id=payload.property_id,
        location_id=payload.location_id,
        room_number=payload.room_number,
        asset_id=payload.asset_id,
        cost=payload.cost,
        sla_deadline=sla_deadline,
        response_sla_deadline=response_sla_deadline,
    )
    db.add(ticket)
    await db.flush()  # get ticket.id before adding children

    if payload.tasks:
        for task_data in payload.tasks:
            task = TicketTask(
                ticket_id=ticket.id,
                description=task_data.description,
                is_completed=task_data.is_completed,
            )
            db.add(task)

    await db.flush()
    await notify_ticket_created(ticket, db)
    await db.commit()
    await db.refresh(ticket)

    # Reload with relationships
    result = await db.execute(_ticket_query().where(Ticket.id == ticket.id))
    return result.scalar_one()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single ticket by its TKT-XXXX identifier."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == "requestor" and ticket.requestor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update ticket fields. Requestors cannot change status/assignee."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Requestors may only update description / room_number
    if current_user.role == "requestor":
        allowed = {"description", "room_number"}
        update_data = {k: v for k, v in update_data.items() if k in allowed}

    # Auto-set resolved_at when status transitions to resolved
    if update_data.get("status") == "resolved" and ticket.status != "resolved":
        ticket.resolved_at = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.add(ticket)
    await db.commit()

    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    return result.scalar_one()


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    """Delete a ticket (admin only)."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(select(Ticket).where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    await db.delete(ticket)
    await db.commit()


@router.patch("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: str,
    payload: TicketAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "service_desk")),
):
    """Assign a ticket to a technician (admin / service_desk only)."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket.assignee_id = payload.assignee_id
    if ticket.status == "open":
        ticket.status = "assigned"

    db.add(ticket)
    await db.flush()
    await notify_ticket_assigned(ticket, payload.assignee_id, db)
    await db.commit()

    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    return result.scalar_one()


@router.patch("/{ticket_id}/rate", response_model=TicketResponse)
async def rate_ticket(
    ticket_id: str,
    payload: TicketRateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a satisfaction rating for a resolved ticket."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if ticket.status not in ("resolved", "closed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only resolved or closed tickets can be rated",
        )

    if ticket.rating:
        ticket.rating.score = payload.score
        ticket.rating.feedback = payload.feedback
        db.add(ticket.rating)
    else:
        rating = TicketRating(
            ticket_id=ticket.id,
            score=payload.score,
            feedback=payload.feedback,
        )
        db.add(rating)

    await db.commit()
    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    return result.scalar_one()


@router.get("/{ticket_id}/worklogs", response_model=List[WorklogResponse])
async def get_ticket_worklogs(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get all worklogs for a ticket."""
    int_id = _parse_ticket_id(ticket_id)
    from sqlalchemy.orm import selectinload as sl
    query = (
        select(Worklog)
        .options(sl(Worklog.parts), sl(Worklog.photos))
        .where(Worklog.ticket_id == int_id)
        .order_by(Worklog.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{ticket_id}/worklogs", response_model=WorklogResponse, status_code=status.HTTP_201_CREATED)
async def add_ticket_worklog(
    ticket_id: str,
    activity: str = Form(...),
    time_spent_minutes: int = Form(default=0),
    parts_used: Optional[str] = Form(default=None),
    photos: Optional[List[UploadFile]] = File(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a worklog to a ticket (multipart/form-data with optional photo uploads)."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(select(Ticket).where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    technician_id = current_user.id if current_user.role in ("technician", "admin", "service_desk") else None

    worklog = Worklog(
        ticket_id=int_id,
        technician_id=technician_id,
        activity=activity,
        time_spent_minutes=time_spent_minutes,
    )
    db.add(worklog)
    await db.flush()

    if parts_used:
        try:
            parts_list = json.loads(parts_used)
            for part in parts_list:
                wp = WorklogPart(
                    worklog_id=worklog.id,
                    inventory_id=int(part.get("inventoryId", part.get("inventory_id", 0))),
                    quantity=int(part.get("quantity", 1)),
                )
                db.add(wp)
        except (json.JSONDecodeError, ValueError):
            pass

    if photos:
        upload_dir = f"uploads/worklogs/{worklog.id}"
        os.makedirs(upload_dir, exist_ok=True)
        for i, photo_file in enumerate(photos):
            if photo_file and photo_file.filename:
                ext = os.path.splitext(photo_file.filename)[1] or ".jpg"
                filename = f"photo_{i}{ext}"
                filepath = os.path.join(upload_dir, filename)
                with open(filepath, "wb") as f:
                    shutil.copyfileobj(photo_file.file, f)
                photo_url = f"/uploads/worklogs/{worklog.id}/{filename}"
                db.add(WorklogPhoto(worklog_id=worklog.id, url=photo_url))

    if ticket.status == "assigned":
        ticket.status = "in-progress"
        db.add(ticket)

    await db.commit()

    from sqlalchemy.orm import selectinload as sl
    result = await db.execute(
        select(Worklog).options(sl(Worklog.parts), sl(Worklog.photos)).where(Worklog.id == worklog.id)
    )
    return result.scalar_one()


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update ticket status. Triggers inventory deduction when resolving."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    old_status = ticket.status
    ticket.status = payload.status

    if payload.status == "resolved" and old_status != "resolved":
        ticket.resolved_at = datetime.now(timezone.utc)
        if not ticket.parts_deducted:
            await deduct_parts_for_ticket(int_id, db)
            ticket.parts_deducted = True

    db.add(ticket)
    await db.commit()
    result = await db.execute(_ticket_query().where(Ticket.id == int_id))
    return result.scalar_one()


@router.patch("/{ticket_id}/tasks/{task_id}", response_model=dict)
async def toggle_task(
    ticket_id: str,
    task_id: int,
    is_completed: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Set a task's completion status via ?is_completed=true/false."""
    from app.models.ticket import TicketTask as TT
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(
        select(TT).where(TT.id == task_id, TT.ticket_id == int_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task.is_completed = is_completed
    db.add(task)
    await db.commit()
    return {"id": task.id, "isCompleted": task.is_completed}


@router.post("/{ticket_id}/deduct-parts", response_model=dict)
async def deduct_parts(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "technician")),
):
    """Manually trigger inventory deduction for all worklog parts on this ticket."""
    int_id = _parse_ticket_id(ticket_id)
    result = await db.execute(select(Ticket).where(Ticket.id == int_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if ticket.parts_deducted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parts have already been deducted for this ticket",
        )

    await deduct_parts_for_ticket(int_id, db)
    ticket.parts_deducted = True
    db.add(ticket)
    await db.commit()
    return {"message": "Parts deducted successfully"}
