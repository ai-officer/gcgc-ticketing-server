"""PricingRecord ORM model."""
from sqlalchemy import Column, Date, Integer, Numeric, String, Text

from app.database import Base


class PricingRecord(Base):
    __tablename__ = "pricing_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
