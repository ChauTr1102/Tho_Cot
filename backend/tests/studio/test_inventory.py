"""Inventory decides which slots can be filled with the brand's real photos.

Getting `bg_whiteness` wrong sends an off-white photo to Shopee's main slot and
breaks a marketplace rule, so it is measured, not guessed. Getting
`too_small_for_ref` wrong sends a 129x27 logo to Seedance, which rejects the
whole request with `InvalidParameter: expected the width to be at least 300px`.

Every test here runs with no network and no API key: the vision call is
monkeypatched at `inventory.ark.describe_image`.
"""
import json

import pytest
from PIL import Image

from app.services.studio import inventory
from app.services.studio.config import studio_settings
from app.services.studio.inventory import (
    InventorySheet,
    PhotoFacts,
    build_sheet,
    measure,
)


def _make(tmp_path, name, size=(1200, 1200), bg=(255, 255, 255), blob=(80, 40, 40)):
    """Write a synthetic product photo: a solid background with a dark centre blob."""
    im = Image.new("RGB", size, bg)
    w, h = size
    for x in range(w // 3, 2 * w // 3):
        for y in range(h // 3, 2 * h // 3):
            im.putpixel((x, y), blob)
    p = tmp_path / name
    im.save(p, quality=95)
    return str(p)


def _stub_vision(monkeypatch, payload, *, calls=None):
    """Replace the network vision call with a canned JSON answer."""

    def fake_describe_image(image_bytes, prompt, max_tokens=600):
        assert isinstance(image_bytes, (bytes, bytearray)) and image_bytes
        assert "JSON" in prompt
        if calls is not None:
            calls.append(prompt)
        return json.dumps(payload) if not isinstance(payload, str) else payload

    monkeypatch.setattr(inventory.ark, "describe_image", fake_describe_image)


# --------------------------------------------------------------------------
# measure() — Pillow only
# --------------------------------------------------------------------------

def test_white_background_photo_scores_near_one(tmp_path):
    facts = measure(_make(tmp_path, "white.jpg"))
    assert facts.bg_whiteness > 0.9
    assert facts.width == 1200 and abs(facts.aspect - 1.0) < 0.01


def test_coloured_background_photo_scores_low(tmp_path):
    facts = measure(_make(tmp_path, "beige.jpg", bg=(180, 150, 110)))
    assert facts.bg_whiteness < 0.5


def test_warm_offwhite_studio_background_is_not_white_enough_for_shopee(tmp_path):
    """Marou and Cocoon shoot on warm cream (~#F0EAD9). It reads as white to a
    careless threshold and would break Shopee's pure-white rule."""
    facts = measure(_make(tmp_path, "cream.jpg", bg=(240, 234, 217)))
    assert facts.bg_whiteness < studio_settings.BG_WHITE_THRESHOLD
    assert "shopee_main" not in inventory.eligible_slots(facts)


def test_near_white_studio_grey_still_counts_as_white(tmp_path):
    """Anker shoots on (245,245,247). That is a white listing background."""
    facts = measure(_make(tmp_path, "f5.jpg", bg=(245, 245, 247)))
    assert facts.bg_whiteness > studio_settings.BG_WHITE_THRESHOLD


def test_bright_ivory_is_rejected_even_though_it_outshines_a_grey_sweep(tmp_path):
    """The case a brightness-only rule gets wrong. COSRX's infographic sits on
    ivory (255,248,235). Its darkest channel is exactly 235, so it clears the
    brightness floor, and it is on average brighter than Anker's genuinely white
    (245,245,247) backdrop -- yet it is visibly cream. Tint, not brightness, is
    what separates them."""
    ivory_rgb, grey_rgb = (255, 248, 235), (245, 245, 247)
    assert min(ivory_rgb) >= inventory.BG_WHITE_MIN_CHANNEL   # clears the floor
    assert sum(ivory_rgb) > sum(grey_rgb)                     # and is brighter
    ivory = measure(_make(tmp_path, "ivory.jpg", bg=ivory_rgb))
    grey = measure(_make(tmp_path, "grey.jpg", bg=grey_rgb))
    assert ivory.bg_whiteness < studio_settings.BG_WHITE_THRESHOLD
    assert grey.bg_whiteness > studio_settings.BG_WHITE_THRESHOLD


def test_sharpness_is_higher_for_a_detailed_photo(tmp_path):
    flat = measure(_make(tmp_path, "flat.jpg", blob=(250, 250, 250)))
    edgy = measure(_make(tmp_path, "edgy.jpg", blob=(10, 10, 10)))
    assert edgy.sharpness > flat.sharpness


def test_measure_does_not_touch_the_network(tmp_path, monkeypatch):
    def explode(*_a, **_k):
        raise AssertionError("measure() must be Pillow-only")

    monkeypatch.setattr(inventory.ark, "describe_image", explode)
    assert measure(_make(tmp_path, "x.jpg")).width == 1200


def test_transparent_logo_is_measured_against_white_not_black(tmp_path):
    """A transparent PNG lands on a white listing page. Dropping the alpha
    channel would read the empty pixels as black and score it 0.0."""
    im = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
    for x in range(400, 500):
        for y in range(400, 500):
            im.putpixel((x, y), (20, 20, 20, 255))
    p = tmp_path / "logo.png"
    im.save(p)
    assert measure(str(p)).bg_whiteness > 0.9


# --------------------------------------------------------------------------
# Hard disqualifications, both measured against the live API
# --------------------------------------------------------------------------

def test_photo_under_300px_is_tagged_too_small_for_ref(tmp_path):
    """Seedance: `expected the width to be at least 300px, but received a
    129x27px image instead`. The COSRX logo is exactly this case."""
    facts = measure(_make(tmp_path, "logo.jpg", size=(129, 27)))
    assert "too_small_for_ref" in facts.tags
    assert not facts.is_video_reference_safe


def test_too_small_photos_never_reach_the_video_reference_list(tmp_path):
    small = _make(tmp_path, "logo.jpg", size=(129, 27))
    big = _make(tmp_path, "hero.jpg", size=(1200, 1200))
    sheet = build_sheet([small, big], use_vision=False)
    assert sheet.video_refs == [big]


def test_extreme_aspect_ratio_is_rejected_as_a_reference(tmp_path):
    """The API accepts 0.4-2.5 only. The Oatside logo is 800x200 = 4.0."""
    facts = measure(_make(tmp_path, "wide.jpg", size=(800, 200)))
    assert "bad_aspect_for_ref" in facts.tags
    assert not facts.is_video_reference_safe


def test_photo_with_people_is_excluded_from_video_references(tmp_path, monkeypatch):
    """Seedance rejects reference images containing real human faces."""
    _stub_vision(monkeypatch, {"angle": "lifestyle", "has_people": True,
                               "has_text": False, "product_count": 1,
                               "background": "scene", "label_readable": False})
    sheet = build_sheet([_make(tmp_path, "ugc.jpg")], use_vision=True)
    facts = sheet.photos[0]
    assert "has_people" in facts.tags
    assert not facts.is_video_reference_safe
    assert sheet.video_refs == []


def test_svg_is_skipped_entirely(tmp_path):
    """Pillow cannot open it and the API accepts only jpeg/png/webp/bmp/tiff/
    gif/heic/heif. One brand's logo is SVG."""
    p = tmp_path / "logo.svg"
    p.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    good = _make(tmp_path, "ok.jpg")
    sheet = build_sheet([str(p), good], use_vision=False)
    assert [f.path for f in sheet.photos] == [good]
    assert str(p) in sheet.skipped


def test_unreadable_file_is_skipped_without_killing_the_run(tmp_path):
    bad = tmp_path / "truncated.jpg"
    bad.write_bytes(b"not really a jpeg")
    good = _make(tmp_path, "ok.jpg")
    sheet = build_sheet([str(bad), good], use_vision=False)
    assert [f.path for f in sheet.photos] == [good]
    assert str(bad) in sheet.skipped


# --------------------------------------------------------------------------
# Slot eligibility
# --------------------------------------------------------------------------

def test_white_square_photo_is_eligible_for_shopee_main(tmp_path):
    sheet = build_sheet([_make(tmp_path, "a.jpg")], use_vision=False)
    assert "shopee_main" in sheet.photos[0].eligible_slots
    assert sheet.by_slot["shopee_main"] == [sheet.photos[0].path]


def test_small_photo_is_not_eligible_for_shopee_main(tmp_path):
    """Shopee's main image has a resolution floor (SHOPEE_MIN_PX)."""
    sheet = build_sheet([_make(tmp_path, "small.jpg", size=(600, 600))], use_vision=False)
    assert "shopee_main" not in sheet.photos[0].eligible_slots


def test_by_slot_is_empty_not_missing_when_nothing_qualifies(tmp_path):
    sheet = build_sheet([_make(tmp_path, "beige.jpg", bg=(180, 150, 110))], use_vision=False)
    assert sheet.by_slot.get("shopee_main", []) == []
    assert "shopee_main" in sheet.by_slot


def test_baked_in_marketing_text_disqualifies_the_main_image(tmp_path, monkeypatch):
    """COSRX's kho photos are marketing collateral with GLOBAL NO.1 set across
    the top. Shopee's main image may not carry promotional overlay text."""
    _stub_vision(monkeypatch, {"angle": "front", "has_people": False,
                               "has_text": True, "product_count": 1,
                               "background": "plain", "label_readable": True})
    sheet = build_sheet([_make(tmp_path, "infographic.jpg")], use_vision=True)
    assert "shopee_main" not in sheet.photos[0].eligible_slots


def test_two_products_in_frame_disqualify_the_main_image_but_fill_collection(tmp_path, monkeypatch):
    _stub_vision(monkeypatch, {"angle": "front", "has_people": False,
                               "has_text": False, "product_count": 3,
                               "background": "white", "label_readable": True})
    sheet = build_sheet([_make(tmp_path, "group.jpg")], use_vision=True)
    slots = sheet.photos[0].eligible_slots
    assert "shopee_main" not in slots
    assert "shopee_collection" in slots


def test_a_diagram_with_no_product_in_it_fills_no_slot(tmp_path, monkeypatch):
    """COSRX's `product_02.jpg` is a 'how snail secretion filtrate works'
    diagram: high resolution, correctly named, and a photograph of nothing for
    sale. Only vision can tell, and it must veto every product slot."""
    _stub_vision(monkeypatch, {"angle": "lifestyle", "has_people": False,
                               "has_text": True, "product_count": 0,
                               "background": "plain", "label_readable": False})
    sheet = build_sheet([_make(tmp_path, "diagram.jpg")], use_vision=True)
    assert sheet.photos[0].eligible_slots == []


def test_collection_needs_vision_because_nothing_else_can_count_products(tmp_path):
    """`product_count >= 2` is the slot's only requirement, so without vision it
    is unknown and the slot stays empty rather than guessing."""
    sheet = build_sheet([_make(tmp_path, "a.jpg")], use_vision=False)
    assert "shopee_collection" not in sheet.photos[0].eligible_slots


def test_lifestyle_angle_is_kept_out_of_the_sku_closeup(tmp_path, monkeypatch):
    """The SKU close-up is where the shopper inspects what they are buying."""
    _stub_vision(monkeypatch, {"angle": "lifestyle", "has_people": False,
                               "has_text": False, "product_count": 1,
                               "background": "scene", "label_readable": False})
    sheet = build_sheet([_make(tmp_path, "scene.jpg")], use_vision=True)
    assert "shopee_sku" not in sheet.photos[0].eligible_slots


def test_vision_tags_only_veto_never_invent(tmp_path):
    """With vision off, geometry alone decides. A photo is not disqualified for
    a fact nobody measured."""
    sheet = build_sheet([_make(tmp_path, "a.jpg")], use_vision=False)
    slots = sheet.photos[0].eligible_slots
    assert {"shopee_main", "shopee_sku", "tiktok_product"} <= set(slots)


def test_by_slot_ranks_the_best_candidate_first(tmp_path):
    small = _make(tmp_path, "small.jpg", size=(900, 900))
    large = _make(tmp_path, "large.jpg", size=(2000, 2000))
    sheet = build_sheet([small, large], use_vision=False)
    assert sheet.by_slot["tiktok_product"][0] == large


# --------------------------------------------------------------------------
# Vision plumbing
# --------------------------------------------------------------------------

def test_vision_answer_is_parsed_out_of_a_fenced_code_block(tmp_path, monkeypatch):
    _stub_vision(monkeypatch, '```json\n{"angle": "macro", "has_people": false, '
                              '"has_text": false, "product_count": 1, '
                              '"background": "white", "label_readable": true}\n```')
    sheet = build_sheet([_make(tmp_path, "a.jpg")], use_vision=True)
    assert "angle:macro" in sheet.photos[0].tags
    assert "no_people" in sheet.photos[0].tags


def test_vision_failure_degrades_to_geometry_instead_of_killing_the_run(tmp_path, monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError("read timed out")

    monkeypatch.setattr(inventory.ark, "describe_image", boom)
    sheet = build_sheet([_make(tmp_path, "a.jpg")], use_vision=True)
    assert "vision_failed" in sheet.photos[0].tags
    assert "shopee_main" in sheet.photos[0].eligible_slots


def test_vision_garbage_is_ignored_not_trusted(tmp_path, monkeypatch):
    _stub_vision(monkeypatch, "I am sorry, I cannot help with that.")
    sheet = build_sheet([_make(tmp_path, "a.jpg")], use_vision=True)
    assert "vision_failed" in sheet.photos[0].tags


def test_vision_is_called_once_per_photo(tmp_path, monkeypatch):
    calls = []
    _stub_vision(monkeypatch, {"angle": "front", "has_people": False,
                               "has_text": False, "product_count": 1,
                               "background": "white", "label_readable": True},
                 calls=calls)
    paths = [_make(tmp_path, f"p{i}.jpg", size=(900, 900)) for i in range(5)]
    build_sheet(paths, use_vision=True)
    assert len(calls) == 5


def test_vision_is_not_called_when_disabled(tmp_path, monkeypatch):
    def explode(*_a, **_k):
        raise AssertionError("use_vision=False must not call the API")

    monkeypatch.setattr(inventory.ark, "describe_image", explode)
    build_sheet([_make(tmp_path, "a.jpg")], use_vision=True and False)


# --------------------------------------------------------------------------
# Contracts Task 7 and Task 11 code against
# --------------------------------------------------------------------------

def test_empty_sheet_is_constructible_for_downstream_fixtures():
    sheet = InventorySheet()
    assert sheet.photos == [] and sheet.by_slot == {} and sheet.video_refs == []
    assert InventorySheet(photos=[], by_slot={}).photos == []


def test_build_sheet_of_nothing_still_lists_every_slot(tmp_path):
    sheet = build_sheet([], use_vision=False)
    assert set(sheet.by_slot) == set(inventory.SLOT_RULES)
    assert all(v == [] for v in sheet.by_slot.values())


def test_photofacts_is_json_serialisable_for_the_sse_stream(tmp_path):
    facts = measure(_make(tmp_path, "a.jpg"))
    payload = json.loads(json.dumps(inventory.to_dict(facts)))
    assert payload["width"] == 1200
    assert isinstance(payload["eligible_slots"], list)


def test_photofacts_defaults_allow_hand_built_fixtures():
    facts = PhotoFacts(path="/fake/a.jpg", width=1200, height=1200,
                       aspect=1.0, bg_whiteness=1.0, sharpness=10.0)
    assert facts.tags == [] and facts.eligible_slots == []
    assert facts.min_side == 1200


@pytest.mark.parametrize("slot_id", ["shopee_main", "shopee_sku",
                                     "shopee_collection", "tiktok_product"])
def test_every_documented_slot_has_a_rule(slot_id):
    assert slot_id in inventory.SLOT_RULES


def test_slot_ids_have_not_drifted_from_the_platform_kits():
    """`SLOT_RULES` names slots declared in `platforms.py`. If the art director
    renames one, `by_slot` silently stops filling it and the whole kit falls
    back to GENERATE with every test still green -- so assert it here instead."""
    platforms = pytest.importorskip("app.services.studio.platforms")
    kit_slots = {s.id for kit in platforms.KITS.values() for s in kit.slots}

    assert set(inventory.SLOT_RULES) <= kit_slots, "a rule names a slot that no kit has"
    reuse_slots = {s.id for kit in platforms.KITS.values() for s in kit.slots
                   if s.prefer_origin.value == "reuse"}
    assert reuse_slots <= set(inventory.SLOT_RULES), (
        "a slot that prefers a real photo has no eligibility rule, so it can "
        "never be filled from the kho"
    )
