"""
The studio's front door: adapts whatever the planning agent actually emits into
the Pydantic contracts the rest of the graph is written against.

Every other studio module (`direct`, `prompts`, `render`, `motion`, `qa_visual`)
consumes `CampaignPlan` and `CampaignInput` from `app.schemas.campaign`. The
upstream planning and research agents, however, emit a *research* shape: nested
`{decision, rationale, evidence[]}` objects instead of plain strings, a ranked
`benefit_hierarchy` instead of a flat list, `route_name` instead of `route_id`,
no `ab_test_plan`, no `campaign_id`, and platform names ("Douyin", "Taobao")
that no `Platform` enum member covers. Feeding that straight into the studio
raises `ValidationError`; feeding a hand-patched version into
`qa_review_agent.review` produces BLOCKERs about missing plan fields. This
module is the single place that reconciles the two, so no downstream node ever
has to guess which shape it was handed.

It also does four things a mechanical field rename would not:

1. **Strips editorial placeholders.** The real G7 plan carries the literal
   string `[Placeholder khuyến mãi 9.9: chưa xác nhận điều kiện áp dụng]` inside
   `message_angle`. Seedream renders any string it is given, faithfully, so an
   unstripped note becomes a marketplace banner reading "Placeholder khuyến mãi
   9.9". Bracketed editorial notes are removed here, at the boundary, and
   reported in `stripped_placeholders`.

2. **Recovers on-screen copy buried in prose.** Measurement is unambiguous:
   Seedream renders text that a prompt names explicitly (Vietnamese stacked
   diacritics included) and garbles text it has to invent. Upstream hides the
   copy inside `hook_idea` — *"Dòng chữ nhảy ra: 'Mệt buổi sáng? Pha nhanh một
   ly cà phê vị đậm Việt Nam'"*. Quoted spans are lifted out as exact strings so
   the prompt assembler can quote them verbatim.

3. **Keeps upstream's art direction.** `visual_direction` names kho files
   ("product_02.jpg") and says *"giữ logo Trung Nguyên G7 theo đúng bao bì,
   không chỉnh sửa thiết kế gốc"*. That instruction is correct and expensive to
   ignore: a real COSRX bottle regenerated from scratch came back with its
   vertical wordmark reading `COSRᴀ`. Referenced filenames are surfaced as a
   list of basenames so the worksheet can prefer those photos (REUSE/REMIX over
   GENERATE), and the "do not redraw the packaging" instruction is surfaced as a
   boolean the prompt assembler can act on.

4. **Maps platforms without dropping any.** Douyin, TikTok Shop and livestream
   commerce are one vertical short-form kit; Shopee, Lazada and Tokopedia are
   one marketplace kit. Anything else (Taobao, Tmall International — the G7
   campaign targets China, the US, Korea and SEA) is *reported*, never silently
   discarded, so the studio can say out loud which marketplace it was asked for
   and cannot serve.

Public surface:
    load_plan(raw, campaign_id)   -> CampaignPlan
    load_input(raw, campaign_id)  -> CampaignInput
    load_pair(plan_path, input_path, campaign_id) -> (CampaignPlan, CampaignInput)
    parse_plan(raw, campaign_id)  -> UpstreamPlan   (plan + hints + warnings)
    parse_input(raw, campaign_id) -> UpstreamInput  (input + platforms + warnings)

Everything is forgiving by design: missing optional keys, `null` where a list is
expected, and either schema shape all parse. `UpstreamFormatError` is raised
only when something genuinely required is absent — a plan with no creative
routes, or a brief with no product name.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

from pydantic import BaseModel, Field

from app.schemas.campaign import (
    ABTestPlan,
    AudienceBrief,
    BrandKit,
    CampaignInput,
    CampaignPlan,
    CreativeRoute,
    MarketSignal,
    PastCampaignData,
    Platform,
    PerformanceLearning,
    ProductBrief,
    ProductPositioning,
)
from app.services.studio.config import studio_settings


def _setting(name: str, default: Any) -> Any:
    """Read a tunable from `studio_settings`, falling back to a module default.

    Mirrors `inventory._setting`. The vocabularies below are data tables rather
    than API knobs, so they live here where they can be read alongside the
    parsing rules that use them, but any of the numeric limits can be promoted
    to `config.py` later without touching a call site.
    """
    return getattr(studio_settings, name, default)


# ---------------------------------------------------------------------------
# Vocabularies (data only — no logic below this heading)
# ---------------------------------------------------------------------------

#: Phrases that mark a span of text as a note to a human rather than copy for a
#: shopper. Hit anywhere in a bracketed span or a quoted span, the span is
#: dropped instead of being rendered. Vietnamese first: the planning agent
#: writes its notes in Vietnamese.
EDITORIAL_MARKERS: tuple[str, ...] = (
    "placeholder",
    "chưa xác nhận",
    "chưa xác minh",
    "cần xác nhận",
    "cần xác minh",
    "cần bổ sung",
    "cần thay thế",
    "ghi chú",
    "chú thích",
    "lưu ý",
    "không phải ảnh thực tế",
    "ảnh minh họa",
    "ảnh minh hoạ",
    "tbd",
    "to be confirmed",
    "to be decided",
    "todo",
    "fixme",
    "internal note",
    "note:",
    "pending confirmation",
    "draft only",
    "fill in",
    "insert ",
    "lorem ipsum",
    "xxx",
)

#: Phrases that mean "this product's packaging is already correct — reproduce
#: it, do not redesign it". Upstream is right to say so: regenerating a label
#: reproducibly misspelled a real brand name (`COSRX` -> `COSRᴀ`).
PRESERVE_MARKERS: tuple[str, ...] = (
    "không chỉnh sửa",
    "không thay đổi",
    "giữ nguyên",
    "giữ logo",
    "giữ đúng",
    "đúng bao bì",
    "theo đúng bao bì",
    "thiết kế gốc",
    "nguyên bản",
    "bản gốc",
    "do not modify",
    "do not redraw",
    "do not alter",
    "do not redesign",
    "keep the original",
    "keep original",
    "unchanged",
    "as printed",
)

#: Platform name -> studio kit. Matched longest-alias-first as a substring of
#: the normalised name, so "TikTok Shop", "TikTok organic" and "Douyin" all land
#: on the same vertical short-form kit and "Shopee Live" stays on Shopee.
PLATFORM_ALIASES: dict[str, Platform] = {
    # vertical short-form video, scrolling viewer
    "tiktok shop": Platform.TIKTOK_SHOP,
    "tiktok organic": Platform.TIKTOK_SHOP,
    "tiktok": Platform.TIKTOK_SHOP,
    "douyin": Platform.TIKTOK_SHOP,
    "livestream commerce": Platform.TIKTOK_SHOP,
    "live commerce": Platform.TIKTOK_SHOP,
    "livestream": Platform.TIKTOK_SHOP,
    "live streaming": Platform.TIKTOK_SHOP,
    "short video": Platform.TIKTOK_SHOP,
    "short-form video": Platform.TIKTOK_SHOP,
    "instagram reels": Platform.TIKTOK_SHOP,
    "youtube shorts": Platform.TIKTOK_SHOP,
    "reels": Platform.TIKTOK_SHOP,
    # marketplace listing, comparing shopper
    "shopee": Platform.SHOPEE,
    "lazada": Platform.SHOPEE,
    "tokopedia": Platform.SHOPEE,
}

#: Used when upstream gives no A/B success metrics. These four are what the
#: BP-01 reference plan measures and what the campaign objectives imply.
DEFAULT_SUCCESS_METRICS: tuple[str, ...] = (
    "CTR",
    "3s view rate",
    "Add-to-cart rate",
    "CVR",
)

#: Route ids are positional. Upstream numbers its routes by prose name only.
ROUTE_ID_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

#: A headline is a few words. When nothing in `hook_idea` is quoted we fall back
#: to a short field and truncate rather than shipping a paragraph into a frame.
MAX_HEADLINE_WORDS = 12

#: A bracketed span with at least this many words is an editorial aside even
#: when it uses none of the marker phrases. Short brackets ("[NEW]", "[9.9]")
#: are legitimate on-image labels and survive.
EDITORIAL_MIN_WORDS = 3

#: Keys an upstream object may use for its single meaningful value, in priority
#: order. The research agent wraps every decision as
#: `{decision, rationale, evidence[]}`; other runs use `value` or `text`.
_SCALAR_KEYS: tuple[str, ...] = (
    "decision",
    "value",
    "text",
    "statement",
    "summary",
    "answer",
    "benefit",
    "label",
    "title",
    "name",
)

#: Wrapper keys a plan may be nested under.
_PLAN_WRAPPERS: tuple[str, ...] = ("plan", "campaign_plan", "output", "data", "result")

_BRACKET_RE = re.compile(r"[\[［【]([^\[\]［］【】]*)[\]］】]")

#: Quote pairs, richest first. Each pass blanks what it matched so a straight
#: apostrophe inside an already-matched double-quoted span ("don't") can never
#: open a single-quoted span of its own.
_QUOTE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'"([^"\n]{2,400})"'),
    re.compile(r"“([^”\n]{2,400})”"),
    re.compile(r"„([^“”\n]{2,400})[“”]"),
    re.compile(r"«([^»\n]{2,400})»"),
    re.compile(r"‘([^’\n]{2,400})’"),
    re.compile(r"(?<![\w’'])'([^'\n]{2,400})'(?![\w])"),
)

_FILENAME_RE = re.compile(
    r"\b([\w\-]+\.(?:jpe?g|png|webp|avif|gif|bmp|tiff?|heic|mp4|mov|webm))\b",
    re.IGNORECASE,
)

_URL_RE = re.compile(r"https?://\S+")

#: Sentence boundaries. A full stop only ends a sentence when whitespace or the
#: end of the string follows it, so `product_01.jpg` stays one token and an
#: art-direction clause is not sliced in half at its own filename reference.
_SENTENCE_SPLIT_RE = re.compile(r"[;\n]|\.(?=\s|$)")

_HEADLINE_SPLIT_RE = re.compile(r"[;!?\n]|\.(?=\s|$)|\s[–—-]\s")


# ---------------------------------------------------------------------------
# Errors and contracts
# ---------------------------------------------------------------------------


class UpstreamFormatError(ValueError):
    """Raised when an upstream document is missing something genuinely required.

    Deliberately narrow. Missing optional keys, `null` in place of a list and an
    unfamiliar schema shape are all absorbed silently; only a plan with no
    creative routes, an unreadable document, or a brief with no product name
    stops the studio, because those cannot be worked around.
    """


class RouteHints(BaseModel):
    """Everything the studio needs from one creative route that `CreativeRoute` cannot hold.

    `CreativeRoute` is teammate-owned and carries prose. The studio needs exact
    strings and file references, so they are extracted once here and travel
    alongside the plan rather than being re-derived (differently) by each node.
    """

    route_id: str
    route_name: str = ""
    #: Exact strings upstream quoted inside `hook_idea` — the copy that is meant
    #: to appear in the frame. Quote these verbatim in the TEXT block.
    onscreen_text: list[str] = Field(default_factory=list)
    #: The single best on-screen line for this route, always short enough to set.
    headline: str = ""
    #: Strings printed on the product's own packaging that upstream asked to keep
    #: ("G7 INSTANT COFFEE"). Naming them explicitly is the defence against the
    #: measured `COSRX` -> `COSRᴀ` failure.
    packaging_text: list[str] = Field(default_factory=list)
    #: Basenames of kho photos upstream referenced by name ("product_02.jpg").
    #: The worksheet should prefer these over an arbitrary photo.
    reference_photos: list[str] = Field(default_factory=list)
    #: The clauses of `visual_direction` that carry an instruction, kept verbatim.
    art_direction_notes: list[str] = Field(default_factory=list)
    #: True when upstream said the packaging must not be redesigned.
    preserve_packaging: bool = False
    #: Platform kits this route maps onto, in the order upstream listed them.
    platforms: list[Platform] = Field(default_factory=list)
    #: Platform names this studio has no kit for. Reported, never dropped.
    unsupported_platforms: list[str] = Field(default_factory=list)
    #: The platform names exactly as upstream wrote them.
    raw_platforms: list[str] = Field(default_factory=list)
    #: Bracketed editorial spans removed from this route's text.
    stripped_placeholders: list[str] = Field(default_factory=list)


class UpstreamPlan(BaseModel):
    """A `CampaignPlan` plus everything the adapter learned while building it."""

    plan: CampaignPlan
    hints: list[RouteHints] = Field(default_factory=list)
    #: Union of every route's platforms, first-seen order.
    platforms: list[Platform] = Field(default_factory=list)
    unsupported_platforms: list[str] = Field(default_factory=list)
    stripped_placeholders: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def hints_for(self, route_id: str) -> RouteHints | None:
        """Return the hints for one route id, or None when the id is unknown."""
        for hint in self.hints:
            if hint.route_id == route_id:
                return hint
        return None


class UpstreamInput(BaseModel):
    """A `CampaignInput` plus the platform mapping and anything lost in flattening."""

    campaign_input: CampaignInput
    platforms: list[Platform] = Field(default_factory=list)
    unsupported_platforms: list[str] = Field(default_factory=list)
    stripped_placeholders: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Text hygiene
# ---------------------------------------------------------------------------


def looks_editorial(text: str) -> bool:
    """Return True when a span reads as a note to a human, not copy for a shopper.

    Used to decide whether a bracketed span is stripped and whether a quoted
    span is eligible to become on-screen text. Marker-driven so an art director
    can extend `EDITORIAL_MARKERS` without reading this file.
    """
    lowered = text.casefold()
    return any(marker in lowered for marker in EDITORIAL_MARKERS)


def strip_placeholders(text: str | None) -> tuple[str, list[str]]:
    """Remove bracketed editorial notes from `text`.

    Returns `(cleaned_text, removed_spans)`. A bracketed span is removed when it
    contains an editorial marker or runs to `EDITORIAL_MIN_WORDS` words or more;
    short brackets such as `[NEW]` are legitimate on-image labels and survive.

    This is the guard behind the single most embarrassing failure this system
    could ship: the real G7 plan carries
    `[Placeholder khuyến mãi 9.9: chưa xác nhận điều kiện áp dụng]` inside
    `message_angle`, and Seedream renders whatever string it is handed.
    """
    if not text:
        return "", []

    removed: list[str] = []

    min_words = _setting("UPSTREAM_EDITORIAL_MIN_WORDS", EDITORIAL_MIN_WORDS)

    def _replace(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        wordy = len(inner.split()) >= min_words
        if inner and (looks_editorial(inner) or wordy):
            removed.append(match.group(0))
            return " "
        return match.group(0)

    cleaned = _BRACKET_RE.sub(_replace, text)
    return _tidy(cleaned), removed


def drop_editorial_clauses(text: str | None) -> tuple[str, list[str]]:
    """Remove whole clauses that read as a note to a human, keeping the rest.

    The bracket stripper handles upstream's marked-up notes. This handles the
    unmarked ones: the real G7 brief ends its promotion with
    *"; cần xác nhận điều kiện áp dụng trước khi xuất bản"* — an instruction to
    the marketing team that would otherwise be rendered onto a 9.9 sale banner
    next to the offer it qualifies. Applied to promotional copy and to recovered
    on-screen strings, not to positioning prose, where a marker phrase is more
    likely to be part of a real sentence.
    """
    if not text:
        return "", []

    kept: list[str] = []
    removed: list[str] = []
    for piece in _SENTENCE_SPLIT_RE.split(text):
        clause = piece.strip()
        if not clause:
            continue
        if looks_editorial(clause):
            removed.append(clause)
        else:
            kept.append(clause)

    if not kept:
        return "", removed
    return _tidy("; ".join(kept)), removed


def extract_quoted(text: str | None) -> list[str]:
    """Return every quoted span in `text`, in document order.

    Handles straight and curly quotes, single and double, plus guillemets. Each
    pass blanks what it matched, so an apostrophe inside an already-captured
    double-quoted span ("so you don't need sugar") cannot open a span of its own.
    Editorial spans are dropped: upstream also quotes its own disclaimers
    (*'không phải ảnh thực tế vùng nguyên liệu sản phẩm'*) and those must never
    reach a frame.
    """
    if not text:
        return []

    working = text
    found: list[tuple[int, str]] = []
    for pattern in _QUOTE_PATTERNS:
        for match in pattern.finditer(working):
            found.append((match.start(), match.group(1)))
        working = pattern.sub(lambda m: "\x00" * len(m.group(0)), working)

    spans: list[str] = []
    for _, value in sorted(found, key=lambda pair: pair[0]):
        cleaned, _ = strip_placeholders(value)
        cleaned, _ = drop_editorial_clauses(cleaned)
        cleaned = cleaned.strip(" \t–—-:,")
        if not cleaned or looks_editorial(cleaned):
            continue
        if not re.search(r"[^\W\d_]", cleaned, re.UNICODE):
            continue  # punctuation or digits only
        if _FILENAME_RE.fullmatch(cleaned):
            continue  # a filename is an art-direction reference, not copy
        if cleaned not in spans:
            spans.append(cleaned)
    return spans


def extract_onscreen_text(hook_idea: str | None, *extra: str | None) -> list[str]:
    """Recover the exact on-screen strings upstream buried in prose.

    Text a prompt names explicitly renders correctly; text the model invents
    comes back garbled (`LUNAÁIRA`, `EFFFECTIVE`), in English as well as in
    Vietnamese. Upstream writes the copy it wants on screen inside `hook_idea`
    and marks it with quotes, so quoted spans are the signal.
    """
    spans = extract_quoted(hook_idea)
    for other in extra:
        for value in extract_quoted(other):
            if value not in spans:
                spans.append(value)
    return spans


def pick_headline(
    onscreen: Sequence[str], route_name: str = "", message_angle: str = ""
) -> str:
    """Choose one short line to set as the route's headline.

    Prefers a string upstream actually quoted. When nothing is quoted, falls
    back to the route name and then to the opening clause of `message_angle`,
    truncated: a headline is a few words, and `message_angle` is three sentences
    of positioning that would be unreadable on a 9:16 cover.
    """
    for candidate in onscreen:
        if candidate.strip():
            return candidate.strip()

    max_words = _setting("UPSTREAM_MAX_HEADLINE_WORDS", MAX_HEADLINE_WORDS)

    name, _ = strip_placeholders(route_name)
    if name and len(name.split()) <= max_words:
        return name

    angle, _ = strip_placeholders(message_angle)
    if angle:
        first = next((p.strip() for p in _HEADLINE_SPLIT_RE.split(angle) if p.strip()), "")
        words = first.split()
        if words:
            return " ".join(words[:max_words])

    return name


def extract_reference_photos(*texts: str | None) -> list[str]:
    """Return the kho filenames upstream named, as basenames, in first-seen order.

    Upstream writes art direction like *"Dùng ảnh gói cà phê đơn product_02.jpg
    làm điểm nhấn"*. Leaving that buried in prose throws away the one thing that
    lets the worksheet choose REUSE or REMIX over GENERATE for the slot the
    brand already has a real photograph for. URLs are removed first so a CDN
    path never masquerades as a local file.
    """
    names: list[str] = []
    for text in texts:
        if not text:
            continue
        for match in _FILENAME_RE.finditer(_URL_RE.sub(" ", text)):
            base = os.path.basename(match.group(1))
            if base not in names:
                names.append(base)
    return names


def extract_art_direction(visual_direction: str | None) -> tuple[list[str], bool]:
    """Split art direction into instruction clauses and detect a "do not redraw" order.

    Returns `(notes, preserve_packaging)`. `preserve_packaging` is True when
    upstream asked for the packaging to be reproduced rather than redesigned —
    *"giữ logo Trung Nguyên G7 theo đúng bao bì, không chỉnh sửa thiết kế gốc"*.
    That instruction is correct: regenerating a label reproducibly misspelled a
    real brand name, so the prompt assembler must pin the product rather than
    invite the model to restyle it.
    """
    if not visual_direction:
        return [], False

    cleaned, _ = strip_placeholders(visual_direction)
    notes: list[str] = []
    for raw_clause in _SENTENCE_SPLIT_RE.split(cleaned):
        clause = raw_clause.strip()
        if not clause:
            continue
        lowered = clause.casefold()
        if any(marker in lowered for marker in PRESERVE_MARKERS):
            if clause not in notes:
                notes.append(clause)
    return notes, bool(notes)


def map_platforms(names: Iterable[Any] | None) -> tuple[list[Platform], list[str]]:
    """Map upstream platform names onto studio kits, reporting the ones we cannot serve.

    Returns `(platforms, unsupported)`. Douyin, TikTok Shop and livestream
    commerce are all vertical short-form video and share the `tiktok_shop` kit;
    Shopee, Lazada and Tokopedia share the `shopee` kit. Anything else — Taobao
    and Tmall International appear in the real G7 plan, which targets China, the
    US, Korea and SEA — is returned in `unsupported` so the studio can say which
    marketplace it was asked for and has no kit for. Nothing is discarded.
    """
    platforms: list[Platform] = []
    unsupported: list[str] = []
    aliases = sorted(PLATFORM_ALIASES, key=len, reverse=True)

    for entry in _iter_strings(names):
        normalised = re.sub(r"\s+", " ", entry).strip().casefold()
        if not normalised:
            continue
        match = next((a for a in aliases if a in normalised), None)
        if match is None:
            if entry not in unsupported:
                unsupported.append(entry)
            continue
        platform = PLATFORM_ALIASES[match]
        if platform not in platforms:
            platforms.append(platform)

    return platforms, unsupported


# ---------------------------------------------------------------------------
# Shape-tolerant readers
# ---------------------------------------------------------------------------


def _tidy(text: str) -> str:
    """Collapse the whitespace and dangling punctuation a removal leaves behind."""
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"([,;:])\s*([.;,])", r"\2", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip(" \t\n,;:–—")


def _first(mapping: Any, *keys: str) -> Any:
    """Return the first present, non-None value among `keys` in a mapping."""
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _scalar(value: Any) -> str:
    """Flatten any upstream value into a plain string.

    Absorbs the research agent's `{decision, rationale, evidence[]}` wrapper, a
    bare string, a list of strings, a number, and `None`. This is the single
    reason a plan whose `main_campaign_angle` is an object still produces a
    `ProductPositioning` whose `main_campaign_angle` is a `str`.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        picked = _first(value, *_SCALAR_KEYS)
        if picked is not None:
            return _scalar(picked)
        return ""
    if isinstance(value, (list, tuple)):
        parts = [_scalar(item) for item in value]
        return "; ".join(p for p in parts if p)
    return str(value).strip()


