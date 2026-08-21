from typing import List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    """Specific CRUD operations for Item model."""

    def get_by_completed(self, db: Session, *, is_completed: bool) -> List[Item]:
        return db.query(self.model).filter(self.model.is_completed == is_completed).all()


crud_item = CRUDItem(Item)
