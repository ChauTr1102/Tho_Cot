"""
Shared fixtures for the studio test suite.

Several agents own different parts of this file. **Append, never rewrite.**

The brief and plan fixtures below are the real COSRX Advanced Snail 96 campaign
from `sample_data/01_cosrx_snail_essence` - a real brand, a real 11.11
promotion, real forbidden claims, and real past-campaign numbers in which the
testimonial/UGC route beat the science-led route on every metric. Testing the
studio against invented data would hide exactly the problems it exists to catch.

Route A's hook deliberately carries a forbidden claim ("trắng da vĩnh viễn").
That is not a mistake in the fixture: a planning agent can write a
non-compliant hook, and the worksheet has to drop it before it reaches a
listing image.

The inventory fixtures are built here rather than imported from
`app.services.studio.inventory` on purpose, so these tests keep passing while
that module is being changed by whoever owns it. They are structurally the same
shape: `.photos[*].path/.width/.height/.tags/.eligible_slots` and `.by_slot`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from app.schemas.campaign import (
    ABTestPlan,
    AudienceBrief,
    BrandKit,
    CampaignInput,
    CampaignPlan,
    CreativeRoute,
    MarketSignal,
    PerformanceLearning,
    ProductBrief,
    ProductPositioning,
)

# repo root: backend/tests/studio/conftest.py -> Tho_Cot/
REPO_ROOT = Path(__file__).resolve().parents[3]
COSRX_ASSETS = REPO_ROOT / "sample_data" / "01_cosrx_snail_essence" / "assets"


# ---------------------------------------------------------------------------
# Inventory stand-ins (shaped like app.services.studio.inventory)
# ---------------------------------------------------------------------------

@dataclass
class FakePhotoFacts:
    """The fields of `inventory.PhotoFacts` that the worksheet actually reads."""

    path: str
    width: int = 1200
    height: int = 1200
    aspect: float = 1.0
    bg_whiteness: float = 0.95
    sharpness: float = 12.0
    tags: list[str] = field(default_factory=list)
    eligible_slots: list[str] = field(default_factory=list)


@dataclass
class FakeInventorySheet:
    """The fields of `inventory.InventorySheet` that the worksheet actually reads."""

    photos: list[FakePhotoFacts] = field(default_factory=list)
    by_slot: dict[str, list[str]] = field(default_factory=dict)
    video_refs: list[str] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The COSRX brief and plan
# ---------------------------------------------------------------------------

def build_sample_input() -> CampaignInput:
    """The COSRX Advanced Snail 96 brief, as `sample_data/01_...` states it."""
    return CampaignInput(
        campaign_id="01_cosrx_snail_essence",
        product_brief=ProductBrief(
            product_name="COSRX Advanced Snail 96 Mucin Power Essence (100ml)",
            category="Skincare / Facial Essence",
            key_selling_points=[
                "96% Snail Secretion Filtrate phục hồi hàng rào da",
                "Cấp ẩm sâu, cho làn da căng bóng glass skin",
                "Kết cấu mỏng nhẹ, thẩm thấu nhanh, không nhờn rít",
                "Đã kiểm nghiệm lâm sàng tại Hàn Quốc",
            ],
            price_or_promotion="11.11: giảm 25% còn 290.000đ + freeship",
            target_market="Việt Nam (mở rộng SEA)",
            required_claims=[
                "96% snail mucin",
                "đã kiểm nghiệm lâm sàng",
                "phục hồi hàng rào da",
            ],
            forbidden_claims=["trị mụn dứt điểm", "trắng da vĩnh viễn"],
        ),
        brand_kit=BrandKit(
            logo_url=str(COSRX_ASSETS / "logo.png"),
            brand_colors=["#FFFFFF", "#1A1A1A", "#00A19A"],
            tone_of_voice="Sạch sẽ, khoa học, đáng tin, tối giản (clean / science-led)",
            product_photo_urls=[
                str(COSRX_ASSETS / "product_01.jpg"),
                str(COSRX_ASSETS / "product_02.jpg"),
            ],
        ),
        audience_brief=AudienceBrief(
            target_customer="Nữ 18-30, da nhạy cảm / sau mụn, mê skincare Hàn",
            language="Tiếng Việt",
            platform=["TikTok Shop", "Shopee"],
            market="Vietnam / SEA",
        ),
        market_signal=MarketSignal(
            trend="Glass skin, skin-barrier repair, snail mucin viral trên TikTok",
            seasonal_moment="Sale 11.11",
            consumer_pain_point="Da xỉn màu, khô, mất nước, dễ kích ứng",
            search_keyword="snail mucin · tinh chất ốc sên · phục hồi da",
            competitor_angle="Some By Mi, SKIN1004 Centella, Anua Heartleaf",
            campaign_objective="Conversion (purchase)",
        ),
    )


def build_sample_plan() -> CampaignPlan:
    """A plan of the shape the upstream agent produces for the COSRX brief.

    `performance_learning.keep` carries the finding from `past_campaign.xlsx`:
    the testimonial/UGC route returned CTR 2.4% and ROAS 4.3 against the
    science-led route's 0.9% and 2.1. The studio is expected to read that and
    let the proven look lead route A.
    """
    return CampaignPlan(
        campaign_id="01_cosrx_snail_essence",
        positioning=ProductPositioning(
            main_campaign_angle="Phục hồi hàng rào da cho da khô, xỉn màu sau mụn",
            target_audience="Nữ 18-30, da nhạy cảm, đang tìm cách phục hồi da",
            key_selling_message="96% tinh chất ốc sên phục hồi hàng rào da",
            product_benefit_hierarchy=[
                "Phục hồi hàng rào da",
                "Cấp ẩm sâu, da căng bóng",
                "Thẩm thấu nhanh, không nhờn rít",
            ],
        ),
        creative_routes=[
            CreativeRoute(
                route_id="A",
                # Non-compliant on purpose: "trắng da vĩnh viễn" is a forbidden
                # claim in the brief, and this string must never reach a frame.
                hook_idea="Trắng da vĩnh viễn chỉ sau 2 tuần dùng tinh chất ốc sên",
                visual_direction="UGC, quay tại nhà, ánh sáng tự nhiên",
                message_angle="testimonial",
                suggested_platform_usage=["TikTok Shop"],
            ),
            CreativeRoute(
                route_id="B",
                hook_idea="Da khô căng, xỉn màu? Hàng rào da đang kêu cứu",
                visual_direction="Studio sạch, nền trắng, cận cảnh texture",
                message_angle="science_led",
                suggested_platform_usage=["Shopee"],
            ),
        ],
        ab_test_plan=ABTestPlan(
            what_to_test="Hook UGC vs hook khoa học",
            route_a="testimonial_ugc",
            route_b="science_led",
            success_metrics=["CTR", "CVR", "ROAS"],
            expected_learning="Hook nào giữ chân người xem lâu hơn 3 giây đầu",
        ),
        performance_learning=PerformanceLearning(
            keep=[
                "Giữ route testimonial_ugc: CTR 2.4% và ROAS 4.3 vượt xa science_led",
                "Giữ before_after làm route thứ hai: ROAS 3.8",
            ],
            change=["Đổi hook nặng khoa học sang lời kể của người dùng"],
            stop=["Dừng route science_led thuần số liệu"],
            test_next=["Thử góc UGC quay tại phòng tắm"],
        ),
    )


@pytest.fixture
def sample_input() -> CampaignInput:
    """The COSRX brief, including its two forbidden claims."""
    return build_sample_input()


@pytest.fixture
def sample_plan() -> CampaignPlan:
    """The COSRX plan, including the past-campaign learning."""
    return build_sample_plan()


@pytest.fixture
def rich_sheet() -> FakeInventorySheet:
    """A brand whose kho can fill the slots that want a real photograph."""
    photos = [
        FakePhotoFacts(
            path=str(COSRX_ASSETS / "product_01.jpg"),
            width=800,
            height=1067,
            aspect=0.75,
            eligible_slots=["shopee_main", "shopee_sku", "tiktok_product"],
        ),
        FakePhotoFacts(
            path=str(COSRX_ASSETS / "product_02.jpg"),
            width=800,
            height=1067,
            aspect=0.75,
            eligible_slots=["shopee_sku", "tiktok_product"],
        ),
    ]
    return FakeInventorySheet(
        photos=photos,
        by_slot={
            "shopee_main": [photos[0].path],
            "shopee_sku": [photos[0].path, photos[1].path],
            "tiktok_product": [photos[0].path, photos[1].path],
        },
        video_refs=[photo.path for photo in photos],
    )


@pytest.fixture
def empty_sheet() -> FakeInventorySheet:
    """A brand that turned up with nothing the inventory could use."""
    return FakeInventorySheet(photos=[], by_slot={})


@pytest.fixture
def bare_input(sample_input: CampaignInput) -> CampaignInput:
    """The COSRX brief stripped of every product photograph.

    The worst case the studio has to survive: no kho at all, so there is no
    Brand Lock reference and every slot has to be generated from words.
    """
    return sample_input.model_copy(
        update={"brand_kit": sample_input.brand_kit.model_copy(update={"product_photo_urls": []})}
    )
