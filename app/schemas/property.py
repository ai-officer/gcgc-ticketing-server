"""Property request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class PropertyBase(BaseSchema):
    name: str
    description: Optional[str] = None
    collection_target: Optional[float] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    collection_target: Optional[float] = None


class PropertyResponse(PropertyBase):
    id: int
