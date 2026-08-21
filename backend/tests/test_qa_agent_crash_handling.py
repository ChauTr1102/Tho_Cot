"""
A crashed checklist item must never reach the user as a QA "warning".

Reported bug: a verifier item pointed `needs_image` at a field that was
actually free text (a long product description), and pathlib raised
OSError("File name too long") trying to treat it as a file path. That
exception escaped `_verify_item`, was caught by `verify()`'s broad
except-Exception handler, and got embedded verbatim into a QAIssue message
— so the user saw "Verifier agent crashed: [Errno 36] File name too long:
'<the entire product description>'" rendered as if it were a real QA
finding about their campaign.

The fix: `verify()` still catches the crash (so one bad item cannot take
down the whole checklist run), but the crashed item is now dropped from
`issues` and `checked_items` entirely rather than being reported with its
raw exception text — it was never actually judged, so it must not look
like a judgment.
"""
from __future__ import annotations

from app.schemas.qa_checklist import QAIssue, QASeverity, RegenerateTarget, VerifyChecklistRequest
from app.services.qa_agent.service import AgentQAChecklistService
from app.services.research import RawModelClient


def _minimal_request() -> VerifyChecklistRequest:
    return VerifyChecklistRequest.model_validate({
        "campaign_input": {
            "product_brief": {
                "product_name": "G7 3in1", "category": "F&B",
                "key_selling_points": ["Đậm vị"],
                "price_or_promotion": {"price": 135000, "currency": "VND", "promotion": None},
                "target_market": "Vietnam", "required_claims": [], "restricted_or_forbidden_claims": [],
            },
            "brand_kit": {
                "logo": {"path": "./logo.jpg"},
                "brand_colors": {"primary": "#000", "secondary": None, "accent": [], "palette": []},
                "tone_of_voice": {"description": "", "attributes": [], "do": [], "dont": []},
                "product_photos": ["./photo.jpg"], "existing_product_visuals": [],
            },
            "audience_brief": {"target_customer": "Gen Z", "language": "vi", "platform": "TikTok Shop", "market": "VN"},
            "market_signal": {
                "trend": None, "seasonal_moment": None, "consumer_pain_point": None,
                "search_keyword": [], "competitor_angle": None, "campaign_objective": "Drive trial",
            },
            "past_campaign_data": {
                "enabled": False, "ctr": None, "cvr": None, "roas": None,
                "watch_time": {"value": None, "unit": "seconds"}, "add_to_cart_rate": None,
                "comments": [], "sales_results": {"units_sold": None, "revenue": None, "currency": "VND"},
            },
        },
        "campaign_output": {
            "product_positioning": {
                "main_campaign_angle": "Đậm vị", "target_audience": "Gen Z",
                "key_selling_message": "Đậm vị Việt", "product_benefit_hierarchy": ["Đậm vị"],
            },
            "creative_routes": [
                {"name": "A", "hook_idea": "x", "visual_direction": "x", "message_angle": "x", "suggested_platform_usage": []},
                {"name": "B", "hook_idea": "x", "visual_direction": "x", "message_angle": "x", "suggested_platform_usage": []},
            ],
            "short_form_video_asset": {"generated_video_urls": ["https://example.com/v.mp4"], "format": "9:16", "duration": "20s", "additional_cuts": []},
            "product_collection_image_set": {
                "product_hero_image": "https://example.com/hero.jpg",
                "sku_detail_image": "https://example.com/sku.jpg",
                "campaign_collection_image": "https://example.com/collection.jpg",
                "marketplace_thumbnail": "https://example.com/thumb.jpg",
            },
            "commerce_copy": {
                "product_title": "G7 3in1",
                "product_description": "Trải nghiệm năng lượng bứt phá mỗi sáng. " * 5,
                "listing_bullet_points": ["Đậm vị"], "ad_caption": "Đậm vị Việt",
                "promotion_copy": "Mua 3 tặng 1", "short_hook_lines": ["Đậm vị"],
            },
            "ab_testing_plan": {
                "what_to_test": "hook", "route_a_description": "a", "route_b_description": "b",
                "suggested_success_metrics": ["CTR"], "expected_learning": "x",
            },
            "performance_learning": None,
        },
        "iteration": 1,
    })


def test_crashed_item_is_excluded_not_reported_as_a_warning(monkeypatch):
    service = AgentQAChecklistService(client=RawModelClient("test-key"))

    checklist = [
        {
            "id": "OK_ITEM", "description": "always passes", "severity": "WARNING",
            "category": "asset", "target_fields": ["commerce_copy.product_title"], "needs_image": False,
        },
        {
            "id": "CRASHING_ITEM", "description": "hits the bug", "severity": "WARNING",
            "category": "asset", "target_fields": ["commerce_copy.product_description"], "needs_image": True,
        },
    ]
    monkeypatch.setattr(service, "_generate_checklist", lambda *a, **k: checklist)

    def fake_verify_item(self, client, item, request):
        if item["id"] == "CRASHING_ITEM":
            # Reproduces the real bug: an internal error escaping the item,
            # e.g. OSError("File name too long") from image_loader.
            raise OSError(36, "File name too long", request.campaign_output.commerce_copy.product_description)
        return None  # OK_ITEM passes

    monkeypatch.setattr(AgentQAChecklistService, "_verify_item", fake_verify_item)

    result = service.verify(_minimal_request())

    # The crash must not appear anywhere in the user-facing issues.
    assert result.issues == []
    for issue in result.issues:
        assert "Errno" not in issue.message
        assert "File name too long" not in issue.message

    # The crashed item is excluded from the tick-list entirely — not marked
    # failed (that would misrepresent an internal error as a real finding).
    checked_ids = {item.rule_id for item in result.checked_items}
    assert "CRASHING_ITEM" not in checked_ids
    assert "OK_ITEM" in checked_ids

    # One item crashing must not fail the whole run.
    assert result.passed is True


def test_unusable_verifier_response_is_also_excluded_not_fabricated(monkeypatch):
    """The other internal-failure path (_verify_item's own
    ResearchOutputError/JSONDecodeError handling) must behave the same way:
    excluded from the report, not turned into a QAIssue carrying a raw
    exception message."""
    service = AgentQAChecklistService(client=RawModelClient("test-key"))

    checklist = [
        {
            "id": "BAD_JSON_ITEM", "description": "verifier returns garbage", "severity": "BLOCKER",
            "category": "plan", "target_fields": ["product_positioning.main_campaign_angle"], "needs_image": False,
        },
    ]
    monkeypatch.setattr(service, "_generate_checklist", lambda *a, **k: checklist)
    monkeypatch.setattr(service.client, "ask", lambda **kwargs: "not valid json")

    result = service.verify(_minimal_request())

    assert result.issues == []
    assert result.checked_items == []
    assert result.passed is True
