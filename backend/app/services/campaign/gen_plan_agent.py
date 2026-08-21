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
        main_campaign_angle=f"{product.product_name}: {product.key_selling_points[0] if product.key_selling_points else 'lựa chọn tốt hơn mỗi ngày'}",
        target_audience=campaign_input.audience_brief.target_customer,
        key_selling_message=f"{product.product_name} giải quyết {campaign_input.market_signal.consumer_pain_point or 'một vấn đề thực tế của khách hàng'}.",
        product_benefit_hierarchy=product.key_selling_points or ["Chất lượng", "Giá trị", "Tiện lợi"],
        sources=campaign_input.market_signal.sources or ["mock-source://trend-report-2026"],
    )

    creative_routes = [
        CreativeRoute(
            route_id="A",
            hook_idea="Mở đầu bằng vấn đề – khoét sâu – giải pháp trong 2 giây đầu",
            visual_direction="Cận cảnh sản phẩm, ánh sáng tự nhiên, phong cách UGC",
            message_angle="Dẫn dắt bằng nỗi đau khách hàng",
            suggested_platform_usage=["TikTok Shop", "Instagram Reels"],
        ),
        CreativeRoute(
            route_id="B",
            hook_idea="Mở đầu bằng lời chứng thực / bằng chứng xã hội",
            visual_direction="Ảnh sản phẩm trong studio, phông nền tối giản",
            message_angle="Dẫn dắt bằng niềm tin / bằng chứng xã hội",
            suggested_platform_usage=["Shopee", "TikTok Shop"],
        ),
    ]

    ab_test_plan = ABTestPlan(
        what_to_test="Phong cách mở đầu: nỗi đau khách hàng so với lời chứng thực",
        route_a="A",
        route_b="B",
        success_metrics=["CTR", "Tỷ lệ xem 3 giây", "Tỷ lệ thêm vào giỏ hàng"],
        expected_learning="Xác định điểm chạm cảm xúc nào tạo tương tác ban đầu tốt hơn với nhóm khách hàng này.",
    )

    return CampaignPlan(
        campaign_id=campaign_input.campaign_id,
        positioning=positioning,
        creative_routes=creative_routes,
        ab_test_plan=ab_test_plan,
        performance_learning=None,
    )
