"""Worklog request/response schemas."""
from datetime import datetime
from typing import List, Optional

from app.schemas.common import BaseSchema


class WorklogPartSchema(BaseSchema):
    inventory_id: int
    quantity: int


class WorklogCreate(BaseSchema):
    ticket_id: int
    activity: str
    time_spent_minutes: int = 0
    parts_used: Optional[List[WorklogPartSchema]] = None
    photos: Optional[List[str]] = None


class WorklogUpdate(BaseSchema):
    activity: Optional[str] = None
    time_spent_minutes: Optional[int] = None


class WorklogPartResponse(BaseSchema):
    id: int
    inventory_id: Optional[int] = None
    quantity: int


class WorklogPhotoResponse(BaseSchema):
    id: int
    url: str


class WorklogResponse(BaseSchema):
    id: int
    ticket_id: int
    technician_id: Optional[int] = None
    activity: str
    time_spent_minutes: int
    created_at: Optional[datetime] = None
    parts: Optional[List[WorklogPartResponse]] = None
    photos: Optional[List[WorklogPhotoResponse]] = None