def _iter_strings(value: Any) -> list[str]:
    """Coerce anything into a list of non-empty strings.

    `None` (upstream writes `null` where the schema says list), a bare string, a
    list of strings and a list of `{decision, ...}` objects all land here.
    """
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        text = _scalar(value)
        return [text] if text else []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            out.extend(_iter_strings(item))
        return out
    text = str(value).strip()
    return [text] if text else []


def _ranked_strings(value: Any) -> list[str]:
    """Flatten a ranked list (`[{rank, benefit, rationale, evidence[]}]`) to strings.

    Sorts by `rank` when every entry carries one, so the benefit *hierarchy*
    survives the flattening instead of becoming an arbitrarily ordered list.
    """
    if not isinstance(value, (list, tuple)):
        return _iter_strings(value)

    entries = [item for item in value if item is not None]
    ranks = [
        item.get("rank")
        for item in entries
        if isinstance(item, dict) and isinstance(item.get("rank"), (int, float))
    ]
    if entries and len(ranks) == len(entries):
        entries = sorted(entries, key=lambda item: item.get("rank", 0))

    out: list[str] = []
    for item in entries:
        text = _scalar(item)
        if text and text not in out:
            out.append(text)
    return out


def _collect_sources(node: Any, found: list[str] | None = None) -> list[str]:
    """Walk an upstream document and collect every citation URL, in first-seen order.

    Upstream scatters citations in three places: `source_summary.sources[].url`,
    `evidence[].source_url` on every decision, and (in the canonical shape) a
    plain `positioning.sources` list of strings. `qa_review_agent` raises
    MARKET.NO_SOURCES when `positioning.sources` is empty, so all three are
    gathered into the one field the contract has.
    """
    found = [] if found is None else found

    if isinstance(node, dict):
        for key in ("source_url", "url"):
            value = node.get(key)
            if isinstance(value, str) and value.strip() and value.strip() not in found:
                found.append(value.strip())
        for key, value in node.items():
            if key in {"source_url", "url"}:
                continue
            _collect_sources(value, found)
    elif isinstance(node, (list, tuple)):
        for item in node:
            _collect_sources(item, found)

    return found


