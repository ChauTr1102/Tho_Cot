"""
Triage the kho: decide which of the brand's own photos can be used as they are.

This is the node that makes the studio credible to an actual seller. A generic
AI tool regenerates everything; this one looks at what the brand already owns
and only makes what is missing. The commercial logic is asymmetric:

* Where the shopper **inspects** the product before paying -- Shopee's main
  listing image, the SKU close-up -- an invented pixel is a liability. A
  mismatch between the listing and the parcel is a return, and returns are the
  seller's money. Those slots want a real photograph.
* Where the viewer is **scrolling past** -- a TikTok cover, a promo banner --
  staged imagery is exactly what is wanted, and the kho rarely contains it.

So `build_sheet` is not a utility. It is the judgement call, and the thresholds
below decide how much of the kit is real photography.

Two disqualifications are hard, and both were measured against the live API
rather than assumed:

1. `min(width, height) < REF_MIN_PX` (300). Seedance rejects the request
   outright: `InvalidParameter: expected the width to be at least 300px, but
   received a 129x27px image instead`. Three of the five brand logos in
   `sample_data/` fail this (COSRX 129x27, Oatside 800x200, Marou 205x145).
2. `has_people`. Seedance rejects reference images containing real human faces.

Both produce a tag on `PhotoFacts` and exclude the photo from
`InventorySheet.video_refs`, which is the only list Task 9 may draw references
from.

The module is deliberately split into two halves. `measure()` is Pillow-only,
instant and offline -- every geometric fact comes from there. Vision tags are an
optional enrichment layered on top, and they may only ever **veto** a slot, never
invent eligibility: a photo is not disqualified for a fact nobody measured. The
one exception is `shopee_collection`, whose sole requirement (`product_count >=
2`) cannot be derived from pixels, so that slot stays empty without vision.

Consumed by Task 7 (`direct.build_worksheet` reads `by_slot` to choose REUSE vs
REMIX vs GENERATE) and Task 11 (`pipeline` runs this as the `inventory` node).
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageChops, ImageFilter, ImageStat

# Imported as a module, not as `from ark import describe_image`, so that the
# single network call this module makes is reachable at `inventory.ark` and can
# be stubbed in tests without a live key.
from app.services.studio import ark
from app.services.studio.config import studio_settings


# ---------------------------------------------------------------------------
# Tunables
#
# The studio's contract is that every tunable lives in config.py. These four are
# internals of the sampling method rather than studio policy, and config.py is
# owned by another task, so they are declared here and read through `_setting`:
# if a field of the same name is added to StudioSettings later, it silently
# wins and this default becomes dead. No call site hardcodes any of them.
# ---------------------------------------------------------------------------

#: A white pixel has to be *bright*: its darkest channel at least this value.
#: 235 accepts Anker's studio grey (#F5F5F5) and rejects Marou's cream
#: (#F3ECDC = 243,236,220) and Cocoon's (#F2EEE5) on brightness alone.
BG_WHITE_MIN_CHANNEL = 235

#: ...and *neutral*: no more than this spread between its brightest and darkest
#: channel. Brightness alone is not enough, and the kho proves it. COSRX's
#: infographic sits on ivory #FFF8EB = (255,248,235): its darkest channel is
#: 235, so it clears the brightness floor -- while being *brighter* than Anker's
#: legitimately white (245,245,247) backdrop. What separates them is tint.
#: Ivory spreads 20 levels across its channels, Anker's grey spreads 2. A bound
#: of 10 leaves room for JPEG chroma-subsampling noise on a genuine white and
#: still rejects every warm backdrop in the kho. Without this, an off-white
#: photo reaches Shopee's main slot and breaks a marketplace rule.
BG_WHITE_MAX_CHROMA = 10

#: Edge band sampled for `bg_whiteness`, as a fraction of the short side. A
#: fixed 12px band reads 1.5% of an 800px photo but only 0.5% of a 2500px one,
#: which makes the metric depend on resolution; a fraction keeps it comparable
#: across the kho. 2% of the short side is ~16px on COSRX's 800x1067 and ~50px
#: on Marou's 2500x2500.
BG_EDGE_BAND_FRACTION = 0.02
BG_EDGE_BAND_MIN_PX = 12

#: Seedance reference-image limits, measured 21/08/2026: aspect ratio 0.4-2.5,
#: 300-6000 px per side. The aspect bound is what rejects the Oatside logo
#: (800x200 = 4.0) even though both of its sides clear 300px... it does not,
#: but a 900x300 banner would, and this is the rule that stops it.
REF_MAX_PX = 6000
REF_MIN_ASPECT = 0.4
REF_MAX_ASPECT = 2.5

#: Formats the ModelArk endpoints accept. `.svg` is absent on purpose: Pillow
#: cannot open it and the API rejects it. One brand's logo is SVG.
SUPPORTED_SUFFIXES = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif", ".heic", ".heif"}
)

#: The exact question put to the vision model. Kept as one flat JSON request
#: because the model must *report*, not judge -- code does the judging below.
VISION_PROMPT = (
    "Describe this product photo for an e-commerce asset librarian. Answer as "
    'JSON: {"angle": "front|side|top|macro|lifestyle", "has_people": bool, '
    '"has_text": bool, "product_count": int, "background": "white|plain|scene", '
    '"label_readable": bool}'
)

#: Angles that show the product the way a shopper inspects it on a listing page.
CLOSEUP_ANGLES = frozenset({"macro", "front"})

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _setting(name: str, default: Any) -> Any:
    """Read a tunable from `studio_settings`, falling back to a module default.

    Lets config.py adopt one of this module's sampling constants later without
    any edit here, and keeps every value out of the call sites either way.
    """
    return getattr(studio_settings, name, default)


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


@dataclass
class PhotoFacts:
    """Everything known about one photo in the kho.

    `path` is the local file path and stays the identity of the photo
    everywhere downstream -- `InventorySheet.by_slot` and `video_refs` hold
    paths, not objects.

    `bg_whiteness` is the fraction (0-1) of sampled edge pixels that read as
    white. It is the load-bearing metric: it is the only thing standing between
    an off-white photo and Shopee's main slot, where a coloured background
    breaks a marketplace rule.

    `sharpness` is the standard deviation of an edge-detected copy -- a
    Laplacian-variance stand-in. It is informational: it ranks candidates
    within a slot rather than gating them, since a soft photo is a taste
    problem and a small photo is a rule violation.

    `tags` is a flat vocabulary so the sheet stays JSON-serialisable for the SSE
    stream. Geometry tags come from `measure`; vision tags are merged in by
    `build_sheet`. Absence of a vision tag means *unknown*, never *false*, which
    is why the positive and negative forms are both emitted (`has_people` /
    `no_people`).
    """

    path: str
    width: int
    height: int
    aspect: float
    bg_whiteness: float
    sharpness: float
    tags: list[str] = field(default_factory=list)
    eligible_slots: list[str] = field(default_factory=list)

    @property
    def min_side(self) -> int:
        """Shortest side in pixels -- the dimension every API floor is stated in."""
        return min(self.width, self.height)

    @property
    def max_side(self) -> int:
        """Longest side in pixels."""
        return max(self.width, self.height)

    @property
    def is_video_reference_safe(self) -> bool:
        """True when Seedance will accept this photo as a reference image.

        False means the API would reject the whole request (too small, too
        large, aspect outside 0.4-2.5) or reject the content (real human faces).
        """
        return not any(tag in _REF_BLOCKER_TAGS for tag in self.tags)


@dataclass
class InventorySheet:
    """The triage result for one brand's kho.

    `photos` holds every readable photo, in the order it was given.
    `by_slot` maps every known slot id to the photos that qualify, best first;
    a slot with no candidate is present with an empty list rather than missing,
    so callers can write `sheet.by_slot[slot_id]` without a guard and can tell
    "nothing qualified" apart from "never evaluated".
    `video_refs` holds the paths Seedance will actually accept as references.
    `skipped` maps a path that never became a photo to the reason why.

    All four fields default, so downstream fixtures can build an empty sheet
    with `InventorySheet()` or a hand-made one with keyword arguments.
    """

    photos: list[PhotoFacts] = field(default_factory=list)
    by_slot: dict[str, list[str]] = field(default_factory=dict)
    video_refs: list[str] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# measure() -- Pillow only, no network, instant
# ---------------------------------------------------------------------------


def measure(path: str) -> PhotoFacts:
    """Measure one photo with Pillow. No network, no API key, milliseconds.

    Raises `OSError` when the file is not an image Pillow can open; callers that
    are triaging a whole folder should use `build_sheet`, which records the
    failure in `InventorySheet.skipped` and carries on.
    """
    with Image.open(path) as raw:
        raw.load()
        im = _flatten_onto_white(raw)
        width, height = im.size
        facts = PhotoFacts(
            path=str(path),
            width=width,
            height=height,
            aspect=width / height if height else 0.0,
            bg_whiteness=_edge_whiteness(im),
            sharpness=_sharpness(im),
        )
    facts.tags = _geometry_tags(facts)
    facts.eligible_slots = eligible_slots(facts)
    return facts


def _flatten_onto_white(im: Image.Image) -> Image.Image:
    """Return an RGB copy, compositing any transparency onto white.

    A transparent PNG logo is displayed on a white listing page, so white is the
    honest background to measure it against. Calling `.convert("RGB")` directly
    would drop the alpha channel and read those pixels as whatever is stored
    beneath -- usually black -- scoring a white-page logo 0.0.
    """
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, (255, 255, 255))
        canvas.paste(rgba, mask=rgba.split()[3])
        return canvas
    return im.convert("RGB")


def _edge_whiteness(im: Image.Image) -> float:
    """Fraction of pixels in the four edge bands that read as white.

    Sampling the border rather than the whole frame is what separates
    "photographed on white" from "mostly pale": a white-background product shot
    has its subject in the middle and nothing at the edges, while a cream
    infographic is pale everywhere including the border.

    A pixel counts as white only when it is both **bright**
    (darkest channel >= `BG_WHITE_MIN_CHANNEL`) and **neutral**
    (channel spread <= `BG_WHITE_MAX_CHROMA`). Both conditions are load-bearing:
    ivory is brighter than a grey studio sweep and still is not white.
    """
    width, height = im.size
    if not width or not height:
        return 0.0

    band = max(int(_setting("BG_EDGE_BAND_MIN_PX", BG_EDGE_BAND_MIN_PX)),
               round(min(width, height) * float(
                   _setting("BG_EDGE_BAND_FRACTION", BG_EDGE_BAND_FRACTION))))
    band = max(1, min(band, width // 2, height // 2))

    strips = [
        im.crop((0, 0, width, band)),                       # top
        im.crop((0, height - band, width, height)),         # bottom
        im.crop((0, band, band, height - band)),            # left, corners already counted
        im.crop((width - band, band, width, height - band)),  # right
    ]

    cutoff = int(_setting("BG_WHITE_MIN_CHANNEL", BG_WHITE_MIN_CHANNEL))
    max_chroma = int(_setting("BG_WHITE_MAX_CHROMA", BG_WHITE_MAX_CHROMA))
    white = 0
    total = 0
    for strip in strips:
        if not strip.size[0] or not strip.size[1]:
            continue
        # Reduce each strip to two single-channel images -- per-pixel darkest and
        # brightest channel -- then AND the two masks. Every step stays in C.
        red, green, blue = strip.split()
        darkest = ImageChops.darker(ImageChops.darker(red, green), blue)
        brightest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
        bright_enough = darkest.point(lambda v: 255 if v >= cutoff else 0)
        neutral_enough = ImageChops.subtract(brightest, darkest).point(
            lambda v: 255 if v <= max_chroma else 0
        )
        histogram = ImageChops.darker(bright_enough, neutral_enough).histogram()
        white += histogram[255]
        total += sum(histogram)
    return (white / total) if total else 0.0


def _sharpness(im: Image.Image) -> float:
    """Standard deviation of an edge-detected grayscale copy.

    A stand-in for the variance of the Laplacian: `FIND_EDGES` is a 3x3
    high-pass convolution, so its spread tracks how much fine detail survives.
    The one-pixel border is cropped because the filter is undefined there and
    leaves a bright frame that would flatter every image equally.
    """
    grey = im.convert("L")
    if min(grey.size) < 3:
        return 0.0
    edges = grey.filter(ImageFilter.FIND_EDGES)
    width, height = edges.size
    edges = edges.crop((1, 1, width - 1, height - 1))
    return float(ImageStat.Stat(edges).stddev[0])


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

#: Tags that, on their own, make a photo unusable as a Seedance reference.
_REF_BLOCKER_TAGS = frozenset(
    {"too_small_for_ref", "too_large_for_ref", "bad_aspect_for_ref", "has_people"}
)


def _geometry_tags(facts: PhotoFacts) -> list[str]:
    """Tags derivable from pixels alone. Includes both hard API disqualifiers."""
    tags: list[str] = []

    if facts.aspect > 1.05:
        tags.append("landscape")
    elif facts.aspect < 0.95:
        tags.append("portrait")
    else:
        tags.append("square")

    if facts.bg_whiteness > float(studio_settings.BG_WHITE_THRESHOLD):
        tags.append("white_bg")

    # Measured: Seedance answers `InvalidParameter: expected the width to be at
    # least 300px, but received a 129x27px image instead`. The COSRX logo is
    # exactly that file.
    if facts.min_side < studio_settings.REF_MIN_PX:
        tags.append("too_small_for_ref")
    if facts.max_side > int(_setting("REF_MAX_PX", REF_MAX_PX)):
        tags.append("too_large_for_ref")
    if not (float(_setting("REF_MIN_ASPECT", REF_MIN_ASPECT))
            <= facts.aspect
            <= float(_setting("REF_MAX_ASPECT", REF_MAX_ASPECT))):
        tags.append("bad_aspect_for_ref")

    if facts.min_side >= studio_settings.SLOT_MIN_PX:
        tags.append("slot_sized")
    if facts.min_side >= studio_settings.SHOPEE_MIN_PX:
        tags.append("shopee_sized")

    return tags


def _vision_tags(payload: dict[str, Any]) -> list[str]:
    """Translate one vision answer into the flat tag vocabulary.

    Every field is optional and every value is checked: the model is a witness,
    not an authority, and a malformed answer must degrade to "unknown" rather
    than to a wrong assertion. Both polarities are emitted so that a missing tag
    unambiguously means the question was never answered.
    """
    tags: list[str] = []

    angle = payload.get("angle")
    if isinstance(angle, str) and angle.strip():
        tags.append(f"angle:{angle.strip().lower()}")

    background = payload.get("background")
    if isinstance(background, str) and background.strip():
        tags.append(f"background:{background.strip().lower()}")

    for key, yes, no in (
        ("has_people", "has_people", "no_people"),
        ("has_text", "has_text", "no_text"),
        ("label_readable", "label_readable", "label_unreadable"),
    ):
        value = payload.get(key)
        if isinstance(value, bool):
            tags.append(yes if value else no)

    count = payload.get("product_count")
    if isinstance(count, bool):
        count = None
    if isinstance(count, (int, float)) and count >= 0:
        tags.append(f"products:{int(count)}")

    return tags


def _flag(facts: PhotoFacts, yes: str, no: str) -> bool | None:
    """Read a three-state vision flag: True, False, or None for never measured."""
    if yes in facts.tags:
        return True
    if no in facts.tags:
        return False
    return None


def _product_count(facts: PhotoFacts) -> int | None:
    """How many distinct products the vision model counted, or None if unknown."""
    for tag in facts.tags:
        if tag.startswith("products:"):
            try:
                return int(tag.split(":", 1)[1])
            except ValueError:
                return None
    return None


def _angle(facts: PhotoFacts) -> str | None:
    """The camera angle the vision model reported, or None if unknown."""
    for tag in facts.tags:
        if tag.startswith("angle:"):
            return tag.split(":", 1)[1]
    return None


# ---------------------------------------------------------------------------
# Slot eligibility -- pure functions of PhotoFacts, easy to tune
# ---------------------------------------------------------------------------


def _qualifies_shopee_main(facts: PhotoFacts) -> bool:
    """Shopee's main listing image.

    The strictest slot in the studio, and the one where reuse matters most: it
    is the thumbnail the shopper decides on. Shopee requires a white background,
    so `bg_whiteness` is a hard gate, not a preference. A second product or any
    promotional overlay text also disqualifies -- both are marketplace rules and
    both are exactly what brand marketing collateral is full of.
    """
    if facts.min_side < studio_settings.SHOPEE_MIN_PX:
        return False
    if facts.bg_whiteness <= float(studio_settings.BG_WHITE_THRESHOLD):
        return False
    if _flag(facts, "has_text", "no_text") is True:
        return False
    if _flag(facts, "has_people", "no_people") is True:
        return False
    count = _product_count(facts)
    if count is not None and count != 1:
        return False
    return True


def _qualifies_shopee_sku(facts: PhotoFacts) -> bool:
    """The SKU close-up, where the shopper reads the label before paying.

    Background colour is free here, but the shot has to actually show the
    product head-on or in macro with a legible label. A lifestyle frame is a
    mood, not a specification, and putting one here is how a listing ends up
    describing something the parcel does not contain.
    """
    if facts.min_side < studio_settings.SLOT_MIN_PX:
        return False
    if _shows_no_product(facts):
        return False
    if _flag(facts, "has_people", "no_people") is True:
        return False
    angle = _angle(facts)
    if angle is not None and angle not in CLOSEUP_ANGLES:
        return False
    if _flag(facts, "label_readable", "label_unreadable") is False:
        return False
    return True


def _qualifies_shopee_collection(facts: PhotoFacts) -> bool:
    """The range shot: several products or variants in one frame.

    The only slot whose requirement cannot be seen in the pixels by Pillow, so
    it is the only one that genuinely needs vision. Unknown means not eligible:
    guessing here would put a single bottle into a slot the copy calls a range.
    """
    if facts.min_side < studio_settings.SLOT_MIN_PX:
        return False
    count = _product_count(facts)
    return count is not None and count >= 2


def _qualifies_tiktok_product(facts: PhotoFacts) -> bool:
    """The in-feed product still on TikTok Shop.

    Permissive by design -- this frame is scrolled past, not inspected, and it
    also seeds video keyframes, which is why real faces are excluded: Seedance
    refuses reference images containing them.
    """
    if facts.min_side < studio_settings.SLOT_MIN_PX:
        return False
    if _shows_no_product(facts):
        return False
    if _flag(facts, "has_people", "no_people") is True:
        return False
    return True


def _shows_no_product(facts: PhotoFacts) -> bool:
    """True when the vision model counted zero products in the frame.

    Brand kho folders are full of marketing collateral that contains no product
    at all -- COSRX's `product_02.jpg` is a "how snail secretion filtrate works"
    diagram. It is a well-lit, high-resolution, correctly-named file, and it is
    not a photograph of anything for sale. Only vision can tell.
    """
    count = _product_count(facts)
    return count is not None and count < 1


#: Slot id -> predicate. The ids mirror `platforms.KITS[...].slots[*].id`; they
#: are declared here rather than imported so inventory stays independent of the
#: art-direction tables (they are written by a different task and change often).
#: Add a slot by adding a predicate: nothing else in this module needs editing.
SLOT_RULES: dict[str, Callable[[PhotoFacts], bool]] = {
    "shopee_main": _qualifies_shopee_main,
    "shopee_sku": _qualifies_shopee_sku,
    "shopee_collection": _qualifies_shopee_collection,
    "tiktok_product": _qualifies_tiktok_product,
}

#: How to rank the candidates within a slot, best first. `by_slot[slot][0]` is
#: what Task 7 will REUSE, so the ordering is a real editorial choice: whitest
#: for the main image (it is a marketplace rule), sharpest for the close-up (the
#: label has to be readable), largest everywhere else.
_SLOT_RANKERS: dict[str, Callable[[PhotoFacts], tuple]] = {
    "shopee_main": lambda f: (-f.bg_whiteness, -f.min_side, -f.sharpness),
    "shopee_sku": lambda f: (-f.sharpness, -f.min_side),
    "shopee_collection": lambda f: (-(_product_count(f) or 0), -f.min_side),
    "tiktok_product": lambda f: (-f.min_side, -f.sharpness),
}


def eligible_slots(facts: PhotoFacts) -> list[str]:
    """Every kit slot this photo may fill as-is, in `SLOT_RULES` order."""
    return [slot_id for slot_id, rule in SLOT_RULES.items() if rule(facts)]


def video_reference_blockers(facts: PhotoFacts) -> list[str]:
    """Why Seedance would refuse this photo as a reference image. Empty is good.

    Kept separate from `eligible_slots` because these are API rejections, not
    editorial judgements: a blocked photo does not merely look wrong in a slot,
    it fails the request with `InvalidParameter` and wastes the render.
    """
    return [tag for tag in facts.tags if tag in _REF_BLOCKER_TAGS]


def to_dict(facts: PhotoFacts) -> dict[str, Any]:
    """Plain-JSON view of a `PhotoFacts`, for the SSE stream and the pack file."""
    payload = asdict(facts)
    payload["min_side"] = facts.min_side
    payload["is_video_reference_safe"] = facts.is_video_reference_safe
    return payload


def sheet_to_dict(sheet: InventorySheet) -> dict[str, Any]:
    """Plain-JSON view of an `InventorySheet`, for the SSE stream and the pack."""
    return {
        "photos": [to_dict(f) for f in sheet.photos],
        "by_slot": {k: list(v) for k, v in sheet.by_slot.items()},
        "video_refs": list(sheet.video_refs),
        "skipped": dict(sheet.skipped),
    }


# ---------------------------------------------------------------------------
# build_sheet -- the judgement call
# ---------------------------------------------------------------------------


def build_sheet(paths: list[str], use_vision: bool = True) -> InventorySheet:
    """Triage a brand's whole kho into a slot-eligibility sheet.

    `paths` are local files; anything Pillow cannot open -- an SVG logo, a
    truncated download -- is recorded in `sheet.skipped` and never reaches
    `sheet.photos`, because a file that cannot be measured cannot be reasoned
    about and must not be handed to the API.

    With `use_vision=True` each photo is additionally described by
    `ark.describe_image`, at most `VISION_CONCURRENCY` at a time. Those tags may
    only veto a slot; a vision failure is tagged `vision_failed` and the photo
    is judged on geometry alone. Triage that dies because one vision call timed
    out would be worse than triage that is slightly too generous, since every
    slot it fills is checked again by the visual QA gate downstream.

    Returns an `InventorySheet` whose `by_slot` lists every known slot id, best
    candidate first.
    """
    facts_list: list[PhotoFacts] = []
    skipped: dict[str, str] = {}

    for path in paths:
        suffix = Path(path).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            skipped[str(path)] = (
                f"unsupported format '{suffix or 'none'}': "
                "the API accepts jpeg/png/webp/bmp/tiff/gif/heic/heif"
            )
            continue
        try:
            facts_list.append(measure(path))
        except (OSError, ValueError) as exc:  # unreadable, truncated, not an image
            skipped[str(path)] = f"unreadable: {exc}"

    if use_vision and facts_list:
        _apply_vision(facts_list)

    by_slot: dict[str, list[str]] = {}
    for slot_id in SLOT_RULES:
        candidates = [f for f in facts_list if slot_id in f.eligible_slots]
        ranker = _SLOT_RANKERS.get(slot_id, lambda f: (-f.min_side,))
        by_slot[slot_id] = [f.path for f in sorted(candidates, key=ranker)]

    return InventorySheet(
        photos=facts_list,
        by_slot=by_slot,
        video_refs=[f.path for f in facts_list if f.is_video_reference_safe],
        skipped=skipped,
    )


def _apply_vision(facts_list: list[PhotoFacts]) -> None:
    """Describe every photo through the vision model and merge the tags in place.

    Runs `VISION_CONCURRENCY` calls at once because a single description takes
    41-109s; serially, a six-photo kho would cost ten minutes before the first
    image is rendered. Eligibility is recomputed afterwards, since a vision tag
    can only ever remove a slot the geometry allowed -- or, for
    `shopee_collection`, add the one slot geometry cannot see.
    """
    workers = max(1, int(studio_settings.VISION_CONCURRENCY))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        tag_lists = list(pool.map(_describe_one, facts_list))

    for facts, tags in zip(facts_list, tag_lists):
        facts.tags.extend(t for t in tags if t not in facts.tags)
        facts.eligible_slots = eligible_slots(facts)


def _describe_one(facts: PhotoFacts) -> list[str]:
    """Ask the vision model about one photo; never raise.

    Any failure -- a timeout, a refusal, a prose answer with no JSON in it --
    becomes the single tag `vision_failed`, which vetoes nothing.
    """
    try:
        raw = Path(facts.path).read_bytes()
        answer = ark.describe_image(raw, VISION_PROMPT)
        payload = parse_vision_answer(answer)
        if not payload:
            return ["vision_failed"]
        return _vision_tags(payload)
    except Exception:  # noqa: BLE001 - triage must survive any client failure
        return ["vision_failed"]


def parse_vision_answer(answer: str) -> dict[str, Any]:
    """Pull the JSON object out of a vision reply. Returns `{}` when there is none.

    The model wraps its answer in prose or a ```json fence often enough that
    `json.loads` on the raw string is not a safe reading, and a refusal is a
    perfectly valid string with no object in it at all.
    """
    if not isinstance(answer, str):
        return {}
    match = _JSON_BLOCK.search(answer)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
