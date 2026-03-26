"""IncidentType ORM model."""
from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class IncidentType(Base):
    __tablename__ = "incident_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    sla_hours = Column(Integer, nullable=False)
    response_sla_hours = Column(Integer, nullable=False)
    resolution_sla_hours = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    business_hours_only = Column(Boolean, default=False, nullable=False)
    escalation_level = Column(Integer, nullable=True)
