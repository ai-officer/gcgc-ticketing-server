"""Ticket ORM model with related TicketTask and TicketRating child models."""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class TicketTask(Base):
    __tablename__ = "ticket_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Relationship back to parent ticket
    ticket = relationship("Ticket", back_populates="tasks")


class TicketRating(Base):
    __tablename__ = "ticket_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    score = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=True)

    # Relationship back to parent ticket
    ticket = relationship("Ticket", back_populates="rating")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=False)
    priority = Column(String(50), nullable=False)  # low|medium|high|critical
    status = Column(String(50), nullable=False, default="open")  # open|assigned|in-progress|resolved|closed

    # People
    requestor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)

    # Location context
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    room_number = Column(String(50), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)

    # Financials
    cost = Column(Numeric(10, 2), nullable=True, default=0)
    revenue = Column(Numeric(10, 2), nullable=True, default=0)
    vendor_cost = Column(Numeric(10, 2), nullable=True)

    # SLA
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    response_sla_deadline = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    escalated = Column(Boolean, default=False, nullable=False)

    # Flags
    parts_deducted = Column(Boolean, default=False, nullable=False)

    # Preventive maintenance link (for deduplication)
    source_pm_id = Column(
        Integer, ForeignKey("preventive_maintenances.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    requestor = relationship("User", foreign_keys=[requestor_id], back_populates="tickets_requested")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="tickets_assigned")
    vendor = relationship("Vendor", back_populates="tickets")
    property = relationship("Property", back_populates="tickets")
    location = relationship("Location", back_populates="tickets")
    asset = relationship("Asset", back_populates="tickets")
    tasks = relationship("TicketTask", back_populates="ticket", cascade="all, delete-orphan")
    rating = relationship(
        "TicketRating", back_populates="ticket", uselist=False, cascade="all, delete-orphan"
    )
    worklogs = relationship("Worklog", back_populates="ticket", cascade="all, delete-orphan")
    source_pm = relationship(
        "PreventiveMaintenance", foreign_keys=[source_pm_id], back_populates="generated_tickets"
    )
