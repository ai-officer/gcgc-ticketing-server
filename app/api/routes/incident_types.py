"""Incident Type CRUD routes."""
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.incident_type import IncidentType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.incident_type import IncidentTypeCreate, IncidentTypeResponse, IncidentTypeUpdate

router = APIRouter(prefix="/incident-types", tags=["incident-types"])


@router.get("", response_model=PaginatedResponse[IncidentTypeResponse])
async def list_incident_types(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    total = (await db.execute(select(func.count(IncidentType.id)))).scalar_one()
    result = await db.execute(
        select(IncidentType).offset((page - 1) * limit).limit(limit)
    )
    its = result.scalars().all()

    return PaginatedResponse(
        items=its,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=IncidentTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_incident_type(
    payload: IncidentTypeCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    it = IncidentType(**payload.model_dump())
    db.add(it)
    await db.commit()
    await db.refresh(it)
    return it


@router.get("/{it_id}", response_model=IncidentTypeResponse)
async def get_incident_type(
    it_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(IncidentType).where(IncidentType.id == it_id))
    it = result.scalar_one_or_none()
    if not it:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident type not found")
    return it


@router.patch("/{it_id}", response_model=IncidentTypeResponse)
async def update_incident_type(
    it_id: int,
    payload: IncidentTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(IncidentType).where(IncidentType.id == it_id))
    it = result.scalar_one_or_none()
    if not it:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident type not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(it, field, value)

    db.add(it)
    await db.commit()
    await db.refresh(it)
    return it


@router.delete("/{it_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident_type(
    it_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(IncidentType).where(IncidentType.id == it_id))
    it = result.scalar_one_or_none()
    if not it:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident type not found")
    await db.delete(it)
    await db.commit()
