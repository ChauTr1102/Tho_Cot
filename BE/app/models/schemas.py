"""
Shared data contracts between the 3 agents: gen_plan -> gen_assets -> qa_review.

These schemas mirror the "Expected Output" section of BP-01:
  1. Product Positioning
  2. Creative Routes (>=2, for A/B testing)
  3. Short-form Video Asset
  4. Product Collection Image Set (>=4)
  5. Commerce Copy
  6. A/B Testing Plan
  7. Optional Performance Learning

Kept as plain Pydantic models so they serialize directly to/from the
JSON file-system "DB".
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Input briefs
# ---------------------------------------------------------------------------

class ProductBrief(BaseModel):
    product_name: str
    category: str
    key_selling_points: list[str] = Field(default_factory=list)
    price_or_promotion: Optional[str] = None
    target_market: str
    required_claims: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)


class BrandKit(BaseModel):
    logo_url: Optional[str] = None
    brand_colors: list[str] = Field(default_factory=list)
    tone_of_voice: Optional[str] = None
    product_photo_urls: list[str] = Field(default_factory=list)


class AudienceBrief(BaseModel):
    target_customer: str
    language: str
    platform: list[str] = Field(default_factory=list)
    market: str


class MarketSignal(BaseModel):
    trend: Optional[str] = None
    seasonal_moment: Optional[str] = None
    consumer_pain_point: Optional[str] = None
    search_keyword: Optional[str] = None
    competitor_angle: Optional[str] = None
    campaign_objective: Optional[str] = None
    sources: list[str] = Field(default_factory=list)  # citations backing the signal


class PastCampaignData(BaseModel):
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    roas: Optional[float] = None
    watch_time_sec: Optional[float] = None
    add_to_cart_rate: Optional[float] = None
    comments: list[str] = Field(default_factory=list)
    sales_results: Optional[str] = None


class CampaignInput(BaseModel):
    campaign_id: str
    product_brief: ProductBrief
    brand_kit: BrandKit
    audience_brief: AudienceBrief
    market_signal: MarketSignal
    past_campaign_data: Optional[PastCampaignData] = None


# ---------------------------------------------------------------------------
# Gen-plan agent output
# ---------------------------------------------------------------------------

class CreativeRoute(BaseModel):
    route_id: str  # "A" / "B" / ...
    hook_idea: str
    visual_direction: str
    message_angle: str
    suggested_platform_usage: list[str] = Field(default_factory=list)


class ProductPositioning(BaseModel):
    main_campaign_angle: str
    target_audience: str
    key_selling_message: str
    product_benefit_hierarchy: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)  # market research citations


class ABTestPlan(BaseModel):
    what_to_test: str
    route_a: str
    route_b: str
    success_metrics: list[str] = Field(default_factory=list)
    expected_learning: str


class PerformanceLearning(BaseModel):
    keep: list[str] = Field(default_factory=list)
    change: list[str] = Field(default_factory=list)
    stop: list[str] = Field(default_factory=list)
    test_next: list[str] = Field(default_factory=list)


class CampaignPlan(BaseModel):
    campaign_id: str
    positioning: ProductPositioning
    creative_routes: list[CreativeRoute]
    ab_test_plan: ABTestPlan
    performance_learning: Optional[PerformanceLearning] = None
    generated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Gen-assets agent output
# ---------------------------------------------------------------------------

class ImageKind(str, Enum):
    HERO = "product_hero_image"
    SKU_DETAIL = "sku_detail_image"
    COLLECTION = "campaign_collection_image"
    THUMBNAIL = "marketplace_thumbnail"
    BANNER = "promotion_banner"
    BUNDLE = "bundle_image"
    SEASONAL = "seasonal_sale_image"


class ImageAsset(BaseModel):
    kind: ImageKind
    url: str
    width: int
    height: int
    model: str = "dola-seedream-5-0-pro-260628"


class VideoAsset(BaseModel):
    url: str
    duration_sec: float
    resolution: str  # e.g. "720p"
    aspect_ratio: str  # e.g. "9:16"
    model: str = "dreamina-seedance-2-5-260628"
    route_id: Optional[str] = None


class CommerceCopy(BaseModel):
    product_title: str
    product_description: str
    listing_bullet_points: list[str] = Field(default_factory=list)
    ad_caption: str
    promotion_copy: Optional[str] = None
    short_hook_lines: list[str] = Field(default_factory=list)


class AssetBundle(BaseModel):
    campaign_id: str
    images: list[ImageAsset]
    videos: list[VideoAsset]
    listing_copy: CommerceCopy
    generated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# QA review agent output
# ---------------------------------------------------------------------------

class QASeverity(str, Enum):
    BLOCKER = "blocker"     # must fix, fails QA
    WARNING = "warning"     # flagged but non-blocking
    INFO = "info"


class QAIssue(BaseModel):
    rule_id: str
    severity: QASeverity
    message: str
    field: Optional[str] = None  # dotted path to the offending field, if applicable


class QAResult(BaseModel):
    campaign_id: str
    passed: bool
    iteration: int
    issues: list[QAIssue] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=_utcnow)
