"""Asset ORM model."""
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active|maintenance|retired
    purchase_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    last_maintenance = Column(Date, nullable=True)
    next_maintenance = Column(Date, nullable=True)
    serial_number = Column(String(255), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)

    # Relationships
    property = relationship("Property", back_populates="assets")
    location = relationship("Location", back_populates="assets")
    tickets = relationship("Ticket", back_populates="asset")
    pm_schedules = relationship("PreventiveMaintenance", back_populates="asset")
