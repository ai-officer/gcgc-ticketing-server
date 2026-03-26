"""Asset request/response schemas."""
from datetime import date
from typing import Optional

from app.schemas.common import BaseSchema


class AssetBase(BaseSchema):
    name: str
    category: str
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    status: str = "active"
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseSchema):
    name: Optional[str] = None
    category: Optional[str] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AssetResponse(AssetBase):
    id: int