def _plan_body(raw: Any) -> dict[str, Any]:
    """Unwrap a plan document that arrived nested under `plan` / `data` / `result`."""
    if not isinstance(raw, dict):
        raise UpstreamFormatError(
            f"Campaign plan must be a JSON object, got {type(raw).__name__}."
        )
    if _first(raw, "creative_routes", "routes") is not None:
        return raw
    for wrapper in _PLAN_WRAPPERS:
        nested = raw.get(wrapper)
        if isinstance(nested, dict) and _first(nested, "creative_routes", "routes"):
            return nested
    return raw


# ---------------------------------------------------------------------------
# Plan adapter
# ---------------------------------------------------------------------------


def _route_hints(route: dict[str, Any], index: int) -> RouteHints:
    """Build the studio-side hints for one upstream creative route."""
    route_id = _scalar(_first(route, "route_id", "id"))
    if not route_id:
        route_id = ROUTE_ID_ALPHABET[index] if index < len(ROUTE_ID_ALPHABET) else str(index + 1)

    route_name = _scalar(_first(route, "route_name", "name", "title"))

    hook_raw = _scalar(_first(route, "hook_idea", "hook", "opening_idea"))
    visual_raw = _scalar(_first(route, "visual_direction", "visual", "art_direction"))
    angle_raw = _scalar(_first(route, "message_angle", "message", "angle"))

    hook, hook_removed = strip_placeholders(hook_raw)
    visual, visual_removed = strip_placeholders(visual_raw)
    angle, angle_removed = strip_placeholders(angle_raw)

    onscreen = extract_onscreen_text(hook)
    packaging = [span for span in extract_quoted(visual) if span not in onscreen]
    notes, preserve = extract_art_direction(visual)
    photos = extract_reference_photos(visual, hook)

    raw_platforms = _iter_strings(
        _first(route, "suggested_platform_usage", "platforms", "platform_usage", "channels")
    )
    platforms, unsupported = map_platforms(raw_platforms)

    return RouteHints(
        route_id=route_id,
        route_name=route_name,
        onscreen_text=onscreen,
        headline=pick_headline(onscreen, route_name, angle),
        packaging_text=packaging,
        reference_photos=photos,
        art_direction_notes=notes,
        preserve_packaging=preserve,
        platforms=platforms,
        unsupported_platforms=unsupported,
        raw_platforms=raw_platforms,
        stripped_placeholders=[*hook_removed, *visual_removed, *angle_removed],
    )


