"""
MOCK gen_plan agent.

Real implementation would call Seed 2.1 (optional model) for campaign
strategy / positioning reasoning, plus a research step (web/market signal
lookup) to back "sources". This mock returns a deterministic, schema-valid
CampaignPlan so the QA agent can be developed/tested independently.
"""
from __future__ import annotations

from app.schemas.campaign import (
    ABTestPlan,
    CampaignInput,
    CampaignPlan,
    CreativeRoute,
    ProductPositioning,
)


def generate_plan(campaign_input: CampaignInput) -> CampaignPlan:
    product = campaign_input.product_brief

    positioning = ProductPositioning(
        main_campaign_angle=f"{product.product_name}: {product.key_selling_points[0] if product.key_selling_points else 'better everyday choice'}",
        target_audience=campaign_input.audience_brief.target_customer,
        key_selling_message=f"{product.product_name} solves {campaign_input.market_signal.consumer_pain_point or 'a real customer pain point'}.",
        product_benefit_hierarchy=product.key_selling_points or ["Quality", "Value", "Convenience"],
        sources=campaign_input.market_signal.sources or ["mock-source://trend-report-2026"],
    )

    creative_routes = [
        CreativeRoute(
            route_id="A",
            hook_idea="Problem-agitate-solve opener in first 2 seconds",
            visual_direction="Close-up product shot, natural lighting, UGC style",
            message_angle="Pain-point led",
            suggested_platform_usage=["TikTok Shop", "Instagram Reels"],
        ),
        CreativeRoute(
            route_id="B",
            hook_idea="Testimonial / social-proof opener",
            visual_direction="Studio product photography, clean background",
            message_angle="Trust / social-proof led",
            suggested_platform_usage=["Shopee", "TikTok Shop"],
        ),
    ]

    ab_test_plan = ABTestPlan(
        what_to_test="Hook style: pain-point vs. testimonial",
        route_a="A",
        route_b="B",
        success_metrics=["CTR", "3s view rate", "Add-to-cart rate"],
        expected_learning="Which emotional entry point drives higher early engagement for this audience.",
    )

    return CampaignPlan(
        campaign_id=campaign_input.campaign_id,
        positioning=positioning,
        creative_routes=creative_routes,
        ab_test_plan=ab_test_plan,
        performance_learning=None,
    )
