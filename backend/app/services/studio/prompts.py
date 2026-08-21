"""
The prompt assembler - where the studio's golden rule is enforced.

The rule is one sentence: **never leave a gap for the model to fill.**

It comes from measurement, not taste. Seedream 5.0 Pro renders any string it is
handed with complete accuracy, including the hardest Vietnamese stacked
diacritics - `PHỤC HỒI HÀNG RÀO DA`, `Ễ`, `Ậ`, `Ể` all came back perfect. Every
string it was left to invent came back broken: `LUNAÁIRA` for a brand name,
`EFFFECTIVE` for an English word. The failure axis is *specified versus
invented*, not Vietnamese versus English. So the TEXT block enumerates every
string that will appear in the frame - the headline, the badge, and the
product's own label - and when a slot carries no marketing copy at all it says
so out loud rather than leaving the section blank.

An image prompt is six blocks, always in this order:

    SUBJECT   what the product is, and that it must not change
    SCENE     the staging for this one slot
    TEXT      every string in the frame, quoted
    STYLE     the route's look, word for word
    FORMAT    shape, plus any marketplace rule that overrides the look
    NEGATIVE  what must not appear

SUBJECT, STYLE and NEGATIVE are byte-identical for every asset in a route, and
FORMAT is identical for every asset of the same shape. Only SCENE and TEXT move.
That invariance *is* the consistency mechanism: it is why eight images read as
one photoshoot instead of eight unrelated pictures. Do not "improve" it by
rewording a block per slot.

The video prompt is a different animal. Seedance 2.5 cannot spell Vietnamese -
asked for *"Da khô căng, xỉn màu?"* it drew *"Da khò cáng, xỉn mau?"* - so it is
never asked to draw anything. Every legible string is baked into the Seedream
keyframe, which survives image-to-video intact, and the video prompt describes
motion and camera only.

That is a narrower job, not a poorer one. It follows BytePlus's own formula -
Subject, Action, Camera Language, Style, Constraints - and its two rules for
image-to-video: exactly one camera instruction per clip, and describe the
*change* rather than the scene the first frame already shows. The move is chosen
by the beat's role, and when the keyframe carries copy the camera locks off and
the scene moves instead, cinemagraph-style.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterable, Sequence

if TYPE_CHECKING:  # pragma: no cover - import for type checkers only
    from app.services.studio.direct import StyleSpine


# ---------------------------------------------------------------------------
# The image prompt
# ---------------------------------------------------------------------------
# Six blocks, fixed order. Rewriting the wording here changes every image the
# studio produces, so change it in one place and look at the whole kit after.

IMAGE_PROMPT = """SUBJECT: The product from reference image 1, exactly unchanged - same shape, \
same cap, same label artwork and the same proportions, with the label turned towards the camera \
so every character printed on it stays legible. Do not restyle, redesign or re-letter the product.

SCENE: {scene}

TEXT - render exactly these strings and nothing else:
{text_lines}

STYLE: {lens}, {light}, {grade}, palette {palette}

FORMAT: {ratio}, e-commerce ready{rule_clause}

NEGATIVE: no invented brand name, no invented tagline, no text beyond the list above, \
no watermark, no distorted or doubled lettering, no misspelling of any string listed above, \
no softbox, scrim, reflector, bounce card, flag or light stand visible in the frame, \
no flat colour band, border or panel across the photograph."""


# A bullet in the TEXT block. The phrase "reading exactly" is load-bearing: it is
# the wording that was verified to produce character-perfect Vietnamese.
TEXT_LINE = '  · {role} text reading exactly "{value}"'

# The product's own packaging is text too, and the model redraws it whether or
# not we mention it. Naming it is the only defence against the measured failure
# where a real COSRX bottle came back reading `COSRᴀ` on its vertical wordmark.
LABEL_LINE = "  · the product label reading exactly {values}"

# Closing lines. One of these always appears, so the block is never a gap.
NO_OTHER_TEXT_LINE = "  · no other text anywhere in the frame"
NO_TEXT_LINE = "  · no text anywhere in the image"

# Used when a brief carries no brand colours - never leave the palette blank.
DEFAULT_PALETTE = "the product's own colours"


# ---------------------------------------------------------------------------
# Marketplace rules
# ---------------------------------------------------------------------------
# A rule outranks the art direction. Shopee will take a listing down over a
# coloured main image; nobody has ever been taken down for a consistent kit.
# The clause is appended to FORMAT, the block that is otherwise pure geometry.

RULE_CLAUSES: dict[str, str] = {
    "pure_white_bg": (
        ", pure white background (#FFFFFF), seamless, with a soft contact shadow under the "
        "product and nothing else in the frame - this marketplace rule overrides the art "
        "direction above"
    ),
}


# ---------------------------------------------------------------------------
# The video prompt
# ---------------------------------------------------------------------------
# BytePlus's formula is Subject + Action + Camera Language + Style + Audio +
# Constraints, and its own guide adds two rules this block obeys: give a clip
# exactly ONE primary camera instruction (never push-in plus pan plus orbit),
# and, for image-to-video, describe the *change* rather than re-describing a
# scene the first frame already shows. So ACTION leads with what moves.
#
# The audio block is omitted on purpose: the voiceover is spoken by Seed Audio
# TTS, which was verified to pronounce Vietnamese correctly, and Seedance's own
# audio comes from the same model that mangled the captions.

VIDEO_PROMPT = """SUBJECT: the product shown in the first frame, unchanged and in focus, \
its packaging and every character already printed on it exactly as they are
ACTION: {action}; the rest of the scene holds exactly as the first frame shows it - {shot_scene}
CAMERA: {camera}
STYLE: {lens}, {light}, {surface}, {grade}, unchanged from the first frame
CONSTRAINTS: one continuous take, no cuts, one camera instruction only. Preserve the first \
frame's composition and every string already printed in it. {framing_constraint}\
Do not add any text, caption, lettering, overlay or watermark of any kind."""


