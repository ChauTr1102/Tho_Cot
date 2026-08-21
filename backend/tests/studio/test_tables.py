"""These tables are the studio's taste. The tests guard the properties that make
the output usable rather than the exact wording, which the art director tunes.

Read a failure here as "the edit broke a promise the rest of the studio relies
on", not as "the edit was ugly". The promises are:
  * routes A and B stay visibly different from each other;
  * every slot named in one table exists in the others;
  * every placeholder resolves, and every text key is in the vocabulary;
  * the storyboard still fits the QA agent's duration window.
"""
import pytest

from app.schemas.campaign import AssetOrigin, ImageKind, Platform
from app.services.campaign import qa_review_agent
from app.services.studio.config import studio_settings
from app.services.studio.looks import (
    AXES,
    CONTRAST_PARTNERS,
    LOOKS,
    MIN_AXIS_DISTANCE,
    pick_looks,
)
from app.services.studio.platforms import KITS
from app.services.studio.slots import SHOT_TEMPLATES, SLOT_SCENES, TEXT_KEYS


def _axis_distance(a: str, b: str) -> int:
    return sum(1 for axis in AXES if LOOKS[a].axes[axis] != LOOKS[b].axes[axis])


# ---------------------------------------------------------------------------
# Looks
# ---------------------------------------------------------------------------

def test_ab_looks_differ_on_at_least_two_axes():
    """Two routes that look alike make the A/B test meaningless."""
    a, b = pick_looks("Skincare", "clean, scientific", "glass skin", None)
    differing = [k for k in LOOKS[a].axes if LOOKS[a].axes[k] != LOOKS[b].axes[k]]
    assert len(differing) >= 2


def test_winning_past_route_forces_its_look():
    a, b = pick_looks("Skincare", "clean, scientific", "glass skin",
                      winning_route="testimonial_ugc")
    assert "street_ugc" in (a, b)


def test_every_look_fills_every_prompt_placeholder():
    for key, look in LOOKS.items():
        for field in ("lens", "light", "surface", "grade"):
            assert getattr(look, field).strip(), f"{key}.{field} is empty"


def test_every_look_declares_all_three_axes_with_no_typos():
    """A missing or misspelt axis would silently make two looks compare as equal."""
    for key, look in LOOKS.items():
        assert set(look.axes) == set(AXES), f"{key} has axes {sorted(look.axes)}"


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("K-beauty skincare", "clinical_lab"),            # 01 COSRX snail essence
        ("F&B / oat milk", "fresh_market"),               # 02 Oatside barista
        ("Điện tử / sạc dự phòng", "dark_luxe"),          # 03 Anker power bank
        ("Mỹ phẩm thuần chay", "fresh_market"),           # 04 Cocoon coffee body scrub
        ("F&B / cà phê hoà tan", "warm_home"),            # 05 Trung Nguyên G7
        ("F&B / socola cao cấp bean-to-bar", "dark_luxe"),  # 06 Marou chocolate
    ],
)
def test_the_six_demo_categories_map_to_their_intended_look(category, expected):
    """Pins the mapping for the brands the demo actually runs on.

    Re-point one on purpose and update the row; break one by accident and this
    tells you which brand you just restyled.
    """
    assert pick_looks(category)[0] == expected


@pytest.mark.parametrize("category", [
    "K-beauty skincare", "F&B / oat milk", "Điện tử / sạc dự phòng",
    "Mỹ phẩm thuần chay", "F&B / cà phê hoà tan", "F&B / socola cao cấp bean-to-bar",
    "something nobody has ever sold before",
])
def test_every_category_yields_a_pair_that_is_worth_testing(category):
    a, b = pick_looks(category)
    assert a != b
    assert _axis_distance(a, b) >= MIN_AXIS_DISTANCE


