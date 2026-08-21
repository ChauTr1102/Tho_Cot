"""These tables are the studio's taste. The tests guard the properties that make
the output usable rather than the exact wording, which the art director tunes.

Read a failure here as "the edit broke a promise the rest of the studio relies
on", not as "the edit was ugly". The promises are:
  * routes A and B stay visibly different from each other;
  * every slot named in one table exists in the others;
  * every placeholder resolves, and every text key is in the vocabulary;
  * the storyboard still fits the QA agent's duration window.
"""
import re

import pytest

from app.schemas.studio import AssetOrigin, ImageKind, Platform
from app.services.studio.config import studio_settings
from app.services.studio.looks import (
    AXES,
    CONTRAST_PARTNERS,
    LOOKS,
    MIN_AXIS_DISTANCE,
    pick_looks,
)
from app.services.studio.platforms import KITS
# BP-01's own minimums, quoted from the brief rather than imported. They used to
# come from `qa_review_agent`, which the team replaced with `verify_checklist`;
# tying this file to whichever module currently enforces them is what broke it.
#   "At least 4 generated product / marketplace images"
#   "15-30 seconds, 9:16 vertical format"
MIN_PRODUCT_IMAGES = 4
MIN_VIDEO_SECONDS = 15
MAX_VIDEO_SECONDS = 30

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


# ---------------------------------------------------------------------------
# Looks: the four fields have to be art direction, not adjectives
# ---------------------------------------------------------------------------
# These four tests exist because the first version of this library shipped
# "bright even daylight" on a "wooden board with fresh ingredients" and the
# product owner called the output ugly. The diagnosis was that every field was
# a mood word where it should have been an instruction, so the tests pin the
# shape of an instruction: a lens carries numbers, a light names equipment, a
# surface describes a set, and a grade names what happens to the tones.

@pytest.mark.parametrize("key", sorted(LOOKS))
def test_every_lens_names_a_focal_length_and_an_aperture(key):
    """The f-number is what actually moves the image; "shallow depth of field"
    is a wish. Both numbers must be there."""
    lens = LOOKS[key].lens
    assert re.search(r"\d+\s*mm", lens), f"{key}.lens has no focal length: {lens!r}"
    assert re.search(r"f/[\d.]+", lens), f"{key}.lens has no aperture: {lens!r}"


# The words a photographer writes on a lighting diagram. A light that names
# none of them is describing the weather, not a setup.
LIGHTING_EQUIPMENT = (
    "key", "fill", "rim", "kicker", "bounce", "flag", "scrim", "softbox", "grid",
    "gridded", "snoot", "snooted", "gobo", "cookie", "barn door", "diffusion",
    "clamshell", "negative fill", "flash", "strobe", "blind", "window", "gel",
    "gelled", "backlight", "edge light",
)


@pytest.mark.parametrize("key", sorted(LOOKS))
def test_every_light_describes_a_setup_not_a_weather_condition(key):
    light = LOOKS[key].light.casefold()
    named = [word for word in LIGHTING_EQUIPMENT if word in light]
    assert len(named) >= 3, f"{key}.light names only {named}: {LOOKS[key].light!r}"
    # A setup says where the light comes from, not merely that there is some.
    assert any(
        direction in light
        for direction in ("left", "right", "behind", "overhead", "above", "below", "back")
    ), f"{key}.light gives no direction: {LOOKS[key].light!r}"


@pytest.mark.parametrize("key", sorted(LOOKS))
def test_every_surface_describes_a_set_rather_than_a_noun(key):
    """"black stone" is a material; a set says what is on it and what has
    already happened there. Length is a crude proxy, but a two-word surface
    cannot possibly be a set."""
    surface = LOOKS[key].surface
    assert len(surface.split()) >= 12, f"{key}.surface is a noun, not a set: {surface!r}"
    assert surface.count(",") >= 2, f"{key}.surface lists no elements: {surface!r}"


@pytest.mark.parametrize("key", sorted(LOOKS))
def test_every_grade_names_what_happens_to_the_tones(key):
    grade = LOOKS[key].grade.casefold()
    vocabulary = (
        "black", "shadow", "highlight", "contrast", "saturation", "saturated",
        "grain", "tone", "halation", "white balance", "cast", "key",
    )
    named = [word for word in vocabulary if word in grade]
    assert len(named) >= 3, f"{key}.grade names only {named}: {LOOKS[key].grade!r}"


