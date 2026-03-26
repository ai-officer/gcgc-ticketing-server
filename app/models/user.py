"""User ORM model."""
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin|technician|requestor|service_desk
    avatar = Column(String(500), nullable=True)
    is_on_duty = Column(Boolean, default=False, nullable=False)

    # Relationships
    tickets_requested = relationship(
        "Ticket", foreign_keys="Ticket.requestor_id", back_populates="requestor"
    )
    tickets_assigned = relationship(
        "Ticket", foreign_keys="Ticket.assignee_id", back_populates="assignee"
    )
    worklogs = relationship("Worklog", back_populates="technician")
    announcements = relationship("Announcement", back_populates="author")
    notifications = relationship("Notification", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    pm_assignments = relationship(
        "PreventiveMaintenance", foreign_keys="PreventiveMaintenance.assigned_to_id",
        back_populates="assignee"
    )
    pcrs_submitted = relationship(
        "ProjectChangeRequest", foreign_keys="ProjectChangeRequest.submitted_by_id",
        back_populates="submitter"
    )
    pcrs_approved = relationship(
        "ProjectChangeRequest", foreign_keys="ProjectChangeRequest.approved_by_id",
        back_populates="approver"
    )
