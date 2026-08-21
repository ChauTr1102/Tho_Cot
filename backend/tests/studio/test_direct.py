"""
The worksheet is the studio's commercial judgement: where the shopper inspects
the product, use the brand's real photo; where the viewer is scrolling,
generate.

Two facts sit behind that rule, and both are measured. A shopper who receives a
parcel that does not match the listing image returns it. And a generated image
redraws the product's own packaging, badly where the lettering is rotated - a
real COSRX bottle came back reading `COSRᴀ` on its vertical wordmark in every
render, while the same string set horizontally was perfect.
"""
from app.schemas.campaign import AssetOrigin, ImageKind, Platform
from app.services.studio.config import studio_settings
from app.services.studio.direct import (
    build_worksheet,
    is_compliant,
    product_label_text,
    winning_route,
)
from app.services.studio.prompts import build_image_prompt


def test_shopee_main_reuses_a_real_photo_when_the_kho_has_one(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, route_id="A",
                         platforms=[Platform.SHOPEE])
    main = next(i for i in ws.items if i.slot_id == "shopee_main")
    assert main.origin is AssetOrigin.REUSE
    assert main.source_photo is not None


def test_shopee_main_falls_back_to_generate_when_the_kho_is_empty(sample_plan, sample_input, empty_sheet):
    ws = build_worksheet(sample_plan, sample_input, empty_sheet, route_id="A",
                         platforms=[Platform.SHOPEE])
    main = next(i for i in ws.items if i.slot_id == "shopee_main")
    assert main.origin is AssetOrigin.GENERATE


def test_tiktok_cover_is_always_generated(sample_plan, sample_input, rich_sheet):
    """No stock product photo is a vertical hook frame with a headline on it."""
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, route_id="A",
                         platforms=[Platform.TIKTOK_SHOP])
    cover = next(i for i in ws.items if i.slot_id == "tiktok_cover")
    assert cover.origin is AssetOrigin.GENERATE


def test_routes_a_and_b_get_visually_distant_spines(sample_plan, sample_input, rich_sheet):
    a = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE]).spine
    b = build_worksheet(sample_plan, sample_input, rich_sheet, "B", [Platform.SHOPEE]).spine
    assert a.look_key != b.look_key


def test_forbidden_claims_never_enter_rendered_text(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    rendered = " ".join(t for item in ws.items for _, t in item.texts).lower()
    for claim in sample_input.product_brief.forbidden_claims:
        assert claim.lower() not in rendered


# ---------------------------------------------------------------------------
# Compliance, everywhere text can leak
# ---------------------------------------------------------------------------

def test_a_dropped_hook_is_replaced_not_left_blank(sample_plan, sample_input, rich_sheet):
    """Route A's hook carries a forbidden claim. The frame must not go empty -
    an empty TEXT block is what makes the model invent a tagline."""
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    collection = next(i for i in ws.items if i.slot_id == "shopee_collection")
    headline = dict(collection.texts)["headline"]
    assert headline
    assert headline == sample_plan.positioning.key_selling_message


def test_forbidden_claims_never_enter_the_voiceover(sample_plan, sample_input, rich_sheet):
    """A claim that cannot be printed cannot be spoken either."""
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.TIKTOK_SHOP])
    spoken = " ".join(s.vo_text for s in ws.shots).lower()
    onscreen = " ".join(s.onscreen_text for s in ws.shots).lower()
    scenes = " ".join(s.scene for s in ws.shots).lower()
    for claim in sample_input.product_brief.forbidden_claims:
        assert claim.lower() not in spoken
        assert claim.lower() not in onscreen
        assert claim.lower() not in scenes


def test_is_compliant_matches_case_folded_substrings():
    assert not is_compliant("Trắng da vĩnh viễn sau 2 tuần", ["trắng da vĩnh viễn"])
    assert is_compliant("Phục hồi hàng rào da", ["trắng da vĩnh viễn"])
    assert is_compliant("anything", [])


# ---------------------------------------------------------------------------
# Origin routing
# ---------------------------------------------------------------------------

def test_a_thin_kho_never_fails_it_only_shifts_to_generate(sample_plan, bare_input, empty_sheet):
    """A brand with no photographs at all still gets a complete kit."""
    ws = build_worksheet(sample_plan, bare_input, empty_sheet, "A",
                         [Platform.SHOPEE, Platform.TIKTOK_SHOP])
    assert len(ws.items) == 7
    assert {i.origin for i in ws.items} == {AssetOrigin.GENERATE}
    assert all(i.source_photo is None for i in ws.items)
    assert all(i.scene and "{" not in i.scene for i in ws.items)


def test_generate_still_carries_the_brand_lock_reference(sample_plan, sample_input, rich_sheet):
    """A generated frame is anchored to a real photograph; that is what keeps
    the bottle the brand's bottle."""
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.TIKTOK_SHOP])
    cover = next(i for i in ws.items if i.slot_id == "tiktok_cover")
    assert cover.origin is AssetOrigin.GENERATE
    assert cover.source_photo is not None


