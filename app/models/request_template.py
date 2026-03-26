"""RequestTemplate ORM model."""
from sqlalchemy import Column, Integer, String, Text

from app.database import Base


class RequestTemplate(Base):
    __tablename__ = "request_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    priority = Column(String(50), nullable=False)  # low|medium|high|critical
    description = Column(Text, nullable=True)
