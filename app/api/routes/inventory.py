"""Inventory CRUD routes."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.inventory_item import InventoryItem
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import (
    AdjustQuantityRequest,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=PaginatedResponse[InventoryItemResponse])
async def list_inventory(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    property_id: Optional[int] = Query(default=None),
    location_id: Optional[int] = Query(default=None),
    category: Optional[str] = Query(default=None),
    low_stock: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List inventory items. Set low_stock=true to see items below min_quantity."""
    count_q = select(func.count(InventoryItem.id))
    query = select(InventoryItem)

    filters = []
    if property_id:
        filters.append(InventoryItem.property_id == property_id)
    if location_id:
        filters.append(InventoryItem.location_id == location_id)
    if category:
        filters.append(InventoryItem.category == category)
    if low_stock is True:
        filters.append(InventoryItem.quantity <= InventoryItem.min_quantity)
    if search:
        filters.append(InventoryItem.name.ilike(f"%{search}%"))

    for f in filters:
        count_q = count_q.where(f)
        query = query.where(f)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(query.offset((page - 1) * limit).limit(limit))
    items = result.scalars().all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    payload: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    return item


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    payload: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin", "technician")),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    await db.delete(item)
    await db.commit()


@router.post("/{item_id}/adjust", response_model=InventoryItemResponse)
async def adjust_quantity(
    item_id: int,
    payload: AdjustQuantityRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin", "technician")),
):
    """Adjust inventory quantity by a signed delta value."""
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")

    item.quantity = max(0, item.quantity + payload.delta)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item
