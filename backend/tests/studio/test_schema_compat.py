"""The studio extends teammate-owned schemas. Extensions must never break
existing consumers: every new field is optional with a default, and the old
call shape must keep working."""
import inspect

from app.schemas.campaign import AssetOrigin, ImageAsset, ImageKind, Platform
from app.services.campaign import gen_assets_agent


def test_old_imageasset_construction_still_works():
    """qa_review_agent builds and reads ImageAsset with only the original fields."""
    a = ImageAsset(kind=ImageKind.HERO, url="mock://x/hero.jpg", width=2048, height=2048)
    assert a.platform is None
    assert a.origin is None
    assert a.text_rendered == []


def test_generate_assets_accepts_campaign_input_and_stays_optional():
    sig = inspect.signature(gen_assets_agent.generate_assets)
    assert list(sig.parameters) == ["plan", "campaign_input"]
    assert sig.parameters["campaign_input"].default is None


def test_platform_and_origin_values():
    assert Platform.TIKTOK_SHOP.value == "tiktok_shop"
    assert Platform.SHOPEE.value == "shopee"
    assert {o.value for o in AssetOrigin} == {"reuse", "remix", "generate"}
