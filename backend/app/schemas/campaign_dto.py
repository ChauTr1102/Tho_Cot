from typing import List, Optional
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# INPUT DTO (Updated JSON Format)
# ---------------------------------------------------------

class PriceOrPromotion(BaseModel):
    price: Optional[float] = None
    currency: str = "VND"
    promotion: Optional[str] = None

class ProductBrief(BaseModel):
    product_name: str
    category: str
    key_selling_points: List[str]
    price_or_promotion: PriceOrPromotion
    target_market: str
    required_claims: List[str]
    restricted_or_forbidden_claims: List[str]

class Logo(BaseModel):
    path: Optional[str] = None

class BrandColors(BaseModel):
    primary: Optional[str] = None
    secondary: Optional[str] = None
    accent: List[str]
    palette: List[str]

class ToneOfVoice(BaseModel):
    description: str
    attributes: List[str]
    do: List[str]
    dont: List[str]

class BrandKit(BaseModel):
    logo: Logo
    brand_colors: BrandColors
    tone_of_voice: ToneOfVoice
    product_photos: List[str]
    existing_product_visuals: List[str]

class AudienceBrief(BaseModel):
    target_customer: str
    language: str
    platform: str
    market: str

class MarketSignal(BaseModel):
    trend: Optional[str] = None
    seasonal_moment: Optional[str] = None
    consumer_pain_point: Optional[str] = None
    search_keyword: List[str]
    competitor_angle: Optional[str] = None
    campaign_objective: str

class WatchTime(BaseModel):
    value: Optional[float] = None
    unit: str = "seconds"

class SalesResults(BaseModel):
    units_sold: Optional[int] = None
    revenue: Optional[float] = None
    currency: str = "VND"

class PastCampaignData(BaseModel):
    enabled: bool = False
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    roas: Optional[float] = None
    watch_time: WatchTime
    add_to_cart_rate: Optional[float] = None
    comments: List[str]
    sales_results: SalesResults

class CampaignInputDTO(BaseModel):
    product_brief: ProductBrief
    brand_kit: BrandKit
    audience_brief: AudienceBrief
    market_signal: MarketSignal
    past_campaign_data: PastCampaignData

# ---------------------------------------------------------
# OUTPUT DTO
# ---------------------------------------------------------

class ProductPositioning(BaseModel):
    main_campaign_angle: str
    target_audience: str
    key_selling_message: str
    product_benefit_hierarchy: List[str]

class CreativeRoute(BaseModel):
    name: str
    hook_idea: str
    visual_direction: str
    message_angle: str
    suggested_platform_usage: List[str]

class ShortFormVideoAsset(BaseModel):
    generated_video_urls: List[str]
    format: str = "9:16"
    duration: str = "15-30s"
    additional_cuts: List[str] = Field(default_factory=list)

class ProductCollectionImageSet(BaseModel):
    product_hero_image: str
    sku_detail_image: str
    campaign_collection_image: str
    marketplace_thumbnail: str
    promotion_banner: Optional[str] = None
    bundle_image: Optional[str] = None
    seasonal_sale_image: Optional[str] = None

class CommerceCopy(BaseModel):
    product_title: str
    product_description: str
    listing_bullet_points: List[str]
    ad_caption: str
    promotion_copy: str
    short_hook_lines: List[str]

class ABTestingPlan(BaseModel):
    what_to_test: str
    route_a_description: str
    route_b_description: str
    suggested_success_metrics: List[str]
    expected_learning: str

class PerformanceLearning(BaseModel):
    what_to_keep: List[str]
    what_to_change: List[str]
    what_to_stop: List[str]
    what_to_test_next: List[str]

class CampaignOutputDTO(BaseModel):
    product_positioning: ProductPositioning
    creative_routes: List[CreativeRoute]
    short_form_video_asset: ShortFormVideoAsset
    product_collection_image_set: ProductCollectionImageSet
    commerce_copy: CommerceCopy
    ab_testing_plan: ABTestingPlan
    performance_learning: Optional[PerformanceLearning] = None
