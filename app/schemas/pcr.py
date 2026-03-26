"""ProjectChangeRequest request/response schemas."""
from datetime import datetime
from typing import Optional

from app.schemas.common import BaseSchema


class PCRBase(BaseSchema):
    title: str
    description: str
    impact_analysis: Optional[str] = None
    cost_impact: Optional[float] = None
    schedule_impact_days: Optional[int] = None


class PCRCreate(PCRBase):
    pass


class PCRUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    impact_analysis: Optional[str] = None
    cost_impact: Optional[float] = None
    schedule_impact_days: Optional[int] = None
    status: Optional[str] = None


class PCRReviewRequest(BaseSchema):
    status: str  # approved|rejected


class PCRResponse(PCRBase):
    id: int
    status: str
    submitted_by: Optional[int] = None
    submitted_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
