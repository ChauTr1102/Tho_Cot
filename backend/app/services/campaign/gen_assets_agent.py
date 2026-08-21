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
    CampaignPlan,
    CommerceCopy,
    ImageAsset,
    ImageKind,
    VideoAsset,
)


def generate_assets(plan: CampaignPlan) -> AssetBundle:
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
        product_title="Sample Product Title",
        product_description="Sample product description highlighting key selling points.",
        listing_bullet_points=["Benefit 1", "Benefit 2", "Benefit 3"],
        ad_caption="Discover the difference today.",
        promotion_copy="Launch week only: limited offer.",
        short_hook_lines=["Stop scrolling.", "This changes everything."],
    )

    return AssetBundle(campaign_id=campaign_id, images=images, videos=videos, listing_copy=copy)