# --- the locked path -------------------------------------------------------
# When Seedream has drawn copy into the frame the camera must hold its framing.
# This is measured, not cautious: on a real 9:16 keyframe whose headline sat in
# the top third, a push-in carried "PHỤC HỒI HÀNG RÀO DA" straight out of shot,
# while the Ken Burns fallback beat, which only pans, kept it. Losing the
# headline costs more than gaining the movement.
#
# Locked does not mean still, though. A cinemagraph moves everything except the
# camera, and every one of the motions below leaves all four frame edges exactly
# where they were: light travelling, reflections sliding, steam and dust
# drifting, condensation forming, liquid settling, bokeh shimmering.

CAMERA_LOCKED = (
    "locked-off static camera on a tripod - no dolly, no pan, no tilt, no zoom, no orbit, "
    "no parallax and no reframing of any kind; only what is inside the scene moves"
)
FRAMING_CONSTRAINT_LOCKED = (
    "Every edge of the first frame must still be visible in the last: do not zoom in, crop, "
    "pan away from or push past any text near the frame edges, and do not let the background "
    "slide, crawl or jitter behind the type. "
)

# What moves while the camera does not, chosen by the beat's role. Nothing here
# can travel across the type: no element enters or leaves the frame.
MOTION_LOCKED: dict[str, str] = {
    # Beat 1. The light itself becomes the event - a cloud crossing the key.
    "hook": (
        "the key light shifts as though a cloud crossed it and the shadow edges creep a few "
        "degrees, fine dust drifting through the beam"
    ),
    # Beat 2. The object is the subject, so the highlight does the work.
    "product": (
        "a specular highlight travels slowly across the product's face, a bead of condensation "
        "forms and runs, and the background bokeh shimmers behind it"
    ),
    # Beat 3. The reason to believe is the material, so the material moves.
    "benefit": (
        "the product's own material moves in place - liquid settling and rippling, a slow pour "
        "continuing, grain or powder drifting down through the frame"
    ),
    # Beat 4. One glint, then stillness: the eye should end on the offer.
    "cta": (
        "a single bright glint sweeps once across the offer card and the product's edge while "
        "the background darkens a little to lift them forward"
    ),
}
MOTION_LOCKED_DEFAULT = (
    "the light travels slowly across the surface, reflections slide, steam and fine dust drift "
    "through the beam, and a bead of condensation forms and runs"
)


# --- the unlocked path -----------------------------------------------------
# No copy in the frame, so the camera is free. One move per clip, chosen by the
# beat's role: a hook wants to arrive, a product beat wants to show the object
# in the round, a benefit beat wants to land on the label, and a call to action
# wants to settle rather than to keep travelling.

CAMERA_MOVES: dict[str, str] = {
    "hook": "a slow dolly-in from a wide framing to a medium shot, with a trace of handheld drift",
    "product": (
        "a slow quarter orbit around the product on a motion-control arc, the specular highlight "
        "travelling along its edge as the camera passes"
    ),
    "benefit": (
        "a short macro slider move along the surface ending in a rack focus, the foreground going "
        "soft as the label snaps sharp"
    ),
    "cta": (
        "a slow dolly-out that eases to a stop, holding the product and the offer together in the "
        "final frame"
    ),
}
CAMERA_PUSH_IN = "a slow dolly-in, the product held sharp and centred"

