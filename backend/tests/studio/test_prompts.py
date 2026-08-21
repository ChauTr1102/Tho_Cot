"""
The prompt assembler is where the golden rule lives: every string that appears
in the frame must be named.

Research on 21/08 showed the failure axis is *specified versus invented*, not
Vietnamese versus English. Named strings render perfectly, including stacked
diacritics (`PHỤC HỒI HÀNG RÀO DA`); strings the model chooses for itself come
back as `LUNAÁIRA` and `EFFFECTIVE`. So these tests are less about wording than
about two properties: nothing is ever left unsaid, and the blocks that make a
kit look like one photoshoot stay byte-identical across it.
"""
import pytest

from app.services.studio.direct import StyleSpine
from app.services.studio.prompts import (
    build_image_prompt,
    build_video_prompt,
    describe_prompt_blocks,
)

SPINE = StyleSpine(look_key="clinical_lab", lens="85mm macro",
                   light="cool diffused softbox", surface="wet travertine",
                   grade="neutral, low contrast", palette=["#FFFFFF", "#00A19A"])


def test_every_named_string_appears_with_an_exactness_instruction():
    p = build_image_prompt(
        scene="the product on {surface}, {light}", spine=SPINE,
        texts=[("headline", "PHỤC HỒI HÀNG RÀO DA"), ("badge", "GIẢM 25%")],
        label_text=["COSRX", "100ml"], ratio="1:1", rule=None,
    )
    assert 'reading exactly "PHỤC HỒI HÀNG RÀO DA"' in p
    assert 'reading exactly "GIẢM 25%"' in p
    assert "COSRX" in p                       # the real label, so none is invented
    assert "no invented brand name" in p.lower()
    assert "{" not in p                       # every placeholder resolved


def test_style_block_carries_the_whole_spine():
    p = build_image_prompt(scene="a scene on {surface} with {light}", spine=SPINE,
                           texts=[], label_text=[], ratio="1:1", rule=None)
    for fragment in ("85mm macro", "cool diffused softbox", "wet travertine", "neutral, low contrast"):
        assert fragment in p


def test_white_background_rule_reaches_the_prompt():
    p = build_image_prompt(scene="the product centred", spine=SPINE, texts=[],
                           label_text=[], ratio="1:1", rule="pure_white_bg")
    assert "pure white background" in p.lower()


def test_video_prompt_never_asks_seedance_for_vietnamese_text():
    """Seedance mangles Vietnamese captions ("Da khò cáng, xỉn mau?"). All legible
    text is baked into the Seedream keyframe instead, where it renders correctly
    and survives image-to-video intact."""
    p = build_video_prompt(shot_scene="the bottle on wet stone", spine=SPINE,
                           vo_text="Da khô căng, xỉn màu?")
    assert "subtitle" not in p.lower()
    assert "Da khô căng" not in p              # the line is spoken by TTS, not drawn
    assert "do not add any text" in p.lower()  # explicit: keep the keyframe's text only


def test_video_prompt_carries_camera_and_style_but_preserves_the_frame():
    p = build_video_prompt(shot_scene="the bottle on wet stone", spine=SPINE, vo_text="")
    assert "85mm macro" in p
    assert "wet travertine" in p


# ---------------------------------------------------------------------------
# Never leave a gap
# ---------------------------------------------------------------------------

def test_a_frame_with_no_copy_still_says_so_explicitly():
    """An empty TEXT block is an invitation to invent a tagline, and an invented
    tagline is the one thing this model reliably gets wrong."""
    p = build_image_prompt(scene="the product centred", spine=SPINE, texts=[],
                           label_text=[], ratio="1:1", rule=None)
    assert "no text anywhere in the image" in p


def test_a_frame_with_only_a_label_forbids_everything_else():
    p = build_image_prompt(scene="the product centred", spine=SPINE, texts=[],
                           label_text=["COSRX", "100ml"], ratio="1:1", rule=None)
    assert 'the product label reading exactly "COSRX", "100ml"' in p
    assert "no other text anywhere in the frame" in p


def test_an_empty_palette_never_reaches_the_model_blank():
    bare = StyleSpine(look_key="x", lens="50mm", light="soft light",
                      surface="oak", grade="warm", palette=[])
    p = build_image_prompt(scene="the product on {surface}", spine=bare, texts=[],
                           label_text=[], ratio="1:1", rule=None)
    assert "palette the product's own colours" in p


def test_a_typo_in_a_scene_template_is_reported_not_shipped():
    """slots.py is edited by hand. A stray placeholder must fail loudly here
    rather than reach the API as a literal brace."""
    with pytest.raises(ValueError) as exc:
        build_image_prompt(scene="the product on {backdrop}", spine=SPINE, texts=[],
                           label_text=[], ratio="1:1", rule=None)
    assert "backdrop" in str(exc.value)


# ---------------------------------------------------------------------------
# The consistency mechanism
# ---------------------------------------------------------------------------

def test_six_blocks_in_a_fixed_order():
    p = build_image_prompt(scene="the product on {surface}", spine=SPINE,
                           texts=[("headline", "X")], label_text=["COSRX"],
                           ratio="9:16", rule=None)
    heads = [block.split(":", 1)[0].split(" -", 1)[0] for block in describe_prompt_blocks(p)]
    assert heads == ["SUBJECT", "SCENE", "TEXT", "STYLE", "FORMAT", "NEGATIVE"]


def test_subject_style_and_negative_are_byte_identical_across_a_route():
    """This invariance is the entire reason eight images look like one shoot.
    Only SCENE and TEXT are allowed to move between slots of the same route."""
    cover = build_image_prompt(scene="the product low on {surface}, {light}", spine=SPINE,
                               texts=[("headline", "PHỤC HỒI HÀNG RÀO DA")],
                               label_text=["COSRX"], ratio="9:16", rule=None)
    promo = build_image_prompt(scene="the product beside an offer card, {light}", spine=SPINE,
                               texts=[("badge", "GIẢM 25%")],
                               label_text=["COSRX"], ratio="9:16", rule=None)
    a, b = describe_prompt_blocks(cover), describe_prompt_blocks(promo)
    for index in (0, 3, 4, 5):        # SUBJECT, STYLE, FORMAT, NEGATIVE
        assert a[index] == b[index]
    for index in (1, 2):              # SCENE, TEXT
        assert a[index] != b[index]


def test_a_marketplace_rule_is_never_silently_dropped():
    """An unrecognised rule id still reaches the model in readable form: a rule
    that disappears quietly is how a listing gets taken down."""
    p = build_image_prompt(scene="the product centred", spine=SPINE, texts=[],
                           label_text=[], ratio="1:1", rule="no_people_in_frame")
    assert "no people in frame" in p


def test_quoted_text_never_reaches_seedance():
    """Seedance speaks anything it finds in double quotes. A quoted string that
    leaks into a motion prompt becomes audio nobody asked for."""
    p = build_video_prompt(shot_scene='a bottle beside a card reading "GIẢM 25%"',
                           spine=SPINE, vo_text="")
    assert '"' not in p