def _creative_route(route: dict[str, Any], hints: RouteHints) -> CreativeRoute:
    """Build the contract-shaped `CreativeRoute` for one upstream route."""
    hook, _ = strip_placeholders(_scalar(_first(route, "hook_idea", "hook", "opening_idea")))
    visual, _ = strip_placeholders(
        _scalar(_first(route, "visual_direction", "visual", "art_direction"))
    )
    angle, _ = strip_placeholders(_scalar(_first(route, "message_angle", "message", "angle")))

    return CreativeRoute(
        route_id=hints.route_id,
        hook_idea=hook or hints.route_name,
        visual_direction=visual,
        message_angle=angle,
        # Kept as upstream wrote them: `CreativeRoute.suggested_platform_usage`
        # is free text and the mapped enum lives on `RouteHints.platforms`, so
        # nothing is lost either way.
        suggested_platform_usage=hints.raw_platforms,
    )


def _assumptions(body: dict[str, Any], routes: Sequence[dict[str, Any]]) -> list[str]:
    """Collect the hypotheses upstream recorded, for the A/B plan's expected learning.

    The research agent files them twice: as `evidence` entries with
    `basis == "assumption"` on each route, and as free text under
    `source_summary.assumptions`. Route-level entries are preferred because they
    are already split by route.
    """
    out: list[str] = []
    for route in routes:
        for item in route.get("evidence") or []:
            if isinstance(item, dict) and item.get("basis") == "assumption":
                detail = _scalar(item.get("detail"))
                if detail and detail not in out:
                    out.append(detail)
    if out:
        return out

    summary = body.get("source_summary")
    if isinstance(summary, dict):
        for text in _iter_strings(summary.get("assumptions")):
            if text not in out:
                out.append(text)
    return out


