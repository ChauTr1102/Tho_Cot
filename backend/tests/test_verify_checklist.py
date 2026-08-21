from fastapi.testclient import TestClient


def _base_campaign_input() -> dict:
    return {
        "product_brief": {
            "product_name": "Fizzy Roots Sparkling Tea",
            "category": "F&B",
            "key_selling_points": ["Zero added sugar", "Made in Vietnam"],
            "price_or_promotion": {"price": 25000, "currency": "VND", "promotion": "Buy 4 Get 1 Free"},
            "target_market": "Vietnam",
            "required_claims": ["zero added sugar", "made in Vietnam"],
            "restricted_or_forbidden_claims": ["cures bloating"],
        },
        "brand_kit": {
            "logo": {"path": "./brand_assets/brand_logo.jpg"},
            "brand_colors": {"primary": "#0E7C61", "secondary": "#F4D35E", "accent": ["#FFFFFF"], "palette": ["#0E7C61"]},
            "tone_of_voice": {"description": "playful", "attributes": ["playful"], "do": [], "dont": []},
            "product_photos": ["./brand_assets/product_photo_studio.jpg"],
            "existing_product_visuals": [],
        },
        "audience_brief": {
            "target_customer": "Gen Z",
            "language": "vi",
            "platform": "TikTok Shop",
            "market": "VN",
        },
        "market_signal": {
            "trend": "functional beverages",
            "seasonal_moment": None,
            "consumer_pain_point": "sugar guilt",
            "search_keyword": ["tra hoa qua khong duong"],
            "competitor_angle": None,
            "campaign_objective": "Drive trial purchases",
        },
        "past_campaign_data": {
            "enabled": False,
            "ctr": None, "cvr": None, "roas": None,
            "watch_time": {"value": None, "unit": "seconds"},
            "add_to_cart_rate": None,
            "comments": [],
            "sales_results": {"units_sold": None, "revenue": None, "currency": "VND"},
        },
    }


def _passing_campaign_output() -> dict:
    return {
        "product_positioning": {
            "main_campaign_angle": "Zero added sugar, without the trade-off.",
            "target_audience": "Gen Z",
            "key_selling_message": "Fizzy Roots solves sugar guilt with zero added sugar, made in Vietnam.",
            "product_benefit_hierarchy": ["Zero added sugar", "Made in Vietnam"],
        },
        "creative_routes": [
            {
                "name": "Route A", "hook_idea": "Problem-agitate-solve",
                "visual_direction": "Close-up shot", "message_angle": "Pain-point led",
                "suggested_platform_usage": ["TikTok Shop"],
            },
            {
                "name": "Route B", "hook_idea": "Testimonial",
                "visual_direction": "Studio shot", "message_angle": "Trust led",
                "suggested_platform_usage": ["TikTok Shop"],
            },
        ],
        "short_form_video_asset": {
            "generated_video_urls": ["https://example.com/route_a.mp4"],
            "format": "9:16",
            "duration": "20s",
            "additional_cuts": [],
        },
        "product_collection_image_set": {
            "product_hero_image": "https://example.com/hero.jpg",
            "sku_detail_image": "https://example.com/sku.jpg",
            "campaign_collection_image": "https://example.com/collection.jpg",
            "marketplace_thumbnail": "https://example.com/thumb.jpg",
        },
        "commerce_copy": {
            "product_title": "Fizzy Roots Sparkling Tea",
            "product_description": "Made with zero added sugar. Made in Vietnam.",
            "listing_bullet_points": ["Zero added sugar", "Made in Vietnam"],
            "ad_caption": "Zero added sugar, made in Vietnam.",
            "promotion_copy": "Buy 4 Get 1 Free",
            "short_hook_lines": ["Meet Fizzy Roots."],
        },
        "ab_testing_plan": {
            "what_to_test": "Hook style",
            "route_a_description": "Pain-point led opener",
            "route_b_description": "Testimonial led opener",
            "suggested_success_metrics": ["CTR", "Add-to-cart rate"],
            "expected_learning": "Which hook drives more engagement.",
        },
        "performance_learning": None,
    }


def test_verify_checklist_passes_for_compliant_output(client: TestClient):
    payload = {
        "campaign_input": _base_campaign_input(),
        "campaign_output": _passing_campaign_output(),
        "iteration": 1,
    }
    res = client.post("/api/verify-checklist", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["passed"] is True
    assert data["regenerate"] == []
    assert data["issues"] == []


def test_verify_checklist_flags_forbidden_claim_and_regenerates_copy(client: TestClient):
    output = _passing_campaign_output()
    output["commerce_copy"]["product_description"] += " This product cures bloating."

    payload = {
        "campaign_input": _base_campaign_input(),
        "campaign_output": output,
        "iteration": 1,
    }
    res = client.post("/api/verify-checklist", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["passed"] is False
    assert "copy" in data["regenerate"]
    rule_ids = {issue["rule_id"] for issue in data["issues"]}
    assert "USER.FORBIDDEN_CLAIM" in rule_ids


def test_verify_checklist_flags_missing_image_and_regenerates_images(client: TestClient):
    output = _passing_campaign_output()
    output["product_collection_image_set"]["sku_detail_image"] = ""

    payload = {
        "campaign_input": _base_campaign_input(),
        "campaign_output": output,
        "iteration": 1,
    }
    res = client.post("/api/verify-checklist", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["passed"] is False
    assert "images" in data["regenerate"]
    rule_ids = {issue["rule_id"] for issue in data["issues"]}
    assert "ASSETS.MISSING_IMAGE_KIND" in rule_ids


def test_verify_checklist_flags_single_route_and_regenerates_plan(client: TestClient):
    output = _passing_campaign_output()
    output["creative_routes"] = output["creative_routes"][:1]

    payload = {
        "campaign_input": _base_campaign_input(),
        "campaign_output": output,
        "iteration": 1,
    }
    res = client.post("/api/verify-checklist", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["passed"] is False
    assert "plan" in data["regenerate"]
    rule_ids = {issue["rule_id"] for issue in data["issues"]}
    assert "PLAN.ROUTE_COUNT" in rule_ids


def test_verify_checklist_flags_bad_video_aspect_and_regenerates_video(client: TestClient):
    output = _passing_campaign_output()
    output["short_form_video_asset"]["format"] = "1:1"
    output["short_form_video_asset"]["duration"] = "40s"

    payload = {
        "campaign_input": _base_campaign_input(),
        "campaign_output": output,
        "iteration": 1,
    }
    res = client.post("/api/verify-checklist", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    # Aspect/duration are WARNING-only, so this campaign still passes overall,
    # but video should still be flagged as a stage to regenerate.
    assert "video" in data["regenerate"]
    rule_ids = {issue["rule_id"] for issue in data["issues"]}
    assert "ASSETS.VIDEO_ASPECT" in rule_ids
    assert "ASSETS.VIDEO_DURATION" in rule_ids