# A (category, tone) pair that lands on each look, so every branch is exercised.
# street_ugc and studio_pop are never reached from a category: street_ugc is
# reserved for proven-performance routes, studio_pop for unknown products.
BRIEF_FOR_LOOK = {
    "clinical_lab": ("skincare", ""),
    "warm_home": ("cà phê", ""),
    "dark_luxe": ("điện tử", ""),
    "fresh_market": ("F&B", ""),
    "street_ugc": ("", "authentic, real people, unboxing"),
    "studio_pop": ("", ""),
}


@pytest.mark.parametrize("primary", sorted(LOOKS))
def test_each_look_is_actually_reachable(primary):
    category, tone = BRIEF_FOR_LOOK[primary]
    assert pick_looks(category, tone)[0] == primary


@pytest.mark.parametrize("primary", sorted(LOOKS))
def test_the_forced_ugc_pair_is_still_far_enough_apart(primary):
    """Past performance overrides the category, but never the contrast rule."""
    category, tone = BRIEF_FOR_LOOK[primary]
    a, b = pick_looks(category, tone, winning_route="testimonial_ugc")
    assert "street_ugc" in (a, b)
    assert _axis_distance(a, b) >= MIN_AXIS_DISTANCE


def test_tone_chooses_the_look_when_the_category_is_unrecognised():
    """Brand 03 arrives as bare photographs with no brief at all, so the only
    words the studio has to go on are the ones vision reads off the packaging."""
    assert pick_looks("", "cao cấp, tinh tế")[0] == "dark_luxe"
    assert pick_looks("", "tươi, thiên nhiên")[0] == "fresh_market"
    assert pick_looks("", "")[0] == "studio_pop"


def test_no_preferred_pairing_is_a_near_twin():
    """dark_luxe and studio_pop share contrast and surface - one axis apart is
    not a test, it is the same photo with a different bulb."""
    for primary, partner in CONTRAST_PARTNERS.items():
        assert _axis_distance(primary, partner) >= MIN_AXIS_DISTANCE, (
            f"{primary} + {partner} differ on only "
            f"{_axis_distance(primary, partner)} axis"
        )


def test_contrast_partners_reference_real_looks():
    for primary, partner in CONTRAST_PARTNERS.items():
        assert primary in LOOKS and partner in LOOKS
        assert primary != partner


# ---------------------------------------------------------------------------
# Platform kits
# ---------------------------------------------------------------------------

def test_both_demo_kits_exist_and_cover_the_bp01_minimum():
    assert set(KITS) >= {Platform.TIKTOK_SHOP, Platform.SHOPEE}
    kinds = {s.kind for kit in KITS.values() for s in kit.slots}
    assert {ImageKind.HERO, ImageKind.SKU_DETAIL,
            ImageKind.COLLECTION, ImageKind.THUMBNAIL} <= kinds


def test_shopee_main_image_demands_a_white_background_and_prefers_a_real_photo():
    """Marketplace rule, and the slot where an invented pixel costs a return."""
    main = next(s for s in KITS[Platform.SHOPEE].slots if s.id == "shopee_main")
    assert main.rule == "pure_white_bg"
    assert main.prefer_origin.value == "reuse"


def test_the_kits_together_produce_enough_images_for_qa():
    """qa_review_agent blocks a bundle with fewer than MIN_PRODUCT_IMAGES."""
    total = sum(len(kit.slots) for kit in KITS.values())
    assert total >= qa_review_agent.MIN_PRODUCT_IMAGES


def test_slot_ids_are_unique_across_every_kit():
    ids = [s.id for kit in KITS.values() for s in kit.slots]
    assert len(ids) == len(set(ids))


def test_every_slot_size_key_names_a_real_setting():
    """size_key is read with getattr on studio_settings, so a typo would only
    surface at render time, several minutes into a run."""
    for kit in KITS.values():
        for slot in kit.slots:
            assert hasattr(studio_settings, slot.size_key), slot.size_key
            assert "x" in getattr(studio_settings, slot.size_key)


