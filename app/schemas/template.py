"""RequestTemplate request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class TemplateBase(BaseSchema):
    name: str
    category: str
    priority: str
    description: Optional[str] = None


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseSchema):
    name: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None


class TemplateResponse(TemplateBase):
    id: int
