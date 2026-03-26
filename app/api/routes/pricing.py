"""Pricing Record CRUD routes."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.pricing_record import PricingRecord
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.pricing import PricingRecordCreate, PricingRecordResponse, PricingRecordUpdate

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("", response_model=PaginatedResponse[PricingRecordResponse])
async def list_pricing(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    category: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    count_q = select(func.count(PricingRecord.id))
    query = select(PricingRecord)

    if category:
        count_q = count_q.where(PricingRecord.category == category)
        query = query.where(PricingRecord.category == category)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        query.order_by(PricingRecord.effective_date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    records = result.scalars().all()

    return PaginatedResponse(
        items=records,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=PricingRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_record(
    payload: PricingRecordCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    record = PricingRecord(**payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{record_id}", response_model=PricingRecordResponse)
async def get_pricing_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(PricingRecord).where(PricingRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing record not found")
    return record


@router.patch("/{record_id}", response_model=PricingRecordResponse)
async def update_pricing_record(
    record_id: int,
    payload: PricingRecordUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(PricingRecord).where(PricingRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing record not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pricing_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(PricingRecord).where(PricingRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing record not found")
    await db.delete(record)
    await db.commit()