def test_no_two_looks_share_a_light_or_a_surface():
    """Six presets that differ only in wording are one preset with six names."""
    for field in ("light", "surface", "grade", "lens"):
        values = [getattr(look, field) for look in LOOKS.values()]
        assert len(set(values)) == len(values), f"two looks share a {field}"


def test_lighting_hardware_is_always_placed_out_of_frame():
    """Measured: "a white bounce card camera-right" put a literal white board in
    the picture and "a black flag opposite" hung a black cloth behind the
    product. Naming the modifier is right; forgetting to say it is off camera
    is how grip equipment ends up in a campaign image."""
    for key, look in LOOKS.items():
        light = look.light.casefold()
        for hardware in ("bounce card", "black flag", "black flags", "bounce below"):
            if hardware in light:
                assert "out of frame" in light, (
                    f"{key}.light names {hardware!r} without placing it out of frame"
                )


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
    assert total >= MIN_PRODUCT_IMAGES


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


# The three slots a shopper studies before paying. They are deliberately
# propless and eventless: the buyer is checking the object matches the parcel,
# and staging is exactly what makes a listing image untrustworthy.
INSPECTION_SLOTS = {"shopee_main", "tiktok_product"}


def test_every_staged_scene_names_a_composition_and_an_event():
    """A location is not a picture. "three products arranged on a board" says
    where they are; "three in a tight overlapping row, the nearest turned
    three-quarters, a ribbon of milk frozen mid-pour between them" says what the
    photograph looks like. Every scene but the inspection ones must do both."""
    composition = (
        "angle", "row", "overlapping", "three-quarters", "foreground", "bokeh",
        "frame", "third", "half", "close", "macro", "behind", "lower", "left",
    )
    event = (
        "pour", "splash", "steam", "falling", "mid-motion", "in motion", "frozen",
        "arcs", "scatter", "running", "raking", "drift", "beading", "spill",
    )
    for slot_id, scene in SLOT_SCENES.items():
        low = scene.casefold()
        assert any(word in low for word in composition), f"{slot_id} states no composition"
        if slot_id in INSPECTION_SLOTS:
            continue
        assert any(word in low for word in event), f"{slot_id} stages no event"


def test_every_scene_that_carries_copy_reserves_the_space_for_it():
    """Measured, and the most expensive failure in this file. The same headline
    that rendered correctly over a frame whose scene reserved "generous empty
    space in the top third" vanished completely from a busier frame whose scene
    did not. Any slot with text_keys must say out loud where the type goes."""
    text_slots = [s for kit in KITS.values() for s in kit.slots if s.text_keys]
    assert text_slots, "no slot carries copy - this test is guarding nothing"
    for slot in text_slots:
        scene = SLOT_SCENES[slot.id].casefold()
        assert "empty" in scene, f"{slot.id} carries copy but reserves no space for it"


def test_no_scene_asks_for_a_flat_colour_band_behind_the_type():
    """The first attempt at reserving space said "flat negative space", and the
    model answered with a literal white band across the top of four images out
    of six - a template, not a photograph. The scenes now ask for a full-bleed
    photograph and say so."""
    for slot_id, scene in SLOT_SCENES.items():
        if slot_id == "shopee_main":
            continue
        assert "flat negative space" not in scene.casefold(), slot_id


def test_shopee_main_stays_the_plain_one():
    """Marketplace listing image, not a campaign frame. It is the only slot the
    art direction does not reach, and making it cinematic is a takedown risk."""
    scene = SLOT_SCENES["shopee_main"].casefold()
    for cinematic in ("bokeh", "gobo", "raking", "splash", "mid-motion", "hero angle",
                      "rim", "smoke", "dramatic"):
        assert cinematic not in scene, f"shopee_main has gone cinematic: {cinematic!r}"


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
    assert sum(s.seconds for s in SHOT_TEMPLATES) >= 15   # BP-01's floor


def test_storyboard_fits_inside_the_qa_duration_window():
    """Too short is a blocker's worth of warnings; too long and the QA agent
    flags every video the studio makes."""
    total = sum(s.seconds for s in SHOT_TEMPLATES)
    assert MIN_VIDEO_SECONDS <= total <= MAX_VIDEO_SECONDS


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
