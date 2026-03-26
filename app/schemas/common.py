"""Shared schema primitives used across the API."""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Root schema class.

    All response/request models inherit from this so that:
    - ORM objects can be passed directly (``from_attributes=True``).
    - JSON keys are camelCase to match the TypeScript frontend.
    - Snake-case field names still work for internal Python use
      (``populate_by_name=True``).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True,
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated wrapper returned by list endpoints."""

    items: List[T]
    total: int
    page: int
    limit: int
    pages: int


class MessageResponse(BaseModel):
    """Simple success/message envelope."""

    message: str
    success: bool = True
