"""Preventive Maintenance CRUD routes."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.preventive_maintenance import PreventiveMaintenance
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.pm import PMCreate, PMResponse, PMUpdate

router = APIRouter(prefix="/pm", tags=["preventive-maintenance"])


@router.get("", response_model=PaginatedResponse[PMResponse])
async def list_pms(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    property_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    assigned_to: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    count_q = select(func.count(PreventiveMaintenance.id))
    query = select(PreventiveMaintenance)

    filters = []
    if property_id:
        filters.append(PreventiveMaintenance.property_id == property_id)
    if status_filter:
        filters.append(PreventiveMaintenance.status == status_filter)
    if assigned_to:
        filters.append(PreventiveMaintenance.assigned_to_id == assigned_to)

    for f in filters:
        count_q = count_q.where(f)
        query = query.where(f)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        query.order_by(PreventiveMaintenance.next_due_date.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    pms = result.scalars().all()

    # Map assigned_to_id → assigned_to field for schema
    pm_list = []
    for pm in pms:
        pm_dict = {
            "id": pm.id,
            "title": pm.title,
            "description": pm.description,
            "asset_id": pm.asset_id,
            "property_id": pm.property_id,
            "location_id": pm.location_id,
            "frequency": pm.frequency,
            "next_due_date": pm.next_due_date,
            "assigned_to": pm.assigned_to_id,
            "status": pm.status,
            "created_at": pm.created_at,
            "updated_at": pm.updated_at,
        }
        pm_list.append(PMResponse(**pm_dict))

    return PaginatedResponse(
        items=pm_list,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=PMResponse, status_code=status.HTTP_201_CREATED)
async def create_pm(
    payload: PMCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    pm = PreventiveMaintenance(
        title=payload.title,
        description=payload.description,
        asset_id=payload.asset_id,
        property_id=payload.property_id,
        location_id=payload.location_id,
        frequency=payload.frequency,
        next_due_date=payload.next_due_date,
        assigned_to_id=payload.assigned_to,
        status=payload.status,
    )
    db.add(pm)
    await db.commit()
    await db.refresh(pm)

    return PMResponse(
        id=pm.id,
        title=pm.title,
        description=pm.description,
        asset_id=pm.asset_id,
        property_id=pm.property_id,
        location_id=pm.location_id,
        frequency=pm.frequency,
        next_due_date=pm.next_due_date,
        assigned_to=pm.assigned_to_id,
        status=pm.status,
        created_at=pm.created_at,
        updated_at=pm.updated_at,
    )


@router.get("/{pm_id}", response_model=PMResponse)
async def get_pm(
    pm_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(PreventiveMaintenance).where(PreventiveMaintenance.id == pm_id))
    pm = result.scalar_one_or_none()
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PM schedule not found")

    return PMResponse(
        id=pm.id,
        title=pm.title,
        description=pm.description,
        asset_id=pm.asset_id,
        property_id=pm.property_id,
        location_id=pm.location_id,
        frequency=pm.frequency,
        next_due_date=pm.next_due_date,
        assigned_to=pm.assigned_to_id,
        status=pm.status,
        created_at=pm.created_at,
        updated_at=pm.updated_at,
    )


@router.patch("/{pm_id}", response_model=PMResponse)
async def update_pm(
    pm_id: int,
    payload: PMUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(PreventiveMaintenance).where(PreventiveMaintenance.id == pm_id))
    pm = result.scalar_one_or_none()
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PM schedule not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "assigned_to":
            pm.assigned_to_id = value
        else:
            setattr(pm, field, value)

    db.add(pm)
    await db.commit()
    await db.refresh(pm)

    return PMResponse(
        id=pm.id,
        title=pm.title,
        description=pm.description,
        asset_id=pm.asset_id,
        property_id=pm.property_id,
        location_id=pm.location_id,
        frequency=pm.frequency,
        next_due_date=pm.next_due_date,
        assigned_to=pm.assigned_to_id,
        status=pm.status,
        created_at=pm.created_at,
        updated_at=pm.updated_at,
    )


@router.delete("/{pm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pm(
    pm_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(PreventiveMaintenance).where(PreventiveMaintenance.id == pm_id))
    pm = result.scalar_one_or_none()
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PM schedule not found")
    await db.delete(pm)
    await db.commit()