# What the scene does while the camera moves. Freer than the locked table -
# an element may enter or leave the frame, because there is no type to protect.
MOTION_UNLOCKED: dict[str, str] = {
    "hook": (
        "the product's own material enters in slow motion - a pour arcing in, a splash rising or "
        "an ingredient falling past the lens - while steam and dust drift through the light"
    ),
    "product": (
        "a specular highlight sweeps the length of the product as the camera passes, condensation "
        "beading across its surface"
    ),
    "benefit": (
        "the material moves in close-up: liquid ripples and settles, a slow pour continues, grain "
        "or powder falls through the beam"
    ),
    "cta": (
        "a glint sweeps across the offer and the product's edge as the last drops of the pour "
        "settle into stillness"
    ),
}
MOTION_UNLOCKED_DEFAULT = (
    "the product's own material moves through the light - a pour, a drift of steam, a scatter of "
    "its raw ingredient - while the light sweeps across the surface"
)


# --- role inference --------------------------------------------------------
# `build_video_prompt` takes the beat's role explicitly, which is what callers
# should pass. When they do not, the role is read off the staging sentence:
# `direct.SHOT_SCENES` gives each beat a distinctive subject, and these four
# markers separate them cleanly. Order matters - the offer card test runs before
# the macro test, because a promo beat can also be shot close.
ROLE_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cta", ("offer card", "promotion", "offer")),
    ("benefit", ("macro", "texture", "close-up", "cross-section")),
    ("hook", ("portrait", "expression", "mirror", "customer")),
)
DEFAULT_ROLE = "product"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_scene(scene: str, spine: "StyleSpine") -> str:
    """Fill a scene template's `{surface}` and `{light}` from the route's look.

    Scene templates in `slots.SLOT_SCENES` are deliberately incomplete so that
    the same staging can be shot in two different rooms for routes A and B.
    Those two names are the only placeholders allowed; anything else is a typo
    in the data table and is reported as one rather than reaching the API.

    Calling this on an already-resolved scene is a no-op, so it is safe for
    `direct.py` to resolve early and for this module to resolve again.
    """
    try:
        return scene.format(surface=spine.surface, light=spine.light)
    except (KeyError, IndexError) as exc:  # unknown or positional placeholder
        raise ValueError(
            f"scene template has an unsupported placeholder {exc}: "
            f"only {{surface}} and {{light}} are allowed - {scene!r}"
        ) from exc


def _text_lines(texts: Sequence[tuple[str, str]], label_text: Sequence[str]) -> str:
    """Build the TEXT block's bullet list.

    Every string that will appear in the frame gets a line, and the list always
    ends with an explicit statement that there is nothing else - an empty
    section is an invitation for the model to invent a tagline, and invented
    text is the one thing this model reliably gets wrong.
    """
    lines = [
        TEXT_LINE.format(role=role, value=value)
        for role, value in texts
        if str(value).strip()
    ]

    labels = [str(value).strip() for value in label_text if str(value).strip()]
    if labels:
        lines.append(LABEL_LINE.format(values=", ".join(f'"{v}"' for v in labels)))

    if not lines:
        return NO_TEXT_LINE
    lines.append(NO_OTHER_TEXT_LINE)
    return "\n".join(lines)


def _rule_clause(rule: str | None) -> str:
    """Turn a `SlotSpec.rule` id into the sentence appended to the FORMAT block.

    An unrecognised rule is passed through in readable form rather than dropped:
    a rule that silently disappears is how a listing gets taken down.
    """
    if not rule:
        return ""
    known = RULE_CLAUSES.get(rule)
    if known:
        return known
    return f", {rule.replace('_', ' ')}"


def _strip_quotes(text: str) -> str:
    """Remove double quotes from a video prompt fragment.

    Seedance treats text in double quotes as dialogue to be spoken. A quoted
    string that leaks into the prompt therefore becomes audio nobody asked for.
    """
    for quote in ('"', "“", "”"):
        text = text.replace(quote, "")
    return text


# Photographic technical notation, which belongs in an image prompt and not in
# a video one: BytePlus's Seedance guide asks for shot size, angle and movement
# and explicitly warns against f-stops and exposure jargon, while Seedream reads
# "at f/2.8" as a real instruction. The looks therefore carry apertures and the
# video prompt drops them, so one library can serve both models.
_APERTURE_RE = re.compile(r"\s*(?:,\s*)?\bat\s+f/[\d.]+|\s*,?\s*\bf/[\d.]+", re.IGNORECASE)
_FOCUS_STACK_RE = re.compile(r",?\s*focus[- ]stacked[^,]*", re.IGNORECASE)


def _video_lens(lens: str) -> str:
    """Strip aperture and focus-stacking notation from a look's lens for video.

    Seedance is asked for framing, not exposure. What survives is the part it
    can act on - the focal length, the angle and the sense of depth.
    """
    cleaned = _FOCUS_STACK_RE.sub("", _APERTURE_RE.sub("", lens or ""))
    return " ".join(cleaned.replace(" ,", ",").split()).strip(" ,")


