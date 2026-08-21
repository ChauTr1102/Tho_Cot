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
    CAMERA_LOCKED,
    FRAMING_CONSTRAINT_LOCKED,
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
# Motion
# ---------------------------------------------------------------------------
# The video prompt used to offer a push-in or a locked camera and nothing else,
# so a four-beat ad was the same move four times. These tests pin the two
# properties that matter: motion is chosen by the beat, and a frame carrying
# copy still gets motion - just none that can move a frame edge.

def _line(prompt: str, head: str) -> str:
    return next(ln for ln in prompt.splitlines() if ln.startswith(f"{head}:"))


def test_each_beat_gets_its_own_camera_move():
    """A hook arrives, a product beat orbits, a benefit beat racks focus, a cta
    settles. Four identical push-ins is one shot repeated four times."""
    moves = {
        role: _line(build_video_prompt("the bottle on stone", SPINE, role=role), "CAMERA")
        for role in ("hook", "product", "benefit", "cta")
    }
    assert len(set(moves.values())) == 4, moves


def test_the_unlocked_path_uses_real_product_film_vocabulary():
    joined = " ".join(
        build_video_prompt("the bottle on stone", SPINE, role=role).casefold()
        for role in ("hook", "product", "benefit", "cta")
    )
    for term in ("dolly", "orbit", "rack focus", "slider", "pour", "splash"):
        assert term in joined, f"no {term!r} anywhere in the unlocked motion"


def test_one_camera_instruction_per_clip():
    """BytePlus's own guide: never stack push-in plus pan plus zoom plus orbit.
    Each beat's CAMERA line names exactly one move."""
    moves = ("dolly-in", "dolly-out", "orbit", "slider move", "pan", "tilt", "zoom")
    for role in ("hook", "product", "benefit", "cta"):
        camera = _line(build_video_prompt("the bottle on stone", SPINE, role=role), "CAMERA")
        named = [m for m in moves if m in camera.casefold()]
        assert len(named) == 1, f"{role} stacks camera moves: {named}"


@pytest.mark.parametrize("role", ["hook", "product", "benefit", "cta"])
def test_a_keyframe_with_copy_gets_a_locked_camera_whatever_the_beat(role):
    """The one setting here that is not taste. Measured: a push-in carried
    "PHỤC HỒI HÀNG RÀO DA" out of a real 9:16 keyframe."""
    p = build_video_prompt("the bottle on stone", SPINE, has_onscreen_text=True, role=role)
    assert _line(p, "CAMERA") == f"CAMERA: {CAMERA_LOCKED}"
    assert FRAMING_CONSTRAINT_LOCKED.strip() in p


@pytest.mark.parametrize("role", ["hook", "product", "benefit", "cta"])
def test_the_locked_path_still_moves_but_never_moves_the_camera(role):
    """Locked is not still. Everything below animates the scene while all four
    frame edges stay exactly where they were."""
    p = build_video_prompt("the bottle on stone", SPINE, has_onscreen_text=True, role=role)
    action = _line(p, "ACTION").casefold()
    cinemagraph = (
        "light", "highlight", "glint", "steam", "dust", "condensation", "liquid",
        "settl", "ripple", "shimmer", "drift", "reflection", "pour",
    )
    assert any(word in action for word in cinemagraph), action
    for reframing in ("dolly", "orbit", "pan ", "tilt ", "zoom", "push-in", "pull back"):
        assert reframing not in action, f"{role} locked action reframes: {reframing!r}"


def test_locked_beats_still_differ_from_each_other():
    actions = {
        role: _line(build_video_prompt("x on stone", SPINE, has_onscreen_text=True, role=role),
                    "ACTION")
        for role in ("hook", "product", "benefit", "cta")
    }
    assert len(set(actions.values())) == 4, actions


def test_the_role_is_inferred_from_the_staging_when_the_caller_omits_it():
    """`motion.render_shot` does not yet pass the role. Until it does, the beat
    is read off `direct.SHOT_SCENES`, so the storyboard still gets four
    different moves instead of four copies of the default."""
    promo = build_video_prompt(
        "the product on stone beside a clean rectangular offer card", SPINE)
    benefit = build_video_prompt("an extreme macro of the product's texture on stone", SPINE)
    hook = build_video_prompt(
        "a close portrait of the target customer in front of a bathroom mirror", SPINE)
    assert _line(promo, "CAMERA") != _line(benefit, "CAMERA") != _line(hook, "CAMERA")
    assert "rack focus" in benefit


def test_apertures_never_reach_seedance():
    """Seedream reads "at f/8" as an instruction; the Seedance guide asks for
    framing and warns off exposure jargon. One look library, two dialects."""
    spine = StyleSpine(look_key="x", lens="100mm macro at f/8, focus-stacked so the label stays "
                                          "sharp corner to corner",
                       light="a key from back-left", surface="a sweep", grade="low contrast",
                       palette=["#FFF"])
    p = build_video_prompt("the bottle on stone", spine)
    assert "f/8" not in p
    assert "focus-stacked" not in p
    assert "100mm macro" in p          # what Seedance can actually act on survives


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
