"""
Art direction - the brief becomes a worksheet.

This module is the studio's judgement, and it makes two decisions.

**Where the pixels come from.** Every kit slot is routed to REUSE, REMIX or
GENERATE. The rule is commercial, not technical: where a shopper inspects a
product before paying - Shopee's main listing image, the SKU close-up - an
invented pixel is a mismatch with the parcel, a return and a bad review, so the
brand's own photograph wins. Where a viewer is merely scrolling, a staged frame
built for the campaign works far better than a catalogue shot.

Validation on 21/08 added a second, independent argument for the same rule.
Generated images redraw the product's own packaging, and rotated glyphs degrade:
a real COSRX bottle came back reading `COSRᴀ` on the vertical wordmark running
up its black band, reproducibly, while the same string set horizontally on the
gold label was perfect. Regenerating a label risks misspelling a brand name on a
live listing. Reuse is the correct default wherever the label carries weight.

None of this may ever make the studio fail. A brand that arrives with two
photographs gets the same eight assets as a brand with two hundred; the thin
kho only shifts slots from REUSE towards GENERATE.

**What the frame says.** Every string that will be rendered is chosen here, from
the plan and the brief, and filtered against `forbidden_claims` before it can
reach a prompt. A forbidden claim burned into a listing image is a takedown, so
the filter runs on marketing copy, on spoken voiceover lines, and on the scene
descriptions themselves. When a candidate is dropped the next one in the chain
takes its place - the frame degrades to a safer sentence, never to a blank.

Pure logic: no API call, no file is opened, nothing here is slow. The output is
a `Worksheet`, which `render.py`, `motion.py` and `pipeline.py` execute.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable, Sequence

from app.schemas.studio import (
    AssetOrigin,
    AudienceBrief,
    BrandKit,
    CampaignInput,
    CampaignPlan,
    CreativeRoute,
    ImageKind,
    MarketSignal,
    Platform,
    ProductBrief,
)
from app.services.studio.config import studio_settings
from app.services.studio.looks import LOOKS, pick_looks
from app.services.studio.platforms import KITS, SlotSpec
from app.services.studio.slots import SHOT_TEMPLATES, SLOT_SCENES

if TYPE_CHECKING:  # pragma: no cover - inventory is imported for typing only
    from app.services.studio.inventory import InventorySheet


# ---------------------------------------------------------------------------
# Tuning
# ---------------------------------------------------------------------------
# These are art direction, not API behaviour, so they live beside the other
# data tables rather than in config.py: an art director tunes them by reading
# the sentence, not by setting an environment variable.

# Free-form marketing copy is shortened to fit a frame. Product names and
# promotions are facts and are never shortened - a truncated product name on a
# listing image reads as a bug, and a truncated price reads as a lie.
MAX_HEADLINE_CHARS = 60
MAX_BENEFIT_CHARS = 56
MAX_PROMO_CHARS = 48
MAX_NAME_CLAIM_CHARS = 64

# The call to action, on screen and spoken.
CTA_TEXT = "MUA NGAY"
VO_CTA_SUFFIX = "Mua ngay hôm nay."

# Last-resort subjects. A brief may arrive as nothing but product photographs,
# and a scene sentence with a hole in it is worse than a generic one.
FALLBACK_PAIN_POINT = "the everyday frustration this product solves"
FALLBACK_BENEFIT = "the product working as promised"
FALLBACK_PROMOTION = "a limited-time offer on this product"

# Used when a kit slot has no entry in slots.SLOT_SCENES - adding a slot to
# platforms.py must not be able to produce an empty prompt.
DEFAULT_SLOT_SCENE = (
    "the product standing alone and filling most of the frame on {surface}, {light}, "
    "straight on, the label square to the camera"
)

# Storyboard staging. `slots.SHOT_TEMPLATES` says which part of the brief each
# beat is about; this table says what that beat looks like. `{subject}` is the
# brief fragment, `{surface}` and `{light}` come from the route's look.
SHOT_SCENES: dict[str, str] = {
    # Beat 1, the hook. A person, because a problem needs a face - and a
    # generated person, because Seedance rejects reference images containing
    # real human faces.
    "consumer_pain_point": (
        "a close portrait of the target customer in front of a bathroom mirror, her "
        "expression showing the problem of {subject}, with {surface} just visible behind "
        "her, {light}, the product not yet in frame, the top third of the frame left "
        "empty for the headline"
    ),
    # Beat 2, the product. The honest shot: this is the object in the parcel.
    "product_photo": (
        "the product standing alone and filling the centre of the frame on {surface}, "
        "{light}, straight on, the label square to the camera and fully legible"
    ),
    # Beat 3, the reason to believe. One reason - a second weakens the first.
    "key_selling_points[0]": (
        "an extreme macro of the product's texture on {surface}, {light}, showing "
        "{subject}, the product itself just behind it and still in focus"
    ),
    # Beat 4, the ask. The offer is the subject; the product is the evidence.
    "promotion": (
        "the product on {surface} beside a clean rectangular offer card, {light}, the "
        "offer card brighter than everything around it and sitting above the centre line"
    ),
}

# Photos the inventory has disqualified as generation or video references.
UNUSABLE_PHOTO_TAGS = ("too_small_for_ref",)


# ---------------------------------------------------------------------------
# The worksheet
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StyleSpine:
    """One route's art direction, flattened and ready to paste into a prompt.

    Every image and every clip in a route receives these five values, word for
    word. That repetition is the whole consistency mechanism, so the spine is
    frozen: a slot that quietly edits the light is a slot that no longer belongs
    to the same photoshoot.
    """

    look_key: str
    lens: str
    light: str
    surface: str
    grade: str
    palette: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkItem:
    """One still image to produce, with its origin already decided.

    slot_id       `platforms.SlotSpec.id` - the slot this fills.
    platform      which marketplace the kit is for.
    kind          the BP-01 image kind, which is what the QA agent counts.
    origin        REUSE, REMIX or GENERATE. See the module docstring: this is
                  the studio's commercial argument, expressed as an enum.
    ratio / size  the shape as written in a prompt, and the pixel size read
                  from `studio_settings` via `SlotSpec.size_key`.
    scene         the staging sentence, already resolved against the spine.
    texts         `(text_key, string)` pairs to render, in reading order,
                  already filtered against the brief's forbidden claims.
    source_photo  the brand photograph this item is built from: the crop source
                  when REUSE, the image-to-image reference when REMIX, and the
                  Brand Lock reference when GENERATE. None only when the brand
                  supplied no usable photograph at all.
    rule          a marketplace rule that overrides the art direction.
    """

    slot_id: str
    platform: Platform
    kind: ImageKind
    origin: AssetOrigin
    ratio: str
    size: str
    scene: str
    texts: list[tuple[str, str]] = field(default_factory=list)
    source_photo: str | None = None
    rule: str | None = None


@dataclass(frozen=True)
class ShotPlan:
    """One resolved beat of the storyboard.

    `scene` is drawn by Seedream into the shot's keyframe, together with
    `onscreen_text`; the clip is then generated from that keyframe, and the text
    survives image-to-video intact. `vo_text` is spoken by TTS and is never
    given to the video model, which cannot spell Vietnamese.

    Task 9's `motion.render_shot` consumes exactly this type.
    """

    index: int
    role: str
    scene: str
    onscreen_text: str
    vo_text: str
    seconds: int


@dataclass
class Worksheet:
    """Everything one creative route will produce, decided and costed.

    Mutable on purpose: a worksheet is a working document, and the pipeline may
    drop a slot that fails QA twice. The decisions on it - the spine, and each
    item's origin - are frozen, because those are what must not drift.

    `label_text` is the strings printed on the product's own packaging. It is
    constant for the campaign and is passed into every prompt, which is what
    stops the model re-lettering the brand name.
    """

    route_id: str
    spine: StyleSpine
    items: list[WorkItem] = field(default_factory=list)
    shots: list[ShotPlan] = field(default_factory=list)
    label_text: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

def is_compliant(text: str, forbidden_claims: Iterable[str]) -> bool:
    """True when `text` contains none of the brief's forbidden claims.

    Case-folded substring matching, which is deliberately blunt: it catches
    "Trắng da vĩnh viễn chỉ sau 2 tuần" for the forbidden claim "trắng da vĩnh
    viễn". A false positive costs one fallback sentence; a false negative costs
    a marketplace takedown.
    """
    haystack = " ".join((text or "").split()).casefold()
    if not haystack:
        return True
    for claim in forbidden_claims or ():
        needle = " ".join((claim or "").split()).casefold()
        if needle and needle in haystack:
            return False
    return True


def _clean(text: str | None) -> str:
    """Collapse whitespace and strip braces, which would break prompt formatting."""
    if not text:
        return ""
    return " ".join(str(text).replace("{", "").replace("}", "").split())


def _clause(text: str | None) -> str:
    """Clean a brief fragment so it can be dropped mid-sentence into a scene.

    A pain point written as a sentence ("Da xỉn màu, khô.") reads as a mistake
    when it lands inside a longer clause, so the terminal punctuation goes.
    """
    return _clean(text).rstrip(" .;:!")


def _shorten(text: str, limit: int) -> str:
    """Trim free-form copy to `limit` characters at a word boundary."""
    text = _clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.-")
    return cut or text[:limit]


def _first_compliant(candidates: Sequence[str | None], forbidden: Sequence[str]) -> str:
    """Return the first non-empty candidate that carries no forbidden claim.

    The chain is what keeps the golden rule and compliance from fighting each
    other: a hook the planner wrote badly is replaced by the positioning line,
    not by an empty frame the model would fill with invented lettering.
    """
    for candidate in candidates:
        value = _clean(candidate)
        if value and is_compliant(value, forbidden):
            return value
    return ""


# ---------------------------------------------------------------------------
# Reading the brief
# ---------------------------------------------------------------------------

_VOLUME_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:ml|l|g|kg|oz|gói|viên|miếng)\b", re.IGNORECASE
)
_PERCENT_RE = re.compile(r"(\d{1,3})\s*%")
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _empty_input(plan: CampaignPlan) -> CampaignInput:
    """A blank brief, so the rest of this module never has to test for None.

    `gen_assets_agent.generate_assets` may legitimately be called without a
    `CampaignInput` - the seam keeps it optional so older callers work - and the
    studio still has to produce a kit when that happens.
    """
    return CampaignInput(
        campaign_id=plan.campaign_id,
        product_brief=ProductBrief(product_name="", category="", target_market=""),
        brand_kit=BrandKit(),
        audience_brief=AudienceBrief(target_customer="", language="vi", market=""),
        market_signal=MarketSignal(),
    )


def _display_name(brief: ProductBrief) -> str:
    """The product name as it should be set on a frame, or spoken.

    The trailing size in brackets goes: "COSRX Advanced Snail 96 Mucin Power
    Essence (100ml)" is a catalogue string, and "(100ml)" read aloud by a
    voiceover or set as a title card looks like a copy-paste accident. The
    volume is still rendered - as its own line of the product's label.
    """
    return _TRAILING_PAREN_RE.sub("", _clean(brief.product_name)).strip()


def product_label_text(brief: ProductBrief) -> list[str]:
    """The strings printed on the product's own packaging.

    Named in every prompt because the model redraws the packaging whether or not
    it is asked to, and what it invents is wrong: the vertical `COSRX` wordmark
    on a real bottle came back as `COSRᴀ` in every generated image. The brand
    token is listed separately from the full product name because it is a
    separate piece of artwork on the pack, usually the one set vertically.
    """
    full = _clean(brief.product_name)
    if not full:
        return []

    display = _display_name(brief)
    volume_match = _VOLUME_RE.search(full)
    volume = volume_match.group(0).replace(" ", "") if volume_match else ""

    brand = display.split(" ", 1)[0].strip(" -·,") if display else ""

    values: list[str] = []
    for value in (brand, display, volume):
        if value and value not in values:
            values.append(value)
    return values


def _offer_badge(promotion: str) -> str:
    """A short, loud version of the promotion, for a badge on the frame.

    "11.11: giảm 25% còn 290.000đ + freeship" becomes "GIẢM 25%". A badge has to
    read at thumbnail size, so it carries one number and nothing else.
    """
    promotion = _clean(promotion)
    if not promotion:
        return ""
    percent = _PERCENT_RE.search(promotion)
    if percent:
        return f"GIẢM {percent.group(1)}%"
    if "freeship" in promotion.casefold() or "free ship" in promotion.casefold():
        return "FREESHIP"
    return _shorten(promotion, 24).upper()


def _route(plan: CampaignPlan, route_id: str) -> CreativeRoute | None:
    """Find the creative route the worksheet is being built for.

    Matches on `route_id` first and falls back to position, so a plan whose
    routes are named "1"/"2" instead of "A"/"B" still produces two routes rather
    than two copies of the same one.
    """
    routes = list(plan.creative_routes or ())
    if not routes:
        return None
    wanted = (route_id or "A").strip().casefold()
    for route in routes:
        if (route.route_id or "").strip().casefold() == wanted:
            return route
    index = 1 if wanted in ("b", "2", "route b") else 0
    return routes[min(index, len(routes) - 1)]


def winning_route(plan: CampaignPlan) -> str | None:
    """What past campaign data says worked, as a string `pick_looks` can read.

    Only `performance_learning.keep` is consulted: "keep" is the list of things
    that earned their place. The entries are free text written by the planning
    agent ("giữ route testimonial_ugc - CTR 2.4% vs 0.9%"), so they are joined
    and handed over whole for keyword matching rather than parsed.
    """
    learning = getattr(plan, "performance_learning", None)
    keep = [_clean(entry) for entry in getattr(learning, "keep", None) or ()]
    keep = [entry for entry in keep if entry]
    return " · ".join(keep) if keep else None


# ---------------------------------------------------------------------------
# Text resolution
# ---------------------------------------------------------------------------

def _text_for(
    key: str,
    plan: CampaignPlan,
    campaign_input: CampaignInput,
    route: CreativeRoute | None,
) -> str:
    """Resolve one `slots.TEXT_KEYS` key to the exact string to render.

    Each key has a chain of candidates, best first. The chain exists for two
    reasons: a field may be missing from a sparse brief, and a field may carry a
    forbidden claim. Either way the next candidate steps in, so a frame never
    ends up with an empty TEXT block.
    """
    brief = campaign_input.product_brief
    forbidden = list(brief.forbidden_claims or ())
    positioning = plan.positioning

    hook = getattr(route, "hook_idea", "") if route else ""
    message = getattr(positioning, "key_selling_message", "")
    angle = getattr(positioning, "main_campaign_angle", "")
    points = list(brief.key_selling_points or ())
    promotion = brief.price_or_promotion or ""
    badge = _offer_badge(promotion)

    if key == "headline":
        return _shorten(
            _first_compliant([hook, message, angle, brief.product_name], forbidden),
            MAX_HEADLINE_CHARS,
        )

    if key == "benefit":
        return _shorten(
            _first_compliant(
                [message, points[0] if points else "", angle], forbidden
            ),
            MAX_BENEFIT_CHARS,
        )

    if key == "name_claim":
        # The product name is a fact and is never trimmed; the required claim
        # beside it is dropped instead when the pair would not fit the frame.
        name = _first_compliant([_display_name(brief), brief.product_name], forbidden)
        claim = _first_compliant(list(brief.required_claims or ()), forbidden)
        if name and claim and len(f"{name} · {claim}") <= MAX_NAME_CLAIM_CHARS:
            return f"{name} · {claim}"
        return name or claim

    if key == "badge":
        return _first_compliant([badge], forbidden)

    if key == "promo":
        return _shorten(_first_compliant([promotion, badge], forbidden), MAX_PROMO_CHARS)

    if key == "badge_cta":
        offer = _first_compliant([badge], forbidden)
        return f"{offer} · {CTA_TEXT}" if offer else CTA_TEXT

    # An unknown key is a typo in platforms.py or slots.py. Render nothing
    # rather than guessing - an invented string is the one failure mode this
    # module exists to prevent.
    return ""


def _speakable(text: str) -> str:
    """Turn a line written for the eye into one written for the ear.

    Typographic separators are punctuation on a frame and noise in a voiceover:
    TTS either reads "·" aloud or swallows the pause it was standing in for.
    """
    return _clean(text.replace(" · ", ", ").replace("·", ","))


def _vo_for(
    role: str,
    plan: CampaignPlan,
    campaign_input: CampaignInput,
    route: CreativeRoute | None,
    onscreen_text: str,
) -> str:
    """Resolve the spoken line for one storyboard beat.

    Voiceover is filtered against forbidden claims exactly like on-screen copy:
    a claim that cannot be printed cannot be said either.
    """
    brief = campaign_input.product_brief
    forbidden = list(brief.forbidden_claims or ())
    points = list(brief.key_selling_points or ())
    pain = campaign_input.market_signal.consumer_pain_point or ""

    if role == "hook":
        line = _first_compliant([pain, onscreen_text], forbidden)
        if line and line[-1] not in "?.!…":
            line = f"{line}?"
        return line

    if role == "product":
        return _first_compliant(
            [_text_for("name_claim", plan, campaign_input, route), brief.product_name],
            forbidden,
        )

    if role == "benefit":
        return _first_compliant(
            [
                plan.positioning.key_selling_message,
                points[0] if points else "",
                onscreen_text,
            ],
            forbidden,
        )

    if role == "cta":
        offer = _first_compliant([brief.price_or_promotion], forbidden)
        return f"{offer}. {VO_CTA_SUFFIX}" if offer else VO_CTA_SUFFIX

    return _first_compliant([onscreen_text], forbidden)


def _shot_subject(
    scene_from: str,
    plan: CampaignPlan,
    campaign_input: CampaignInput,
) -> str:
    """Resolve a `ShotTemplate.scene_from` token to the brief fragment it names.

    Scene descriptions are filtered for forbidden claims too: staging a shot
    that depicts a banned claim is the same liability as printing it.
    """
    brief = campaign_input.product_brief
    forbidden = list(brief.forbidden_claims or ())
    points = list(brief.key_selling_points or ())

    if scene_from == "consumer_pain_point":
        return _clause(
            _first_compliant(
                [
                    campaign_input.market_signal.consumer_pain_point,
                    plan.positioning.main_campaign_angle,
                    FALLBACK_PAIN_POINT,
                ],
                forbidden,
            )
        )
    if scene_from == "key_selling_points[0]":
        return _clause(
            _first_compliant(
                [
                    points[0] if points else "",
                    plan.positioning.key_selling_message,
                    FALLBACK_BENEFIT,
                ],
                forbidden,
            )
        )
    if scene_from == "promotion":
        return _clause(
            _first_compliant([brief.price_or_promotion, FALLBACK_PROMOTION], forbidden)
        )
    return ""


# ---------------------------------------------------------------------------
# Origin routing
# ---------------------------------------------------------------------------

def _photo_pool(
    sheet: "InventorySheet | None",
    campaign_input: CampaignInput,
) -> list[str]:
    """Every brand photograph usable as a reference, best first.

    The inventory is authoritative when it has anything to say - it has measured
    the pixels and knows which files the video model will reject outright. Only
    when it is silent (it never ran, or the brand handed over nothing) does the
    raw brief stand in.
    """
    photos = list(getattr(sheet, "photos", None) or ())
    if photos:
        return [
            photo.path
            for photo in photos
            if not any(tag in UNUSABLE_PHOTO_TAGS for tag in getattr(photo, "tags", ()))
        ]
    return [_clean(url) for url in campaign_input.brand_kit.product_photo_urls or () if url]


def _choose_origin(
    slot: SlotSpec,
    sheet: "InventorySheet | None",
    pool: Sequence[str],
    already_used: Sequence[str],
) -> tuple[AssetOrigin, str | None]:
    """Decide where one slot's pixels come from, and which photo they start at.

    REUSE     the slot asked for a real photograph and the inventory found one
              that qualifies. This is the shopper-inspects-it case: Shopee's
              main image and the SKU close-up, where an invented pixel means a
              parcel that does not match the listing, and where re-lettering the
              label risks misspelling the brand name.
    REMIX     the slot wants a new scene but a real product in it, and a usable
              photograph exists to work from.
    GENERATE  everything else, including every REUSE slot on a brand whose kho
              is too thin to fill it. The kit is always complete; only its
              provenance shifts.

    When several REUSE slots qualify for the same photograph, the ones later in
    the kit prefer a photograph not yet used, so a four-image listing is not the
    same picture four times.
    """
    eligible = list((getattr(sheet, "by_slot", None) or {}).get(slot.id) or ())

    if slot.prefer_origin is AssetOrigin.REUSE and eligible:
        fresh = [path for path in eligible if path not in already_used]
        return AssetOrigin.REUSE, (fresh or eligible)[0]

    reference = next((path for path in pool if path not in already_used), None) or (
        pool[0] if pool else None
    )

    if slot.prefer_origin is AssetOrigin.REMIX and reference:
        return AssetOrigin.REMIX, reference

    # GENERATE still carries the reference when one exists: it is the Brand Lock
    # image passed to Seedream as reference 1, which is what keeps the bottle
    # the brand's bottle.
    return AssetOrigin.GENERATE, reference


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_spine(
    plan: CampaignPlan,
    campaign_input: CampaignInput,
    route_id: str = "A",
) -> StyleSpine:
    """Choose the art direction for one route and flatten it into a spine.

    Route A takes the first look `pick_looks` returns and route B the second;
    the pair is guaranteed to differ on at least two axes, because two routes
    that look alike make the A/B test measure nothing. A route that past
    campaign data says won - read from `performance_learning.keep` - overrides
    the category convention.

    The palette is the brand's own colours when it has any; otherwise the look's
    palette hint stands in, so the STYLE block is never blank.
    """
    brief = campaign_input.product_brief
    look_a, look_b = pick_looks(
        category=brief.category or "",
        tone=campaign_input.brand_kit.tone_of_voice or "",
        trend=campaign_input.market_signal.trend or "",
        winning_route=winning_route(plan),
    )
    look_key = look_b if (route_id or "A").strip().casefold() in ("b", "2") else look_a
    look = LOOKS[look_key]

    palette = [c for c in (campaign_input.brand_kit.brand_colors or ()) if _clean(c)]
    return StyleSpine(
        look_key=look_key,
        lens=look.lens,
        light=look.light,
        surface=look.surface,
        grade=look.grade,
        palette=palette or [look.palette_hint],
    )


def build_worksheet(
    plan: CampaignPlan,
    campaign_input: CampaignInput | None,
    sheet: "InventorySheet | None" = None,
    route_id: str = "A",
    platforms: Sequence[Platform] | None = None,
) -> Worksheet:
    """Turn a plan, a brief and the brand's photo inventory into a work order.

    plan            the upstream planning agent's output: positioning, creative
                    routes, and any performance learning from past campaigns.
    campaign_input  the brief. Optional only because the agent seam allows it;
                    without it there are no product photos, no brand colours and
                    no forbidden claims, and the kit is correspondingly generic.
    sheet           the inventory's triage of the kho. May be None or empty -
                    the worksheet simply routes more slots to GENERATE.
    route_id        "A" or "B". Decides which of the two looks this route wears.
    platforms       which kits to build. Defaults to every kit in `KITS`.

    Returns a `Worksheet`: one `WorkItem` per slot of every requested platform,
    plus the four-beat storyboard (video slots take a prefix of it), plus the
    product's own label strings.
    """
    campaign_input = campaign_input or _empty_input(plan)
    spine = build_spine(plan, campaign_input, route_id)
    route = _route(plan, route_id)
    targets = list(platforms) if platforms else list(KITS)

    pool = _photo_pool(sheet, campaign_input)
    used: list[str] = []
    items: list[WorkItem] = []

    for platform in targets:
        kit = KITS.get(platform)
        if kit is None:
            continue
        for slot in kit.slots:
            origin, source_photo = _choose_origin(slot, sheet, pool, used)
            if source_photo and origin in (AssetOrigin.REUSE, AssetOrigin.REMIX):
                used.append(source_photo)

            scene_template = SLOT_SCENES.get(slot.id, DEFAULT_SLOT_SCENE)
            texts = [
                (key, value)
                for key in slot.text_keys
                for value in [_text_for(key, plan, campaign_input, route)]
                if value
            ]

            items.append(
                WorkItem(
                    slot_id=slot.id,
                    platform=platform,
                    kind=slot.kind,
                    origin=origin,
                    ratio=slot.ratio,
                    size=getattr(studio_settings, slot.size_key),
                    scene=scene_template.format(surface=spine.surface, light=spine.light),
                    texts=texts,
                    source_photo=source_photo,
                    rule=slot.rule,
                )
            )

    return Worksheet(
        route_id=route_id,
        spine=spine,
        items=items,
        shots=build_shots(plan, campaign_input, spine, route_id),
        label_text=product_label_text(campaign_input.product_brief),
    )


def build_shots(
    plan: CampaignPlan,
    campaign_input: CampaignInput | None,
    spine: StyleSpine,
    route_id: str = "A",
) -> list[ShotPlan]:
    """Expand the four-beat storyboard against this brief.

    Each `ShotTemplate` names the part of the brief its beat is about; this
    resolves that reference, stages it in the route's look, and picks the string
    the keyframe will carry and the line the voiceover will speak. Both are
    filtered against the brief's forbidden claims.

    The full four beats are always returned. A kit's `VideoSlot.shots` says how
    many of them that cut uses, and a shorter cut takes a prefix - the beats are
    ordered so that a prefix is still a coherent ad.
    """
    campaign_input = campaign_input or _empty_input(plan)
    route = _route(plan, route_id)
    shots: list[ShotPlan] = []

    for index, template in enumerate(SHOT_TEMPLATES):
        subject = _shot_subject(template.scene_from, plan, campaign_input)
        scene_template = SHOT_SCENES.get(template.scene_from, DEFAULT_SLOT_SCENE)
        onscreen = _text_for(template.text_key, plan, campaign_input, route)
        shots.append(
            ShotPlan(
                index=index,
                role=template.role,
                scene=scene_template.format(
                    subject=subject, surface=spine.surface, light=spine.light
                ),
                onscreen_text=onscreen,
                vo_text=_speakable(
                    _vo_for(template.role, plan, campaign_input, route, onscreen)
                ),
                seconds=template.seconds,
            )
        )
    return shots
