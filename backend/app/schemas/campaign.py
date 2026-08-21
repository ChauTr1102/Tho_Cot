"""
Shared data contracts between the 3 campaign agents: gen_plan -> gen_assets -> qa_review.

These schemas mirror the "Expected Output" section of BP-01:
  1. Product Positioning
  2. Creative Routes (>=2, for A/B testing)
  3. Short-form Video Asset
  4. Product Collection Image Set (>=4)
  5. Commerce Copy
  6. A/B Testing Plan
  7. Optional Performance Learning

Kept as plain Pydantic models so they serialize directly to/from the
JSON file-system "DB" (no SQLAlchemy models — DB is not deployed for
this feature; see app/storage/campaign_store.py).
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


class Platform(str, Enum):
    """Marketplace a kit is built for.

    Kits differ by more than aspect ratio. TikTok is video-first and the viewer
    is scrolling, so its assets are staged and generated. Shopee is image-first
    and the shopper is comparing before paying, so its assets favour the brand's
    real photographs.
    """
    TIKTOK_SHOP = "tiktok_shop"
    SHOPEE = "shopee"


class AssetOrigin(str, Enum):
    """How an asset was produced.

    REUSE    - an existing brand photo, cropped and resized only. Used where the
               shopper inspects the product and an invented pixel is a liability.
    REMIX    - image-to-image from a real product photo: new scene, added text.
    GENERATE - synthesised, anchored to the product photo and the hero image.
    """
    REUSE = "reuse"
    REMIX = "remix"
    GENERATE = "generate"


class ShotAsset(BaseModel):
    """One shot of a multi-shot video.

    The shot's keyframe carries its on-screen text: Seedream renders Vietnamese
    correctly and that text survives image-to-video intact, whereas Seedance
    garbles Vietnamese captions.
    """
    index: int
    role: str  # hook | product | benefit | cta
    keyframe_path: str
    clip_path: Optional[str] = None
    duration_sec: float = 5.0
    onscreen_text: str = ""
    vo_text: str = ""
    used_fallback: bool = False  # clip missed its deadline; a Ken Burns move
                                 # over the keyframe was used so the shot still exists


class VideoCutdown(BaseModel):
    """A derived cut of the master video - shorter, or a different aspect ratio."""
    label: str  # "15s" | "1x1" | ...
    local_path: str
    duration_sec: float
    aspect_ratio: str


class ImageAsset(BaseModel):
    kind: ImageKind
    url: str
    width: int
    height: int
    model: str = "dola-seedream-5-0-pro-260628"

    # --- studio extensions -------------------------------------------
    # All optional with defaults: qa_review_agent and the existing tests
    # construct ImageAsset with the five fields above and must keep working.
    platform: Optional[Platform] = None
    slot: Optional[str] = None
    origin: Optional[AssetOrigin] = None
    local_path: Optional[str] = None
    prompt: Optional[str] = None
    text_rendered: list[str] = Field(default_factory=list)
    source_photo: Optional[str] = None
    qa_passed: Optional[bool] = None
    qa_notes: list[str] = Field(default_factory=list)
    gen_seconds: Optional[float] = None


class VideoAsset(BaseModel):
    url: str
    duration_sec: float
    resolution: str  # e.g. "720p"
    aspect_ratio: str  # e.g. "9:16"
    model: str = "dreamina-seedance-2-5-260628"
    route_id: Optional[str] = None

    # --- studio extensions -------------------------------------------
    platform: Optional[Platform] = None
    local_path: Optional[str] = None
    shots: list[ShotAsset] = Field(default_factory=list)
    has_voiceover: bool = False
    cutdowns: list[VideoCutdown] = Field(default_factory=list)


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
