"""Announcement request/response schemas."""
from datetime import datetime
from typing import Optional

from app.schemas.common import BaseSchema


class AnnouncementBase(BaseSchema):
    title: str
    content: str


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None


class AnnouncementResponse(AnnouncementBase):
    id: int
    author_id: Optional[int] = None
    date: Optional[datetime] = None
