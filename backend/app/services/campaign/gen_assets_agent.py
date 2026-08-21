"""
MOCK gen_assets agent.

Real implementation would call:
  - Seedream 5.0 Pro (required) -> product images / marketplace visuals
  - Seedance 2.5 (required)     -> short-form video
  - Audio 1.0 (optional)        -> voiceover / subtitles
This mock returns a deterministic, schema-valid AssetBundle covering the
minimum required set (>=4 images, >=1 video, full copy) so the QA agent
can be developed/tested independently. See byteplus_ark.py (repo root)
for the real API call shapes to swap in later.
"""
from __future__ import annotations

from app.schemas.campaign import (
    AssetBundle,
    CampaignInput,
    CampaignPlan,
    CommerceCopy,
    ImageAsset,
    ImageKind,
    VideoAsset,
)


def generate_assets(
    plan: CampaignPlan,
    campaign_input: CampaignInput | None = None,
) -> AssetBundle:
    """Produce the asset bundle for a campaign plan.

    `campaign_input` carries what the plan does not: the brand's real product
    photos (the Brand Lock reference), brand colours, and forbidden claims.
    Without it the studio can only synthesise generic product imagery, so
    callers should always pass it.

    It stays optional, and passing None keeps the deterministic mock below, so
    the QA agent can be developed and tested without a network or an API key.
    """
    campaign_id = plan.campaign_id

    images = [
        ImageAsset(kind=ImageKind.HERO, url=f"mock://{campaign_id}/hero.jpg", width=2048, height=2048),
        ImageAsset(kind=ImageKind.SKU_DETAIL, url=f"mock://{campaign_id}/sku_detail.jpg", width=2048, height=2048),
        ImageAsset(kind=ImageKind.COLLECTION, url=f"mock://{campaign_id}/collection.jpg", width=2048, height=2048),
        ImageAsset(kind=ImageKind.THUMBNAIL, url=f"mock://{campaign_id}/thumbnail.jpg", width=1080, height=1080),
    ]

    videos = [
        VideoAsset(
            url=f"mock://{campaign_id}/route_A.mp4",
            duration_sec=20,
            resolution="720p",
            aspect_ratio="9:16",
            route_id="A",
        ),
    ]

    copy = CommerceCopy(
        product_title="Tiêu đề sản phẩm mẫu",
        product_description="Mô tả sản phẩm mẫu làm nổi bật các điểm bán hàng cốt lõi.",
        listing_bullet_points=["Lợi ích 1", "Lợi ích 2", "Lợi ích 3"],
        ad_caption="Khám phá sự khác biệt ngay hôm nay.",
        promotion_copy="Ưu đãi giới hạn trong tuần ra mắt.",
        short_hook_lines=["Dừng lướt một chút.", "Điều này sẽ thay đổi mọi thứ."],
    )

    return AssetBundle(campaign_id=campaign_id, images=images, videos=videos, listing_copy=copy)
