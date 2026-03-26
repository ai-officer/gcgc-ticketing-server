"""Location ORM model."""
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)

    # Relationships
    property = relationship("Property", back_populates="locations")
    assets = relationship("Asset", back_populates="location")
    inventory_items = relationship("InventoryItem", back_populates="location")
    tickets = relationship("Ticket", back_populates="location")
    pm_schedules = relationship("PreventiveMaintenance", back_populates="location")
