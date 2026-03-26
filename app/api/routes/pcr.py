"""Project Change Request CRUD routes."""
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.project_change_request import ProjectChangeRequest
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.pcr import PCRCreate, PCRResponse, PCRReviewRequest, PCRUpdate

router = APIRouter(prefix="/pcr", tags=["pcr"])


def _orm_to_response(pcr: ProjectChangeRequest) -> PCRResponse:
    return PCRResponse(
        id=pcr.id,
        title=pcr.title,
        description=pcr.description,
        impact_analysis=pcr.impact_analysis,
        cost_impact=float(pcr.cost_impact) if pcr.cost_impact is not None else None,
        schedule_impact_days=pcr.schedule_impact_days,
        status=pcr.status,
        submitted_by=pcr.submitted_by_id,
        submitted_at=pcr.submitted_at,
        approved_by=pcr.approved_by_id,
        approved_at=pcr.approved_at,
    )


@router.get("", response_model=PaginatedResponse[PCRResponse])
async def list_pcrs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    count_q = select(func.count(ProjectChangeRequest.id))
    query = select(ProjectChangeRequest)

    if status_filter:
        count_q = count_q.where(ProjectChangeRequest.status == status_filter)
        query = query.where(ProjectChangeRequest.status == status_filter)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        query.order_by(ProjectChangeRequest.submitted_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    pcrs = result.scalars().all()

    return PaginatedResponse(
        items=[_orm_to_response(pcr) for pcr in pcrs],
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=PCRResponse, status_code=status.HTTP_201_CREATED)
async def create_pcr(
    payload: PCRCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pcr = ProjectChangeRequest(
        title=payload.title,
        description=payload.description,
        impact_analysis=payload.impact_analysis,
        cost_impact=payload.cost_impact,
        schedule_impact_days=payload.schedule_impact_days,
        status="pending",
        submitted_by_id=current_user.id,
    )
    db.add(pcr)
    await db.commit()
    await db.refresh(pcr)
    return _orm_to_response(pcr)


@router.get("/{pcr_id}", response_model=PCRResponse)
async def get_pcr(
    pcr_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProjectChangeRequest).where(ProjectChangeRequest.id == pcr_id))
    pcr = result.scalar_one_or_none()
    if not pcr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PCR not found")
    return _orm_to_response(pcr)


@router.patch("/{pcr_id}", response_model=PCRResponse)
async def update_pcr(
    pcr_id: int,
    payload: PCRUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ProjectChangeRequest).where(ProjectChangeRequest.id == pcr_id))
    pcr = result.scalar_one_or_none()
    if not pcr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PCR not found")

    # Only submitter or admin may edit
    if current_user.role != "admin" and pcr.submitted_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pcr, field, value)

    db.add(pcr)
    await db.commit()
    await db.refresh(pcr)
    return _orm_to_response(pcr)


@router.post("/{pcr_id}/review", response_model=PCRResponse)
async def review_pcr(
    pcr_id: int,
    payload: PCRReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Approve or reject a PCR (admin only)."""
    if payload.status not in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'approved' or 'rejected'",
        )

    result = await db.execute(select(ProjectChangeRequest).where(ProjectChangeRequest.id == pcr_id))
    pcr = result.scalar_one_or_none()
    if not pcr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PCR not found")

    pcr.status = payload.status
    pcr.approved_by_id = current_user.id
    pcr.approved_at = datetime.now(timezone.utc)

    db.add(pcr)
    await db.commit()
    await db.refresh(pcr)
    return _orm_to_response(pcr)


@router.delete("/{pcr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pcr(
    pcr_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(ProjectChangeRequest).where(ProjectChangeRequest.id == pcr_id))
    pcr = result.scalar_one_or_none()
    if not pcr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PCR not found")
    await db.delete(pcr)
    await db.commit()
