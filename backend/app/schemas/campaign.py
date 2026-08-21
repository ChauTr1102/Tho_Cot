from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


CampaignStatus = Literal["draft", "researching", "researched", "failed"]


class CampaignCreate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: CampaignStatus | None = None


class CampaignOut(BaseModel):
    id: str
    name: str
    description: str | None
    status: CampaignStatus
    research_input: dict[str, Any] | None
    research_result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignListItem(BaseModel):
    id: str
    name: str
    description: str | None
    status: CampaignStatus
    has_research_result: bool
    created_at: datetime
    updated_at: datetime

