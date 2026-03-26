"""ServiceCategory request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class CategoryBase(BaseSchema):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
