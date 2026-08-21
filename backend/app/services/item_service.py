from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.crud.crud_item import crud_item
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    """Service layer handling business logic for Items."""

    @staticmethod
    def get_items(db: Session, *, skip: int = 0, limit: int = 50) -> List[Item]:
        return crud_item.get_multi(db, skip=skip, limit=limit)

    @staticmethod
    def get_item_by_id(db: Session, *, item_id: int) -> Item:
        item = crud_item.get(db, id=item_id)
        if not item:
            raise NotFoundException(message=f"Item with ID {item_id} does not exist")
        return item

    @staticmethod
    def create_item(db: Session, *, item_in: ItemCreate) -> Item:
        return crud_item.create(db, obj_in=item_in)

    @staticmethod
    def update_item(db: Session, *, item_id: int, item_in: ItemUpdate) -> Item:
        db_item = ItemService.get_item_by_id(db, item_id=item_id)
        return crud_item.update(db, db_obj=db_item, obj_in=item_in)

    @staticmethod
    def delete_item(db: Session, *, item_id: int) -> Item:
        db_item = ItemService.get_item_by_id(db, item_id=item_id)
        return crud_item.remove(db, id=item_id)


item_service = ItemService()
