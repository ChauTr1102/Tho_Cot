from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_pagination
from app.schemas.common import PaginationParams, StandardResponse
from app.schemas.item import ItemCreate, ItemOut, ItemUpdate
from app.services.item_service import item_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[ItemOut]])
def list_items(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
):
    """Retrieve items list with pagination."""
    items = item_service.get_items(db, skip=pagination.skip, limit=pagination.limit)
    return StandardResponse(
        success=True,
        message=f"Retrieved {len(items)} items",
        data=items,
    )


@router.get("/{item_id}", response_model=StandardResponse[ItemOut])
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a specific item by ID."""
    item = item_service.get_item_by_id(db, item_id=item_id)
    return StandardResponse(
        success=True,
        message="Item found",
        data=item,
    )


@router.post("", response_model=StandardResponse[ItemOut], status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
):
    """Create a new item."""
    new_item = item_service.create_item(db, item_in=payload)
    return StandardResponse(
        success=True,
        message="Item created successfully",
        data=new_item,
    )


@router.patch("/{item_id}", response_model=StandardResponse[ItemOut])
def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing item."""
    updated_item = item_service.update_item(db, item_id=item_id, item_in=payload)
    return StandardResponse(
        success=True,
        message="Item updated successfully",
        data=updated_item,
    )


@router.delete("/{item_id}", response_model=StandardResponse[dict])
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Delete an item by ID."""
    item_service.delete_item(db, item_id=item_id)
    return StandardResponse(
        success=True,
        message="Item deleted successfully",
        data={"id": item_id},
    )
