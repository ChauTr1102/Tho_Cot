"""
Pydantic schema describing the requested JSON output structure.
Agno uses this schema (through Agent(output_schema=...)) to make Gemini
return structured output in the correct format instead of free-form text.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- product_brief ----------
class PriceOrPromotion(BaseModel):
    price: Optional[float] = Field(None, description="Current product price as a number")
    currency: str = Field("VND", description="Currency")
    promotion: Optional[str] = Field(None, description="Promotion if available, e.g. '20% off + Free shipping'")


class ProductBrief(BaseModel):
    product_name: str = Field(..., description="Full product name")
    category: str = Field(..., description="Product category")
    key_selling_points: List[str] = Field(default_factory=list, description="Key selling points (USPs)")
    price_or_promotion: PriceOrPromotion
    target_market: str = Field(..., description="Target market, e.g. 'Vietnam - young adults aged 18-30'")
    required_claims: List[str] = Field(default_factory=list, description="Claims required in advertising, e.g. 'dermatologically tested'")
    restricted_or_forbidden_claims: List[str] = Field(default_factory=list, description="Claims restricted or forbidden in advertising, e.g. 'cures acne 100%'")


# ---------- brand_kit ----------
class Logo(BaseModel):
    path: Optional[str] = Field(None, description="Brand logo image URL if found")


class BrandColors(BaseModel):
    primary: Optional[str] = Field(None, description="Primary color (hex if inferable, or a description)")
    secondary: Optional[str] = Field(None, description="Secondary color")
    accent: List[str] = Field(default_factory=list, description="Accent colors")
    palette: List[str] = Field(default_factory=list, description="Overall palette inferred from product images")


class ToneOfVoice(BaseModel):
    description: str = Field("", description="Brief description of the brand voice")
    attributes: List[str] = Field(default_factory=list, description="Tone attributes, e.g. youthful, trustworthy")
    do: List[str] = Field(default_factory=list, description="Things to do when writing content")
    dont: List[str] = Field(default_factory=list, description="Things to avoid when writing content")


class BrandKit(BaseModel):
    logo: Logo
    brand_colors: BrandColors
    tone_of_voice: ToneOfVoice
    product_photos: List[str] = Field(default_factory=list, description="Product image URLs from the page")
    existing_product_visuals: List[str] = Field(default_factory=list, description="Existing advertising banner or visual URLs if available")


# ---------- audience_brief ----------
class AudienceBrief(BaseModel):
    target_customer: str = Field(..., description="Description of the target customer")
    language: str = Field(..., description="Content language, e.g. 'Vietnamese'")
    platform: str = Field(..., description="Sales platform, e.g. 'TikTok Shop'")
    market: str = Field(..., description="Market or country")


# ---------- market_signal ----------
class MarketSignal(BaseModel):
    trend: Optional[str] = Field(None, description="Relevant product trend if inferable")
    seasonal_moment: Optional[str] = Field(None, description="Relevant seasonal moment, e.g. 'Summer'")
    consumer_pain_point: Optional[str] = Field(None, description="Customer pain point or insight addressed by the product")
    search_keyword: List[str] = Field(default_factory=list, description="Relevant search keywords")
    competitor_angle: Optional[str] = Field(None, description="Competitor angle if known")
    campaign_objective: str = Field("", description="Proposed campaign objective, e.g. 'Increase summer sales'")


# ---------- past_campaign_data ----------
class SalesResults(BaseModel):
    units_sold: Optional[int] = None
    revenue: Optional[float] = None
    currency: str = "VND"


class WatchTime(BaseModel):
    value: Optional[float] = None
    unit: str = "seconds"


class PastCampaignData(BaseModel):
    enabled: bool = Field(False, description="True if the page has previous campaign data (usually False because product pages do not)")
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    roas: Optional[float] = None
    watch_time: WatchTime = Field(default_factory=WatchTime)
    add_to_cart_rate: Optional[float] = None
    comments: List[str] = Field(default_factory=list)
    sales_results: SalesResults = Field(default_factory=SalesResults)


# ---------- root ----------
class TikTokShopExtraction(BaseModel):
    product_brief: ProductBrief
    brand_kit: BrandKit
    audience_brief: AudienceBrief
    market_signal: MarketSignal
    past_campaign_data: PastCampaignData
