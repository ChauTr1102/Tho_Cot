"""HTTP contracts for the Exa-backed research pipeline."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResearchPrice(StrictModel):
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3)
    unit: str = Field(min_length=1)
    note: str | None = None


class ResearchProductBrief(StrictModel):
    product_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    key_selling_points: list[str] = Field(min_length=1)
    price: ResearchPrice | None
    promotion: str | None
    target_market: list[str] = Field(min_length=1)
    required_claims: list[str]
    restricted_claims: list[str]


class ResearchBrandColor(StrictModel):
    name: str = Field(min_length=1)
    hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    verification_status: Literal["verified", "estimated", "unknown"]


class ResearchBrandKit(StrictModel):
    logo: str = ""
    brand_colors: list[ResearchBrandColor] = Field(min_length=1)
    tone_of_voice: list[str] = Field(min_length=1)
    product_photos: list[str]
    existing_product_visuals: list[str]


class ResearchAudienceBrief(StrictModel):
    target_customer: list[str] = Field(min_length=1)
    languages: list[str] = Field(min_length=1)
    platforms: list[str] = Field(min_length=1)
    markets: list[str] = Field(min_length=1)


CampaignObjective = Literal[
    "awareness", "consideration", "conversion", "retention",
    "engagement", "lead_generation",
]


class ResearchMarketSignal(StrictModel):
    trends: list[str]
    seasonal_moments: list[str]
    consumer_pain_points: list[str]
    search_keywords: list[str]
    competitor_angles: list[str]
    campaign_objectives: list[CampaignObjective] = Field(min_length=1)


class ResearchInput(StrictModel):
    schema_version: Literal["1.0"]
    campaign_id: str = Field(min_length=1)
    product_brief: ResearchProductBrief
    brand_kit: ResearchBrandKit
    audience_brief: ResearchAudienceBrief
    market_signal: ResearchMarketSignal


class ResearchAssetManifest(StrictModel):
    label: str
    source: str
    transport: Literal["remote_url", "base64_data_url"]
    mime_type: str | None = None
    bytes: int | None = None


class ResearchRunResult(StrictModel):
    campaign_id: str
    engine: str
    status: Literal["completed"]
    plan: dict[str, Any]
    sources: list[str]
    research_tool_calls: list[str]
    input_assets: list[ResearchAssetManifest]
