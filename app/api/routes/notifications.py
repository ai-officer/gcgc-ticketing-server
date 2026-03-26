"""Notification routes — read/unread management for the current user."""
import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.notification import MarkReadRequest, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for the currently authenticated user."""
    count_q = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    query = select(Notification).where(Notification.user_id == current_user.id)

    if unread_only:
        count_q = count_q.where(Notification.read.is_(False))
        query = query.where(Notification.read.is_(False))

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    notifications = result.scalars().all()

    return PaginatedResponse(
        items=notifications,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("/mark-read", response_model=dict)
async def mark_read(
    payload: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark specific notifications (or all) as read for the current user."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .values(read=True)
    )

    if payload.notification_ids:
        stmt = stmt.where(Notification.id.in_(payload.notification_ids))

    await db.execute(stmt)
    await db.commit()
    return {"message": "Notifications marked as read"}


@router.get("/unread-count", response_model=dict)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the count of unread notifications for the current user."""
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read.is_(False),
        )
    )
    count = result.scalar_one()
    return {"count": count}
