"""ProjectChangeRequest ORM model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectChangeRequest(Base):
    __tablename__ = "project_change_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    impact_analysis = Column(Text, nullable=True)
    cost_impact = Column(Numeric(12, 2), nullable=True)
    schedule_impact_days = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending|approved|rejected

    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    submitter = relationship(
        "User", foreign_keys=[submitted_by_id], back_populates="pcrs_submitted"
    )
    approver = relationship(
        "User", foreign_keys=[approved_by_id], back_populates="pcrs_approved"
    )
