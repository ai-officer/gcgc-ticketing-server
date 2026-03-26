"""PreventiveMaintenance ORM model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class PreventiveMaintenance(Base):
    __tablename__ = "preventive_maintenances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    frequency = Column(String(50), nullable=False)  # daily|weekly|monthly|quarterly|biannually|annually
    next_due_date = Column(DateTime(timezone=True), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active|paused
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    asset = relationship("Asset", back_populates="pm_schedules")
    property = relationship("Property", back_populates="pm_schedules")
    location = relationship("Location", back_populates="pm_schedules")
    assignee = relationship(
        "User", foreign_keys=[assigned_to_id], back_populates="pm_assignments"
    )
    generated_tickets = relationship(
        "Ticket", foreign_keys="Ticket.source_pm_id", back_populates="source_pm"
    )
