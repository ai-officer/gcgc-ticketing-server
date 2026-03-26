"""Vendor request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class VendorBase(BaseSchema):
    name: str
    contact_name: str
    email: str
    phone: str
    specialty: str
    contract_status: str
    sla_hours: int = 24


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseSchema):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    contract_status: Optional[str] = None
    sla_hours: Optional[int] = None


class VendorResponse(VendorBase):
    id: int
