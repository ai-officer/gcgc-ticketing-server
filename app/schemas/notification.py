"""Notification request/response schemas."""
from datetime import datetime
from typing import Optional

from app.schemas.common import BaseSchema


class NotificationResponse(BaseSchema):
    id: int
    user_id: int
    message: str
    read: bool
    link: Optional[str] = None
    created_at: Optional[datetime] = None


class MarkReadRequest(BaseSchema):
    notification_ids: Optional[list[int]] = None  # None = mark all read