def test_two_reuse_slots_do_not_ship_the_same_photograph_twice(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    main = next(i for i in ws.items if i.slot_id == "shopee_main")
    sku = next(i for i in ws.items if i.slot_id == "shopee_sku")
    assert sku.origin is AssetOrigin.REUSE
    assert main.source_photo != sku.source_photo


def test_a_photo_the_inventory_disqualified_is_never_used(sample_plan, sample_input, rich_sheet):
    """Seedance rejects a reference image under 300px on either side, which is
    why the 129x27 COSRX logo can never be pinned into a kit."""
    rich_sheet.photos[0].tags = ["too_small_for_ref"]
    rich_sheet.by_slot = {}
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    assert all(i.source_photo != rich_sheet.photos[0].path for i in ws.items)


# ---------------------------------------------------------------------------
# The work items themselves
# ---------------------------------------------------------------------------

def test_every_slot_of_every_requested_platform_becomes_an_item(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A",
                         [Platform.SHOPEE, Platform.TIKTOK_SHOP])
    assert [i.slot_id for i in ws.items] == [
        "shopee_main", "shopee_sku", "shopee_collection", "shopee_banner",
        "tiktok_cover", "tiktok_product", "tiktok_promo",
    ]
    kinds = {i.kind for i in ws.items}
    assert {ImageKind.HERO, ImageKind.SKU_DETAIL, ImageKind.COLLECTION,
            ImageKind.THUMBNAIL} <= kinds


def test_sizes_come_from_the_control_panel_not_from_literals(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A",
                         [Platform.SHOPEE, Platform.TIKTOK_SHOP])
    sizes = {i.slot_id: i.size for i in ws.items}
    assert sizes["shopee_main"] == studio_settings.IMAGE_SIZE_SQUARE
    assert sizes["shopee_banner"] == studio_settings.IMAGE_SIZE_LANDSCAPE
    assert sizes["tiktok_cover"] == studio_settings.IMAGE_SIZE_PORTRAIT


def test_the_white_background_rule_survives_into_the_prompt(sample_plan, sample_input, empty_sheet):
    ws = build_worksheet(sample_plan, sample_input, empty_sheet, "A", [Platform.SHOPEE])
    main = next(i for i in ws.items if i.slot_id == "shopee_main")
    assert main.rule == "pure_white_bg"
    prompt = build_image_prompt(main.scene, ws.spine, main.texts, ws.label_text,
                                main.ratio, main.rule)
    assert "pure white background" in prompt.lower()
    assert "{" not in prompt


def test_the_promotion_becomes_a_badge_that_reads_at_thumbnail_size(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    banner = dict(next(i for i in ws.items if i.slot_id == "shopee_banner").texts)
    assert banner["badge"] == "GIẢM 25%"
    assert banner["promo"] == sample_input.product_brief.price_or_promotion


# ---------------------------------------------------------------------------
# The product's own packaging
# ---------------------------------------------------------------------------

def test_label_text_names_the_wordmark_and_the_volume(sample_input):
    """The wordmark is listed separately because on the real bottle it is a
    separate piece of artwork, set vertically - and vertical lettering is
    exactly what the model got wrong (`COSRᴀ`)."""
    labels = product_label_text(sample_input.product_brief)
    assert labels[0] == "COSRX"
    assert "COSRX Advanced Snail 96 Mucin Power Essence" in labels
    assert "100ml" in labels


def test_label_text_is_empty_when_the_brief_has_no_product_name(sample_input):
    brief = sample_input.product_brief.model_copy(update={"product_name": ""})
    assert product_label_text(brief) == []


# ---------------------------------------------------------------------------
# The storyboard
# ---------------------------------------------------------------------------

def test_the_storyboard_is_four_resolved_beats(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.TIKTOK_SHOP])
    assert [s.role for s in ws.shots] == ["hook", "product", "benefit", "cta"]
    assert [s.index for s in ws.shots] == [0, 1, 2, 3]
    assert sum(s.seconds for s in ws.shots) >= 15    # qa_review_agent's floor
    for shot in ws.shots:
        assert shot.scene and "{" not in shot.scene
        assert shot.onscreen_text                     # the keyframe always says something
        assert shot.vo_text


def test_the_hook_beat_speaks_the_pain_point_as_a_question(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.TIKTOK_SHOP])
    hook = ws.shots[0]
    assert sample_input.market_signal.consumer_pain_point in hook.vo_text
    assert hook.vo_text.endswith("?")


def test_the_cta_beat_carries_the_offer_and_the_ask(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.TIKTOK_SHOP])
    cta = ws.shots[3]
    assert "GIẢM 25%" in cta.onscreen_text
    assert "MUA NGAY" in cta.onscreen_text


# ---------------------------------------------------------------------------
# Performance learning
# ---------------------------------------------------------------------------

def test_a_winning_past_route_leads_route_a(sample_plan, sample_input, rich_sheet):
    """past_campaign.xlsx: testimonial_ugc returned CTR 2.4% and ROAS 4.3
    against science_led's 0.9% and 2.1. Measured beats conventional."""
    assert "testimonial_ugc" in (winning_route(sample_plan) or "")
    ws = build_worksheet(sample_plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    assert ws.spine.look_key == "street_ugc"


def test_without_past_data_the_category_chooses_the_look(sample_plan, sample_input, rich_sheet):
    plan = sample_plan.model_copy(update={"performance_learning": None})
    ws = build_worksheet(plan, sample_input, rich_sheet, "A", [Platform.SHOPEE])
    assert ws.spine.look_key == "clinical_lab"       # Skincare / Facial Essence


# ---------------------------------------------------------------------------
# Degenerate inputs
# ---------------------------------------------------------------------------

def test_a_missing_brief_still_produces_a_complete_worksheet(sample_plan):
    """`generate_assets` may be called without a CampaignInput. The kit is
    generic, but it exists."""
    ws = build_worksheet(sample_plan, None, None, "A", [Platform.SHOPEE])
    assert len(ws.items) == 4
    assert all(i.origin is AssetOrigin.GENERATE for i in ws.items)
    assert ws.label_text == []
    assert len(ws.shots) == 4


def test_the_default_is_every_kit(sample_plan, sample_input, rich_sheet):
    ws = build_worksheet(sample_plan, sample_input, rich_sheet)
    assert {i.platform for i in ws.items} == {Platform.SHOPEE, Platform.TIKTOK_SHOP}
    assert ws.route_id == "A"
