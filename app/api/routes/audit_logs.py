"""Audit Log read-only routes (admin only)."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    user_id: Optional[int] = Query(default=None),
    action: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    """List audit logs (admin only). Filter by user_id or action prefix."""
    count_q = select(func.count(AuditLog.id))
    query = select(AuditLog)

    if user_id:
        count_q = count_q.where(AuditLog.user_id == user_id)
        query = query.where(AuditLog.user_id == user_id)
    if action:
        count_q = count_q.where(AuditLog.action.ilike(f"{action}%"))
        query = query.where(AuditLog.action.ilike(f"{action}%"))

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        query.order_by(AuditLog.timestamp.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    logs = result.scalars().all()

    return PaginatedResponse(
        items=logs,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )
