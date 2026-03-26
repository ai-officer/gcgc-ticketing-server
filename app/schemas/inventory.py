"""InventoryItem request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class InventoryItemBase(BaseSchema):
    name: str
    sku: str
    category: str
    quantity: int = 0
    min_quantity: int = 0
    unit_cost: float = 0.0
    location_id: Optional[int] = None
    property_id: Optional[int] = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseSchema):
    name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    min_quantity: Optional[int] = None
    unit_cost: Optional[float] = None
    location_id: Optional[int] = None
    property_id: Optional[int] = None


class InventoryItemResponse(InventoryItemBase):
    id: int


class AdjustQuantityRequest(BaseSchema):
    delta: int  # positive = add stock, negative = remove stock
    reason: Optional[str] = None
