"""Ticket request/response schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import field_validator

from app.schemas.common import BaseSchema


class TaskSchema(BaseSchema):
    id: Optional[int] = None
    description: str
    is_completed: bool = False


class RatingSchema(BaseSchema):
    score: int
    feedback: Optional[str] = None


class TicketCreate(BaseSchema):
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    requestor_id: Optional[int] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    room_number: Optional[str] = None
    asset_id: Optional[int] = None
    cost: Optional[float] = None
    tasks: Optional[List[TaskSchema]] = None


class TicketUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    vendor_id: Optional[int] = None
    vendor_cost: Optional[float] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    room_number: Optional[str] = None
    asset_id: Optional[int] = None
    cost: Optional[float] = None
    revenue: Optional[float] = None
    escalated: Optional[bool] = None
    parts_deducted: Optional[bool] = None


class TicketStatusRequest(BaseSchema):
    status: str


class TicketAssignRequest(BaseSchema):
    assignee_id: int


class TicketRateRequest(BaseSchema):
    score: int
    feedback: Optional[str] = None


class TicketResponse(BaseSchema):
    id: str  # "TKT-XXXX" format
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    status: str
    requestor_id: Optional[int] = None
    assignee_id: Optional[int] = None
    vendor_id: Optional[int] = None
    vendor_cost: Optional[float] = None
    property_id: Optional[int] = None
    location_id: Optional[int] = None
    room_number: Optional[str] = None
    asset_id: Optional[int] = None
    cost: Optional[float] = None
    revenue: Optional[float] = None
    escalated: Optional[bool] = False
    parts_deducted: Optional[bool] = False
    source_pm_id: Optional[int] = None
    sla_deadline: Optional[datetime] = None
    response_sla_deadline: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    tasks: Optional[List[TaskSchema]] = None
    rating: Optional[RatingSchema] = None

    @field_validator("id", mode="before")
    @classmethod
    def format_id(cls, v) -> str:
        """Convert integer PK to 'TKT-XXXX' string for the frontend."""
        if isinstance(v, int):
            return f"TKT-{v:04d}"
        return str(v)
