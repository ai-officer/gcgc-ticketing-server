"""IncidentType request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class IncidentTypeBase(BaseSchema):
    name: str
    sla_hours: int
    response_sla_hours: int
    resolution_sla_hours: int
    description: Optional[str] = None
    business_hours_only: Optional[bool] = False
    escalation_level: Optional[int] = None


class IncidentTypeCreate(IncidentTypeBase):
    pass


class IncidentTypeUpdate(BaseSchema):
    name: Optional[str] = None
    sla_hours: Optional[int] = None
    response_sla_hours: Optional[int] = None
    resolution_sla_hours: Optional[int] = None
    description: Optional[str] = None
    business_hours_only: Optional[bool] = None
    escalation_level: Optional[int] = None


class IncidentTypeResponse(IncidentTypeBase):
    id: int
