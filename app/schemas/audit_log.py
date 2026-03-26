"""AuditLog response schemas."""
from datetime import datetime
from typing import Optional

from app.schemas.common import BaseSchema


class AuditLogResponse(BaseSchema):
    id: int
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    timestamp: Optional[datetime] = None