def test_tiktok_is_video_first_and_shopee_is_photo_first():
    """The two kits exist to be different. If this fails, one of them has drifted
    into being the other one resized."""
    tiktok = KITS[Platform.TIKTOK_SHOP]
    shopee = KITS[Platform.SHOPEE]

    # TikTok carries the full storyboard; Shopee's clip is a gallery loop.
    assert max(v.shots for v in tiktok.video_slots) == len(SHOT_TEMPLATES)
    assert any(v.voiceover for v in tiktok.video_slots)
    assert not any(v.voiceover for v in shopee.video_slots)

    # Most TikTok stills carry words; most Shopee stills carry none.
    tiktok_with_text = [s for s in tiktok.slots if s.text_keys]
    assert len(tiktok_with_text) > len(tiktok.slots) / 2

    # Shopee leans on the brand's own photographs.
    shopee_reuse = [s for s in shopee.slots if s.prefer_origin is AssetOrigin.REUSE]
    assert len(shopee_reuse) >= 2


def test_every_kit_states_its_hard_rules():
    for platform, kit in KITS.items():
        assert kit.hard_rules, f"{platform.value} has no hard rules"
        assert all(rule.strip() for rule in kit.hard_rules)


# ---------------------------------------------------------------------------
# Scenes and storyboard
# ---------------------------------------------------------------------------

def test_every_slot_scene_template_resolves():
    for slot_id, tpl in SLOT_SCENES.items():
        rendered = tpl.format(surface="stone", light="soft light")
        assert "{" not in rendered, f"{slot_id} has an unfilled placeholder"


def test_scene_keys_and_slot_ids_are_the_same_set():
    """direct.py looks a scene up by slot id. A slot with no scene renders an
    empty frame; a scene with no slot is dead text nobody will ever see."""
    slot_ids = {s.id for kit in KITS.values() for s in kit.slots}
    assert set(SLOT_SCENES) == slot_ids


def test_shopee_main_scene_ignores_the_route_look():
    """The marketplace rule overrides the art direction in this one slot: pure
    white seamless, whatever the route looks like everywhere else."""
    scene = SLOT_SCENES["shopee_main"]
    assert "{surface}" not in scene and "{light}" not in scene
    assert "pure white" in scene


def test_every_other_scene_inherits_the_route_look():
    """Consistency across a kit comes from every frame sharing one surface and
    one light, so a scene that hardcodes its own has opted out of the shoot."""
    for slot_id, scene in SLOT_SCENES.items():
        if slot_id == "shopee_main":
            continue
        assert "{surface}" in scene and "{light}" in scene, slot_id


def test_storyboard_is_hook_product_benefit_cta():
    assert [s.role for s in SHOT_TEMPLATES] == ["hook", "product", "benefit", "cta"]
    assert sum(s.seconds for s in SHOT_TEMPLATES) >= 15   # qa_review_agent's floor


def test_storyboard_fits_inside_the_qa_duration_window():
    """Too short is a blocker's worth of warnings; too long and the QA agent
    flags every video the studio makes."""
    total = sum(s.seconds for s in SHOT_TEMPLATES)
    assert qa_review_agent.VIDEO_MIN_DURATION_SEC <= total <= qa_review_agent.VIDEO_MAX_DURATION_SEC


def test_every_shot_is_a_length_the_video_model_accepts():
    """Seedance takes 4 to 15 seconds per clip."""
    for shot in SHOT_TEMPLATES:
        assert 4 <= shot.seconds <= 15, shot.role


def test_every_text_key_is_in_the_vocabulary():
    """Slots and shots name their strings; direct.py resolves those names against
    the brief. A key that exists in only one of the two files renders nothing."""
    used = {k for kit in KITS.values() for s in kit.slots for k in s.text_keys}
    used |= {s.text_key for s in SHOT_TEMPLATES}
    assert used <= set(TEXT_KEYS), sorted(used - set(TEXT_KEYS))


def test_every_shot_names_where_its_scene_comes_from():
    known_sources = {
        "consumer_pain_point", "product_photo", "key_selling_points[0]", "promotion",
    }
    assert {s.scene_from for s in SHOT_TEMPLATES} <= known_sources