def _ab_test_plan(
    body: dict[str, Any],
    routes: Sequence[dict[str, Any]],
    hints: Sequence[RouteHints],
    warnings: list[str],
) -> ABTestPlan:
    """Return upstream's A/B plan, repaired, or synthesise one from the routes.

    `qa_review_agent` treats a missing or mis-referenced `ab_test_plan` as a
    BLOCKER (PLAN.AB_ROUTE_MISMATCH), and the real G7 plan has no `ab_test_plan`
    at all — the whole point of two creative routes is the comparison, so the
    absence is a formatting gap rather than a decision not to test. Synthesised
    plans name the two routes explicitly and carry the hypotheses upstream
    already wrote down.
    """
    route_ids = [h.route_id for h in hints]
    raw = _first(body, "ab_test_plan", "ab_test", "testing_plan")

    if isinstance(raw, dict):
        route_a = _scalar(_first(raw, "route_a", "a", "variant_a"))
        route_b = _scalar(_first(raw, "route_b", "b", "variant_b"))
        if route_a not in route_ids:
            route_a = route_ids[0]
            warnings.append("ab_test_plan.route_a did not name a real route; repointed.")
        if route_b not in route_ids:
            route_b = route_ids[1] if len(route_ids) > 1 else route_ids[0]
            warnings.append("ab_test_plan.route_b did not name a real route; repointed.")
        what, _ = strip_placeholders(_scalar(_first(raw, "what_to_test", "hypothesis", "test")))
        learning, _ = strip_placeholders(
            _scalar(_first(raw, "expected_learning", "learning", "outcome"))
        )
        metrics = _iter_strings(_first(raw, "success_metrics", "metrics", "kpis"))
        return ABTestPlan(
            what_to_test=what or _synth_what_to_test(hints),
            route_a=route_a,
            route_b=route_b,
            success_metrics=metrics or list(DEFAULT_SUCCESS_METRICS),
            expected_learning=learning or _synth_learning(body, routes, hints),
        )

    warnings.append(
        "Upstream plan carried no ab_test_plan; synthesised one from the "
        f"{len(route_ids)} creative route(s) so the A/B comparison is testable."
    )
    return ABTestPlan(
        what_to_test=_synth_what_to_test(hints),
        route_a=route_ids[0],
        route_b=route_ids[1] if len(route_ids) > 1 else route_ids[0],
        success_metrics=list(DEFAULT_SUCCESS_METRICS),
        expected_learning=_synth_learning(body, routes, hints),
    )


def _synth_what_to_test(hints: Sequence[RouteHints]) -> str:
    """Describe the comparison between the first two routes in one sentence."""
    if not hints:
        return "Creative route comparison."
    if len(hints) == 1:
        only = hints[0]
        return f"Single creative route {only.route_id} ({only.route_name or only.headline})."
    a, b = hints[0], hints[1]
    label_a = a.route_name or a.headline or f"route {a.route_id}"
    label_b = b.route_name or b.headline or f"route {b.route_id}"
    return (
        f"Creative route {a.route_id} vs route {b.route_id}: "
        f"“{label_a}” against “{label_b}”."
    )


def _synth_learning(
    body: dict[str, Any], routes: Sequence[dict[str, Any]], hints: Sequence[RouteHints]
) -> str:
    """Fill `expected_learning` from upstream's own hypotheses, never from nothing."""
    assumptions = _assumptions(body, routes)
    if assumptions:
        return " ".join(assumptions[:2])
    rationales = [
        _scalar(route.get("rationale")) for route in routes if _scalar(route.get("rationale"))
    ]
    if rationales:
        return " ".join(rationales[:2])
    ids = " / ".join(h.route_id for h in hints)
    return f"Which creative route ({ids}) converts better for this audience."


