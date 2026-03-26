"""PreventiveMaintenance request/response schemas."""
from datetime import datetime
from typing import Optional

from app.schemas.common import BaseSchema


class PMBase(BaseSchema):
    title: str
    description: Optional[str] = None
    asset_id: Optional[int] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    frequency: str
    next_due_date: datetime
    assigned_to: Optional[int] = None
    status: str = "active"


class PMCreate(BaseSchema):
    title: str
    description: Optional[str] = None
    asset_id: Optional[int] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    frequency: str
    next_due_date: datetime
    assigned_to: Optional[int] = None
    status: str = "active"


class PMUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    asset_id: Optional[int] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    frequency: Optional[str] = None
    next_due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    status: Optional[str] = None


class PMResponse(BaseSchema):
    id: int
    title: str
    description: Optional[str] = None
    asset_id: Optional[int] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    frequency: str
    next_due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
