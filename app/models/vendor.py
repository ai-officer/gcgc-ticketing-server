"""Vendor ORM model."""
from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    specialty = Column(String(255), nullable=False)
    contract_status = Column(String(50), nullable=False)  # active|expired|pending
    sla_hours = Column(Integer, nullable=False, default=24)

    # Relationships
    tickets = relationship("Ticket", back_populates="vendor")
