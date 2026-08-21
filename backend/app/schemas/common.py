from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StandardResponse(BaseModel, Generic[T]):
    """Unified JSON API response envelope."""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None
    error: Optional[Any] = None
    timestamp: datetime = Field(default_factory=utc_now)


class PaginationParams(BaseModel):
    """Common pagination query parameters."""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of records to return")
