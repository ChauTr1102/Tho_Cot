from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Campaign(Base):
    """Persisted campaign and the latest research run attached to it."""

    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)
    research_input: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    research_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