def _performance_learning(body: dict[str, Any]) -> PerformanceLearning | None:
    """Parse `performance_learning` when upstream supplied one; otherwise None.

    Nothing is invented here. The field is optional in the contract and a
    fabricated "what worked last time" would be a lie the studio then acts on.
    """
    raw = _first(body, "performance_learning", "past_performance", "learnings")
    if not isinstance(raw, dict):
        return None
    return PerformanceLearning(
        keep=_iter_strings(_first(raw, "keep", "continue")),
        change=_iter_strings(_first(raw, "change", "improve")),
        stop=_iter_strings(_first(raw, "stop", "drop")),
        test_next=_iter_strings(_first(raw, "test_next", "next", "experiments")),
    )


def parse_plan(raw: dict[str, Any], campaign_id: str) -> UpstreamPlan:
    """Adapt an upstream plan document into a `CampaignPlan` plus studio hints.

    `campaign_id` is authoritative: the research-shaped plan carries none, and
    where one is present it may disagree with the input document. `CampaignPlan`,
    `CampaignInput` and `AssetBundle` must all agree on the id or the store and
    the QA result end up filed under different campaigns, so the caller's value
    wins and any different upstream id is reported in `warnings`.

    Raises `UpstreamFormatError` when the document has no creative routes, which
    is the one thing the studio cannot work around: there is nothing to render.
    """
    if not campaign_id or not campaign_id.strip():
        raise UpstreamFormatError("campaign_id is required and must not be empty.")

    body = _plan_body(raw)
    warnings: list[str] = []

    upstream_id = _scalar(_first(body, "campaign_id", "id"))
    if upstream_id and upstream_id != campaign_id:
        warnings.append(
            f"Upstream plan campaign_id {upstream_id!r} replaced by {campaign_id!r} "
            "so plan, input and bundle stay filed together."
        )

    raw_routes = _first(body, "creative_routes", "routes")
    routes = [r for r in (raw_routes or []) if isinstance(r, dict)]
    if not routes:
        raise UpstreamFormatError(
            "Upstream plan has no creative_routes; there is nothing for the "
            "studio to render. Check that the planning agent finished."
        )
    if len(routes) < 2:
        warnings.append(
            f"Only {len(routes)} creative route(s) in the upstream plan; "
            "qa_review_agent requires at least 2 for A/B testing."
        )

    hints = [_route_hints(route, i) for i, route in enumerate(routes)]
    _dedupe_route_ids(hints, warnings)

    positioning_raw = _first(
        body, "positioning", "product_positioning", "positioning_statement"
    )
    positioning_body = positioning_raw if isinstance(positioning_raw, dict) else {}
    if not positioning_body:
        warnings.append("Upstream plan carried no positioning block; derived from routes.")

    angle, angle_removed = strip_placeholders(
        _scalar(_first(positioning_body, "main_campaign_angle", "campaign_angle", "angle"))
    )
    if not angle:
        angle = hints[0].headline or hints[0].route_name
        warnings.append(
            "positioning.main_campaign_angle was empty; used the first route's headline "
            "so PLAN.ANGLE_EMPTY does not block QA."
        )
    audience, audience_removed = strip_placeholders(
        _scalar(_first(positioning_body, "target_audience", "audience", "target_customer"))
    )
    message, message_removed = strip_placeholders(
        _scalar(_first(positioning_body, "key_selling_message", "selling_message", "message"))
    )

    benefits_raw = _first(
        positioning_body,
        "product_benefit_hierarchy",
        "benefit_hierarchy",
        "benefits",
    )
    if benefits_raw is None:
        benefits_raw = _first(body, "benefit_hierarchy", "product_benefit_hierarchy")
    benefits: list[str] = []
    stripped_benefits: list[str] = []
    for benefit in _ranked_strings(benefits_raw):
        cleaned, removed = strip_placeholders(benefit)
        stripped_benefits.extend(removed)
        if cleaned and cleaned not in benefits:
            benefits.append(cleaned)

    sources = _iter_strings(_first(positioning_body, "sources", "citations"))
    for url in _collect_sources(body.get("source_summary")):
        if url not in sources:
            sources.append(url)
    if not sources:
        for url in _collect_sources(positioning_body):
            if url not in sources:
                sources.append(url)
    if not sources:
        warnings.append(
            "No citations found anywhere in the upstream plan; "
            "qa_review_agent will raise MARKET.NO_SOURCES."
        )

    positioning = ProductPositioning(
        main_campaign_angle=angle,
        target_audience=audience,
        key_selling_message=message,
        product_benefit_hierarchy=benefits,
        sources=sources,
    )

    plan_kwargs: dict[str, Any] = {
        "campaign_id": campaign_id,
        "positioning": positioning,
        "creative_routes": [_creative_route(r, h) for r, h in zip(routes, hints)],
        "ab_test_plan": _ab_test_plan(body, routes, hints, warnings),
        "performance_learning": _performance_learning(body),
    }
    generated_at = _first(body, "generated_at", "created_at")
    if generated_at:
        plan_kwargs["generated_at"] = generated_at

    plan = CampaignPlan(**plan_kwargs)

    platforms: list[Platform] = []
    unsupported: list[str] = []
    for hint in hints:
        for platform in hint.platforms:
            if platform not in platforms:
                platforms.append(platform)
        for name in hint.unsupported_platforms:
            if name not in unsupported:
                unsupported.append(name)
    if unsupported:
        warnings.append(
            "No studio kit for requested platform(s): " + ", ".join(unsupported) + "."
        )
    if not platforms:
        warnings.append(
            "No route named a platform this studio has a kit for; "
            "the caller must choose one explicitly."
        )

    stripped = [
        *angle_removed,
        *audience_removed,
        *message_removed,
        *stripped_benefits,
        *[span for hint in hints for span in hint.stripped_placeholders],
    ]
    if stripped:
        warnings.append(
            f"Removed {len(stripped)} editorial placeholder(s) before any text can "
            "reach a prompt: " + "; ".join(stripped)
        )
    for hint in hints:
        residual = [
            text
            for text in (hint.headline, *hint.onscreen_text)
            if text and looks_editorial(text)
        ]
        if residual:
            warnings.append(
                f"Route {hint.route_id} on-screen text still reads as an editorial "
                "note; do not render it: " + "; ".join(residual)
            )
    if _performance_learning(body) is None:
        warnings.append(
            "Upstream plan carried no performance_learning; the studio has no prior "
            "campaign data to bias the look towards."
        )

    return UpstreamPlan(
        plan=plan,
        hints=hints,
        platforms=platforms,
        unsupported_platforms=unsupported,
        stripped_placeholders=stripped,
        warnings=warnings,
    )


