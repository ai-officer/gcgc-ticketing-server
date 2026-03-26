"""Worklog ORM model with WorklogPart and WorklogPhoto child models."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class WorklogPart(Base):
    __tablename__ = "worklog_parts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worklog_id = Column(Integer, ForeignKey("worklogs.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_id = Column(
        Integer, ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    quantity = Column(Integer, nullable=False, default=1)

    # Relationships
    worklog = relationship("Worklog", back_populates="parts")
    inventory_item = relationship("InventoryItem", back_populates="worklog_parts")


class WorklogPhoto(Base):
    __tablename__ = "worklog_photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worklog_id = Column(Integer, ForeignKey("worklogs.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(500), nullable=False)

    # Relationship
    worklog = relationship("Worklog", back_populates="photos")


class Worklog(Base):
    __tablename__ = "worklogs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    technician_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    activity = Column(Text, nullable=False)
    time_spent_minutes = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="worklogs")
    technician = relationship("User", back_populates="worklogs")
    parts = relationship("WorklogPart", back_populates="worklog", cascade="all, delete-orphan")
    photos = relationship("WorklogPhoto", back_populates="worklog", cascade="all, delete-orphan")