def _role_for(role: str, shot_scene: str) -> str:
    """Return the storyboard role driving this shot's motion.

    An explicit `role` always wins. Without one the role is inferred from the
    staging sentence, so a caller that has not been widened to pass it still
    gets beat-appropriate motion instead of the same move four times.
    """
    role = (role or "").strip().casefold()
    if role in MOTION_LOCKED:
        return role

    haystack = (shot_scene or "").casefold()
    for candidate, markers in ROLE_MARKERS:
        if any(marker in haystack for marker in markers):
            return candidate
    return DEFAULT_ROLE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_image_prompt(
    scene: str,
    spine: "StyleSpine",
    texts: Sequence[tuple[str, str]],
    label_text: Sequence[str],
    ratio: str,
    rule: str | None = None,
) -> str:
    """Assemble the six-block prompt for one still image (Seedream 5.0 Pro).

    scene       the slot's staging sentence, with or without `{surface}` and
                `{light}` still in it - both are resolved here from the spine.
    spine       the route's look. Its wording is injected verbatim, and
                identically, into every image of the route.
    texts       `(role, string)` pairs, in reading order. Every one of them is
                quoted into the TEXT block. Callers must have filtered these
                against `forbidden_claims` already - `direct.build_worksheet`
                does, and nothing else should be assembling this list.
    label_text  the strings printed on the product's own packaging. Naming them
                is what stops the model re-lettering the brand name.
    ratio       the frame shape, e.g. "1:1" or "9:16".
    rule        a marketplace rule id that outranks the art direction, e.g.
                "pure_white_bg".

    Returns a prompt with no unresolved placeholder in it.
    """
    palette = ", ".join(p for p in spine.palette if str(p).strip()) or DEFAULT_PALETTE
    return IMAGE_PROMPT.format(
        scene=resolve_scene(scene, spine),
        text_lines=_text_lines(texts, label_text),
        lens=spine.lens,
        light=spine.light,
        grade=spine.grade,
        palette=palette,
        ratio=ratio,
        rule_clause=_rule_clause(rule),
    )


def build_video_prompt(
    shot_scene: str,
    spine: "StyleSpine",
    vo_text: str = "",
    has_onscreen_text: bool = False,
    role: str = "",
) -> str:
    """Assemble the motion prompt for one shot (Seedance 2.5, image-to-video).

    The prompt describes **motion and camera only**. Everything the viewer
    reads already exists in the first frame, drawn by Seedream, and text baked
    into a first frame was verified to survive the whole clip with its
    diacritics and kerning intact.

    `role` is the storyboard beat - hook, product, benefit or cta - and it picks
    the move. A hook arrives, a product beat orbits, a benefit beat racks focus
    onto the label, a call to action settles; four beats that all push in read
    as one shot repeated. When the caller does not supply a role it is inferred
    from the staging sentence.

    `has_onscreen_text` switches the whole camera behaviour and is the one
    setting here that is not taste. A keyframe carrying copy gets a locked-off
    camera, because a push-in measured on a real 9:16 keyframe carried the
    headline straight out of frame. Locked is not still: the scene keeps a
    cinemagraph's worth of motion - light travelling, steam and dust drifting,
    condensation forming, liquid settling - none of which can move a frame edge.

    `vo_text` is accepted so a caller can carry the spoken line alongside the
    shot and forward it to TTS. It is deliberately **never written into the
    prompt**: asked to caption Vietnamese, Seedance turned "Da khô căng, xỉn
    màu?" into "Da khò cáng, xỉn mau?". The CONSTRAINTS block instead forbids
    the model from adding any lettering at all.
    """
    del vo_text  # spoken by Seed Audio TTS; never drawn by Seedance
    beat = _role_for(role, shot_scene)

    if has_onscreen_text:
        action = MOTION_LOCKED.get(beat, MOTION_LOCKED_DEFAULT)
        camera = CAMERA_LOCKED
    else:
        action = MOTION_UNLOCKED.get(beat, MOTION_UNLOCKED_DEFAULT)
        camera = CAMERA_MOVES.get(beat, CAMERA_PUSH_IN)

    return VIDEO_PROMPT.format(
        action=action,
        shot_scene=_strip_quotes(resolve_scene(shot_scene, spine)),
        camera=camera,
        framing_constraint=FRAMING_CONSTRAINT_LOCKED if has_onscreen_text else "",
        lens=_video_lens(spine.lens),
        light=spine.light,
        surface=spine.surface,
        grade=spine.grade,
    )


def describe_prompt_blocks(prompt: str) -> Iterable[str]:
    """Split an assembled prompt back into its blocks, for logging and the UI.

    Useful when a render comes back wrong: the first question is always which
    block failed to reach the model.
    """
    return [block for block in prompt.split("\n\n") if block.strip()]
