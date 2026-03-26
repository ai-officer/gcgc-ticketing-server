"""Announcement CRUD routes."""
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=PaginatedResponse[AnnouncementResponse])
async def list_announcements(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    total = (await db.execute(select(func.count(Announcement.id)))).scalar_one()
    result = await db.execute(
        select(Announcement)
        .order_by(Announcement.date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    announcements = result.scalars().all()

    return PaginatedResponse(
        items=announcements,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    ann = Announcement(
        title=payload.title,
        content=payload.content,
        author_id=current_user.id,
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann


@router.get("/{ann_id}", response_model=AnnouncementResponse)
async def get_announcement(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    return ann


@router.patch("/{ann_id}", response_model=AnnouncementResponse)
async def update_announcement(
    ann_id: int,
    payload: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ann, field, value)

    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann


@router.delete("/{ann_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    await db.delete(ann)
    await db.commit()
