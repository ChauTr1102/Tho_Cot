from typing import Generator
from fastapi import Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.common import PaginationParams


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_pagination(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
) -> PaginationParams:
    """Dependency that extracts and validates pagination parameters."""
    return PaginationParams(skip=skip, limit=limit)