def _dedupe_route_ids(hints: list[RouteHints], warnings: list[str]) -> None:
    """Force route ids to be unique and positional when upstream repeats or omits one.

    `qa_review_agent` blocks on PLAN.ROUTE_ID_DUP, and two routes sharing an id
    would also make the A/B plan ambiguous.
    """
    seen: set[str] = set()
    for index, hint in enumerate(hints):
        if hint.route_id in seen:
            replacement = (
                ROUTE_ID_ALPHABET[index] if index < len(ROUTE_ID_ALPHABET) else str(index + 1)
            )
            while replacement in seen:
                replacement += "'"
            warnings.append(
                f"Duplicate route_id {hint.route_id!r}; renamed to {replacement!r} by position."
            )
            hint.route_id = replacement
        seen.add(hint.route_id)


def load_plan(raw: dict[str, Any], campaign_id: str) -> CampaignPlan:
    """Adapt an upstream plan document into a validated `CampaignPlan`.

    The thin form of `parse_plan` for callers that only need the contract.
    Use `parse_plan` when you also need the extracted on-screen strings, the kho
    filenames upstream named, or the list of platforms that could not be served.
    """
    return parse_plan(raw, campaign_id).plan


# ---------------------------------------------------------------------------
# Input adapter
# ---------------------------------------------------------------------------


def _price_or_promotion(brief: dict[str, Any], warnings: list[str]) -> str | None:
    """Flatten the research shape's `price` object plus `promotion` into one string.

    `ProductBrief.price_or_promotion` is a single optional string; the research
    input splits it into a structured `{amount, currency, unit, note}` and a
    separate `promotion` sentence. Both are kept, joined, because the promotion
    is what the banner slot renders and the price is what the listing shows.
    """
    existing = _scalar(_first(brief, "price_or_promotion"))
    parts: list[str] = []
    if existing:
        parts.append(existing)

    price = brief.get("price")
    if isinstance(price, dict):
        amount = price.get("amount")
        currency = _scalar(price.get("currency"))
        unit = _scalar(price.get("unit"))
        if amount is not None:
            rendered = f"{amount:,.0f}".replace(",", ".") if isinstance(amount, (int, float)) else str(amount)
            chunk = " ".join(p for p in (rendered, currency) if p)
            if unit:
                chunk = f"{chunk} / {unit}"
            parts.append(chunk)
    elif isinstance(price, str) and price.strip():
        parts.append(price.strip())

    promotion, removed = strip_placeholders(_scalar(brief.get("promotion")))
    promotion, dropped = drop_editorial_clauses(promotion)
    if promotion:
        parts.append(promotion)
    for span in (*removed, *dropped):
        warnings.append(f"Removed editorial note from promotion, never render it: {span}")

    joined = " — ".join(p for p in parts if p)
    return joined or None


def _brand_colors(value: Any, warnings: list[str]) -> list[str]:
    """Flatten brand colours to strings, preferring a verified hex over a name.

    The research input models a colour as `{name, hex, verification_status}` and
    the real G7 brief has `hex: null` on all three, so the studio gets the
    Vietnamese colour names ("đỏ", "đen", "vàng đồng"). They are still usable as
    a palette hint in a prompt, but a consumer expecting `#RRGGBB` needs to know,
    so unverified colours are named in the warnings.
    """
    colors: list[str] = []
    unverified: list[str] = []

    for entry in value or []:
        if isinstance(entry, str):
            if entry.strip() and entry.strip() not in colors:
                colors.append(entry.strip())
            continue
        if not isinstance(entry, dict):
            continue
        hex_value = _scalar(entry.get("hex"))
        name = _scalar(entry.get("name"))
        if hex_value:
            if hex_value not in colors:
                colors.append(hex_value)
        elif name:
            if name not in colors:
                colors.append(name)
            unverified.append(name)

    if unverified:
        warnings.append(
            "Brand colour(s) have no hex value, only a name: "
            + ", ".join(unverified)
            + ". Prompts get a palette word, not a swatch."
        )
    return colors


