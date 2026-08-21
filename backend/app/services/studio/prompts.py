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

The video prompt is a different animal and deliberately much poorer. Seedance
2.5 cannot spell Vietnamese - asked for *"Da khô căng, xỉn màu?"* it drew
*"Da khò cáng, xỉn mau?"* - so it is never asked to draw anything. Every legible
string is baked into the Seedream keyframe, which survives image-to-video
intact, and the video prompt describes motion and camera only.
"""
from __future__ import annotations

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
no watermark, no distorted or doubled lettering, no misspelling of any string listed above."""


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
# BytePlus's formula is Subject + Action + Camera + Style + Constraints. The
# audio block is omitted on purpose: the voiceover is spoken by Seed Audio TTS,
# which was verified to pronounce Vietnamese correctly, and Seedance's own audio
# is produced by the same model that mangled the captions.

VIDEO_PROMPT = """SUBJECT: the product shown in the first frame, unchanged and in focus
ACTION + CAMERA: {shot_scene}, slow push-in, the product stays sharp and centred
STYLE: {lens}, {light}, {surface}, {grade}, unchanged from the first frame
CONSTRAINTS: preserve the first frame's composition and every string already printed in it. \
Do not add any text, caption, lettering, overlay or watermark of any kind."""


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
) -> str:
    """Assemble the motion prompt for one shot (Seedance 2.5, image-to-video).

    The prompt describes **motion and camera only**. Everything the viewer
    reads already exists in the first frame, drawn by Seedream, and text baked
    into a first frame was verified to survive the whole clip with its
    diacritics and kerning intact.

    `vo_text` is accepted so a caller can carry the spoken line alongside the
    shot and forward it to TTS. It is deliberately **never written into the
    prompt**: asked to caption Vietnamese, Seedance turned "Da khô căng, xỉn
    màu?" into "Da khò cáng, xỉn mau?". The CONSTRAINTS block instead forbids
    the model from adding any lettering at all.
    """
    del vo_text  # spoken by Seed Audio TTS; never drawn by Seedance
    return VIDEO_PROMPT.format(
        shot_scene=_strip_quotes(resolve_scene(shot_scene, spine)),
        lens=spine.lens,
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
