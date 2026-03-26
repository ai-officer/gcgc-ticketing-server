"""Property ORM model."""
from sqlalchemy import Column, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    collection_target = Column(Numeric(12, 2), nullable=True)

    # Relationships
    locations = relationship("Location", back_populates="property")
    assets = relationship("Asset", back_populates="property")
    inventory_items = relationship("InventoryItem", back_populates="property")
    tickets = relationship("Ticket", back_populates="property")
    pm_schedules = relationship("PreventiveMaintenance", back_populates="property")
