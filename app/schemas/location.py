"""Location request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class LocationBase(BaseSchema):
    property_id: int
    name: str
    address: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseSchema):
    property_id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None


class LocationResponse(LocationBase):
    id: int
