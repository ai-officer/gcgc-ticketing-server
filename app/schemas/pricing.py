"""PricingRecord request/response schemas."""
from datetime import date
from typing import Optional

from app.schemas.common import BaseSchema


class PricingRecordBase(BaseSchema):
    service_name: str
    category: str
    price: float
    effective_date: date
    notes: Optional[str] = None


class PricingRecordCreate(PricingRecordBase):
    pass


class PricingRecordUpdate(BaseSchema):
    service_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    effective_date: Optional[date] = None
    notes: Optional[str] = None


class PricingRecordResponse(PricingRecordBase):
    id: int