def parse_input(raw: dict[str, Any], campaign_id: str) -> UpstreamInput:
    """Adapt an upstream research input document into a `CampaignInput` plus context.

    Absorbs both shapes seen in the wild: the canonical BP-01 shape
    (`price_or_promotion`, `forbidden_claims`, `logo_url`, `product_photo_urls`,
    scalar `language` / `market` / `trend`) and the research-agent shape
    (`price` + `promotion`, `restricted_claims`, `logo`, `product_photos`,
    plural `languages` / `markets` / `trends`). Everything the flattening loses
    — extra languages, unmappable platforms, unverified colours — is reported in
    `warnings` rather than dropped.

    Raises `UpstreamFormatError` when there is no product brief or no product
    name: without them there is no product to photograph.
    """
    if not campaign_id or not campaign_id.strip():
        raise UpstreamFormatError("campaign_id is required and must not be empty.")
    if not isinstance(raw, dict):
        raise UpstreamFormatError(
            f"Campaign input must be a JSON object, got {type(raw).__name__}."
        )

    warnings: list[str] = []
    stripped: list[str] = []

    brief_raw = _first(raw, "product_brief", "brief", "product")
    if not isinstance(brief_raw, dict):
        raise UpstreamFormatError(
            "Campaign input has no product_brief; the studio has no product to build a kit for."
        )

    product_name, name_removed = strip_placeholders(
        _scalar(_first(brief_raw, "product_name", "name", "title"))
    )
    stripped.extend(name_removed)
    if not product_name:
        raise UpstreamFormatError("product_brief.product_name is required and was empty.")

    category = _scalar(_first(brief_raw, "category", "product_category"))
    if not category:
        warnings.append(
            "product_brief.category is empty; art direction falls back to a generic look."
        )

    target_market = ", ".join(
        _iter_strings(_first(brief_raw, "target_market", "target_markets", "markets"))
    )
    if not target_market:
        warnings.append("product_brief.target_market is empty.")

    forbidden = _iter_strings(
        _first(brief_raw, "forbidden_claims", "restricted_claims", "banned_claims")
    )

    product_brief = ProductBrief(
        product_name=product_name,
        category=category,
        key_selling_points=[
            _tidy(strip_placeholders(p)[0])
            for p in _iter_strings(_first(brief_raw, "key_selling_points", "selling_points"))
            if strip_placeholders(p)[0]
        ],
        price_or_promotion=_price_or_promotion(brief_raw, warnings),
        target_market=target_market,
        required_claims=_iter_strings(_first(brief_raw, "required_claims", "must_claims")),
        forbidden_claims=forbidden,
    )

    kit_raw = _first(raw, "brand_kit", "brand") or {}
    photos = _iter_strings(_first(kit_raw, "product_photo_urls", "product_photos", "photos"))
    for extra in _iter_strings(kit_raw.get("existing_product_visuals")):
        # Appended after the clean product shots so photo[0] stays the Brand Lock
        # reference; inventory.py triages the rest and rejects what it cannot use.
        if extra not in photos:
            photos.append(extra)
    if not photos:
        warnings.append(
            "brand_kit has no product photos; there is no Brand Lock reference and "
            "every asset would have to be invented from scratch."
        )

    brand_kit = BrandKit(
        logo_url=_scalar(_first(kit_raw, "logo_url", "logo")) or None,
        brand_colors=_brand_colors(_first(kit_raw, "brand_colors", "colors"), warnings),
        tone_of_voice=", ".join(_iter_strings(_first(kit_raw, "tone_of_voice", "tone"))) or None,
        product_photo_urls=photos,
    )

    audience_raw = _first(raw, "audience_brief", "audience") or {}
    languages = _iter_strings(_first(audience_raw, "language", "languages"))
    if len(languages) > 1:
        warnings.append(
            f"Brief requests {len(languages)} languages ({', '.join(languages)}); "
            f"the contract holds one, so {languages[0]!r} is primary."
        )
    raw_platforms = _iter_strings(_first(audience_raw, "platform", "platforms", "channels"))
    platforms, unsupported = map_platforms(raw_platforms)
    if unsupported:
        warnings.append(
            "No studio kit for requested platform(s): " + ", ".join(unsupported) + "."
        )

    audience_brief = AudienceBrief(
        target_customer="; ".join(
            _iter_strings(_first(audience_raw, "target_customer", "target_customers", "audience"))
        ),
        language=languages[0] if languages else "",
        platform=raw_platforms,
        market=", ".join(_iter_strings(_first(audience_raw, "market", "markets"))),
    )

    signal_raw = _first(raw, "market_signal", "market_signals") or {}
    market_signal = MarketSignal(
        trend=_join_signal(signal_raw, "trend", "trends"),
        seasonal_moment=_join_signal(signal_raw, "seasonal_moment", "seasonal_moments"),
        consumer_pain_point=_join_signal(
            signal_raw, "consumer_pain_point", "consumer_pain_points"
        ),
        search_keyword=_join_signal(signal_raw, "search_keyword", "search_keywords"),
        competitor_angle=_join_signal(signal_raw, "competitor_angle", "competitor_angles"),
        campaign_objective=_join_signal(
            signal_raw, "campaign_objective", "campaign_objectives"
        ),
        sources=_iter_strings(_first(signal_raw, "sources", "citations")),
    )

    past_raw = _first(raw, "past_campaign_data", "past_performance")
    past = PastCampaignData(**_past_fields(past_raw)) if isinstance(past_raw, dict) else None

    upstream_id = _scalar(_first(raw, "campaign_id", "id"))
    if upstream_id and upstream_id != campaign_id:
        warnings.append(
            f"Upstream input campaign_id {upstream_id!r} replaced by {campaign_id!r} "
            "so plan, input and bundle stay filed together."
        )

    campaign_input = CampaignInput(
        campaign_id=campaign_id,
        product_brief=product_brief,
        brand_kit=brand_kit,
        audience_brief=audience_brief,
        market_signal=market_signal,
        past_campaign_data=past,
    )

    return UpstreamInput(
        campaign_input=campaign_input,
        platforms=platforms,
        unsupported_platforms=unsupported,
        stripped_placeholders=stripped,
        warnings=warnings,
    )


def _join_signal(signal: Any, singular: str, plural: str) -> str | None:
    """Read a market signal that may be a scalar or a list, and return one string.

    `MarketSignal` holds one string per signal; the research input holds a list.
    Entries that are already sentences are joined with a space, bare items
    ("Nescafé", "Vinacafé") with a semicolon, so the flattened value reads as
    written rather than as one run-on phrase.
    """
    values = _iter_strings(_first(signal, singular, plural))
    if not values:
        return None
    out = values[0]
    for previous, current in zip(values, values[1:]):
        out += (" " if previous.endswith((".", "!", "?")) else "; ") + current
    return out


def _past_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Pick the `PastCampaignData` fields out of an upstream performance block."""
    numeric = ("ctr", "cvr", "roas", "watch_time_sec", "add_to_cart_rate")
    fields: dict[str, Any] = {
        key: raw[key] for key in numeric if isinstance(raw.get(key), (int, float))
    }
    fields["comments"] = _iter_strings(raw.get("comments"))
    sales = _scalar(_first(raw, "sales_results", "sales"))
    if sales:
        fields["sales_results"] = sales
    return fields


def load_input(raw: dict[str, Any], campaign_id: str) -> CampaignInput:
    """Adapt an upstream research input document into a validated `CampaignInput`.

    The thin form of `parse_input`. Use `parse_input` when you also need the
    mapped platform kits or the list of things the flattening had to report.
    """
    return parse_input(raw, campaign_id).campaign_input


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def read_json(path: str | Path) -> dict[str, Any]:
    """Read one UTF-8 JSON document, reporting the path when it will not parse.

    A bare `JSONDecodeError` names a line and column but not a file, which is
    useless when the studio is loading two documents produced by two agents.
    """
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UpstreamFormatError(f"Upstream document not found: {file_path}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise UpstreamFormatError(f"{file_path} is not valid JSON: {exc}") from exc


def load_pair(
    plan_path: str | Path, input_path: str | Path, campaign_id: str
) -> tuple[CampaignPlan, CampaignInput]:
    """Load an upstream plan and its research input from disk as one matched pair.

    The two documents come from different agents and, in practice, from
    different runs, so they may disagree about the campaign id and about which
    schema version they were written against. Both are re-stamped with
    `campaign_id` so `CampaignPlan`, `CampaignInput` and the `AssetBundle` the
    studio produces all file under the same campaign.

    Returns `(plan, campaign_input)`. Call `parse_plan` / `parse_input` directly
    when the hints and warnings matter.
    """
    plan = load_plan(read_json(plan_path), campaign_id)
    campaign_input = load_input(read_json(input_path), campaign_id)
    return plan, campaign_input
