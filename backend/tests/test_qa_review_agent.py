"""Unit tests for the QA review agent — the main deliverable of this project."""
from __future__ import annotations

from app.schemas.campaign import (
    AudienceBrief,
    BrandKit,
    CampaignInput,
    MarketSignal,
    ProductBrief,
)
from app.services.campaign import gen_assets_agent, gen_plan_agent, qa_review_agent


def make_input(**overrides) -> CampaignInput:
    base = dict(
        campaign_id="camp-test-1",
        product_brief=ProductBrief(
            product_name="Ruby Serum",
            category="Skincare",
            key_selling_points=["Brightens skin", "Fast absorbing"],
            target_market="Vietnam",
            required_claims=[],
            forbidden_claims=[],
        ),
        brand_kit=BrandKit(tone_of_voice="friendly"),
        audience_brief=AudienceBrief(
            target_customer="Women 20-35 interested in skincare",
            language="vi",
            platform=["TikTok Shop"],
            market="VN",
        ),
        market_signal=MarketSignal(consumer_pain_point="dull skin", sources=["ref://trend"]),
    )
    base.update(overrides)
    return CampaignInput(**base)


def test_mock_pipeline_passes_qa():
    campaign_input = make_input()
    plan = gen_plan_agent.generate_plan(campaign_input)
    assets = gen_assets_agent.generate_assets(plan)

    result = qa_review_agent.review(campaign_input, plan, assets)

    assert result.passed is True
    assert not any(i.severity.value == "blocker" for i in result.issues)


def test_qa_fails_on_too_few_creative_routes():
    campaign_input = make_input()
    plan = gen_plan_agent.generate_plan(campaign_input)
    plan.creative_routes = plan.creative_routes[:1]  # drop to 1 route
    assets = gen_assets_agent.generate_assets(plan)

    result = qa_review_agent.review(campaign_input, plan, assets)

    assert result.passed is False
    assert any(i.rule_id == "PLAN.ROUTE_COUNT" for i in result.issues)


def test_qa_fails_on_missing_required_image_kind():
    campaign_input = make_input()
    plan = gen_plan_agent.generate_plan(campaign_input)
    assets = gen_assets_agent.generate_assets(plan)
    assets.images = [img for img in assets.images if img.kind.value != "marketplace_thumbnail"]

    result = qa_review_agent.review(campaign_input, plan, assets)

    assert result.passed is False
    assert any(i.rule_id == "ASSETS.MISSING_IMAGE_KIND" for i in result.issues)


def test_qa_fails_on_forbidden_claim_present():
    campaign_input = make_input(
        product_brief=ProductBrief(
            product_name="Ruby Serum",
            category="Skincare",
            key_selling_points=["Brightens skin"],
            target_market="Vietnam",
            required_claims=[],
            forbidden_claims=["cures acne"],
        )
    )
    plan = gen_plan_agent.generate_plan(campaign_input)
    assets = gen_assets_agent.generate_assets(plan)
    assets.listing_copy.product_description += " This product cures acne."

    result = qa_review_agent.review(campaign_input, plan, assets)

    assert result.passed is False
    assert any(i.rule_id == "USER.FORBIDDEN_CLAIM" for i in result.issues)


def test_qa_fails_on_missing_required_claim():
    campaign_input = make_input(
        product_brief=ProductBrief(
            product_name="Ruby Serum",
            category="Skincare",
            key_selling_points=["Brightens skin"],
            target_market="Vietnam",
            required_claims=["dermatologically tested"],
            forbidden_claims=[],
        )
    )
    plan = gen_plan_agent.generate_plan(campaign_input)
    assets = gen_assets_agent.generate_assets(plan)

    result = qa_review_agent.review(campaign_input, plan, assets)

    assert result.passed is False
    assert any(i.rule_id == "USER.MISSING_REQUIRED_CLAIM" for i in result.issues)


def test_qa_warns_but_does_not_block_on_video_aspect_ratio():
    campaign_input = make_input()
    plan = gen_plan_agent.generate_plan(campaign_input)
    assets = gen_assets_agent.generate_assets(plan)
    assets.videos[0].aspect_ratio = "1:1"

    result = qa_review_agent.review(campaign_input, plan, assets)

    assert result.passed is True  # warning only, not a blocker
    assert any(i.rule_id == "ASSETS.VIDEO_ASPECT" for i in result.issues)
