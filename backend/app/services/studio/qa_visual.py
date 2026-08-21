"""
Visual QA gate — the last node between a generated asset and a live listing.

Every image node in the studio graph ends here. `qa_review_agent` (teammate
owned) checks the *structure* of an `AssetBundle`: enough images, the right
kinds, a video of the right length. This module checks the *pixels*, and the
only thing it looks at is text, because text is the only part of a generated
image that can be wrong in a way a shopper will report.

Two design mistakes were made building this and corrected by experiment on
21/08/2026. Both are load-bearing; reintroducing either silently breaks the gate.

**1. The model transcribes; Python judges.**
Handed an image and a list of expected strings and asked for a verdict, the
vision model failed a perfectly correct asset — it counted the product bottle's
own printed label as "unexpected text". It is excellent at reading and poor at
deciding. So the only thing asked of it here is a verbatim transcription, and
every comparison happens below in code, where it is deterministic, debuggable
and unit-testable.

**2. Never downscale before inspecting.**
A whole 2048x2048 image times out past 180 seconds. Resizing it to 1024 makes
the model *silently auto-correct* the very defects the gate exists to detect: a
rendered `EFFFECTIVE` came back as `EFFECTIVE`. So the image is cropped into
native-resolution `QA_TILE_PX` tiles and the tiles are inspected in parallel.
Nothing is ever resized. There is a test pinning this.

The four defects it is built to catch, all observed in real output:

* **Wrong diacritics** — `PHUC HOI HANG RAO DA` is not `PHỤC HỒI HÀNG RÀO DA`.
  Seedream renders Vietnamese correctly when every string is named in the
  prompt, so this is a regression check, not an expected failure.
* **Invented brand names and taglines** — unprompted, the model wrote
  `LUNAÁIRA` and `CLEAN. GENTLE. EFFFECTIVE.` onto a skincare banner. The
  failure axis is *specified vs invented*, not Vietnamese vs English.
* **Redrawn packaging** — rendering a real COSRX bottle, the vertical wordmark
  on the black band came back as `COSRᴀ` in every generated image, while the
  same string set horizontally on the gold label was perfect. A misspelt brand
  name on a live listing is the most expensive thing this system can ship, so
  every `label_text` string is *required*, not merely permitted.
* **Forbidden claims** — a `forbidden_claims` string reaching an image is a
  marketplace takedown.

That last point creates an asymmetry worth stating plainly: `label_text` strings
are both **permitted** (they must never be reported as unexpected — that was
mistake one) and **required** (their absence or corruption is a failure).

Matching is normalised — NFC, casefold, whitespace collapsed — because
Vietnamese has several valid encodings for the same character and a naive `==`
produces false failures on correct work. A false failure costs a 50-second
regeneration, so the matcher is deliberately layered to survive the two ways a
correct string arrives looking broken: a rendered headline split across two
lines, and a string cut in half by a tile boundary.
"""
from __future__ import annotations

import io
import json
import math
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from PIL import Image

from app.services.studio import ark
from app.services.studio.config import studio_settings

# --------------------------------------------------------------------------
# tuning constants
#
# Global rule: tunables live in config.py. These four describe how *this*
# judgement reads, not how the studio is wired, and none of them is something
# an operator changes between runs, so they stay module-local rather than
# widening the settings surface. QA_TILE_PX, VISION_CONCURRENCY and
# QA_MAX_ATTEMPTS — the values that do get tuned — come from studio_settings.
# --------------------------------------------------------------------------

#: A transcript entry shorter than this is never flagged as an invented name.
#: Cutting a string at a tile seam leaves stubs like "X" or "DA"; they carry no
#: evidence either way and flagging them would fail correct work.
MIN_BRANDLIKE_CHARS = 3

#: Fraction of a string's letters that must be uppercase for it to "read as a
#: name". 0.6 keeps `LUNAÁIRA` and `CLEAN. GENTLE. EFFFECTIVE.` in and leaves
#: Vietnamese sentence case ("Tinh chất ốc sên 96%") out.
UPPERCASE_NAME_RATIO = 0.6

#: Units and measure words. `100ml` and `30ml / 1.01 fl.oz.` are not brand names.
UNIT_WORDS = frozenset(
    {
        "ml", "l", "cl", "dl", "g", "gr", "kg", "mg", "oz", "fl", "floz",
        "lb", "cm", "mm", "m", "in", "pcs", "pc", "ct", "pack", "kcal", "x",
    }
)

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_MEASURE_TOKEN_RE = re.compile(r"^\d+(?:[.,]\d+)?([a-z]{1,4})?$", re.UNICODE)

#: The only thing ever asked of the vision model. It says "transcribe" four
#: different ways on purpose: every softer phrasing tried during research
#: produced a tidied-up reading instead of what is actually on the pixels, and a
#: tidied-up reading is worse than no reading at all — it passes a broken asset.
TRANSCRIBE_PROMPT = (
    "Transcribe every piece of text visible in this image, character by character, "
    "exactly as rendered. Include text printed on product packaging and labels, "
    "including text that is rotated or runs vertically. "
    "Preserve misspellings, doubled letters, and missing or wrong diacritics exactly "
    "as they appear. Do not correct anything. Do not translate anything. "
    "Do not guess at or complete a word that is cut off at the edge of the frame — "
    "transcribe only the characters you can actually see. "
    "Return a JSON array of strings and nothing else. If there is no text, return []."
)


@dataclass
class VisualVerdict:
    """The result of inspecting one image. Produced by `inspect_image`.

    `passed` is true only when all three defect lists are empty; the studio
    treats anything else as a regeneration trigger and feeds the verdict to
    `corrective_hint`.

    * `missing_text` — expected marketing strings *and* `label_text` strings
      that could not be found. A corrupted brand name shows up here when the
      corruption destroyed the only copy of it, and in `unexpected_brandlike`
      when a correct copy also appears elsewhere in the frame.
    * `unexpected_brandlike` — strings that read as a name or a tagline and
      belong to neither list. This is where invented brands (`LUNAÁIRA`) and
      redrawn packaging (`COSRᴀ`) land.
    * `forbidden_hits` — the campaign's `forbidden_claims` found in the pixels.
    * `transcript` — the deduplicated union of every tile transcription, in
      reading order. Kept on the verdict because when this gate is wrong, the
      transcript is the only way to tell whether the model misread the image or
      the judge misread the model.
    * `notes` — human-readable explanations, shaped to drop straight into
      `ImageAsset.qa_notes`.
    * `elapsed_sec` — wall-clock of the vision calls. This gate is the slowest
      non-video step in the studio, so its cost is measured, not assumed.
    """

    passed: bool = True
    missing_text: list[str] = field(default_factory=list)
    unexpected_brandlike: list[str] = field(default_factory=list)
    forbidden_hits: list[str] = field(default_factory=list)
    transcript: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    elapsed_sec: float = 0.0


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------

def normalise(text: str) -> str:
    """Fold a string to the form every comparison in this module uses.

    NFC first, because Vietnamese has two valid encodings for every stacked
    diacritic (`Ệ` is one code point or three) and the model returns whichever
    its tokenizer emitted; a naive `==` fails correct work about half the time.
    Then casefold, then collapse internal whitespace, because a rendered
    headline arrives with line breaks the prompt never asked for.

    Casefolding is applied before the final NFC pass so that a decomposed input
    still composes afterwards.
    """
    return " ".join(unicodedata.normalize("NFC", text.casefold()).split())


def _tokens(text: str) -> list[str]:
    """Alphanumeric runs of a normalised string, punctuation discarded."""
    return _TOKEN_RE.findall(normalise(text))


def _squash(text: str) -> str:
    """Normalised text with every space removed.

    Used as the last-resort matcher: a string cut by a tile seam comes back as
    two entries (`COSR`, `X`) that no whitespace-preserving comparison can
    reunite, but their concatenation is the original.
    """
    return normalise(text).replace(" ", "")


def _levenshtein(a: str, b: str) -> int:
    """Edit distance, used only to explain a defect, never to decide one."""
    if a == b:
        return 0
    if not a or not b:
        return len(a) or len(b)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            )
        previous = current
    return previous[-1]


# --------------------------------------------------------------------------
# tiling — native resolution, never a resize
# --------------------------------------------------------------------------

def _tile_origins(size: int, tile: int) -> list[int]:
    """Left/top offsets of the tiles covering one axis, at native resolution.

    The count is the minimum that covers the axis: a 2048px side gives exactly
    two 1024px tiles — the four quadrants the measurement prescribes — and any
    other side length gives edge-anchored tiles that overlap in the middle
    rather than leaving a gap. A 1440px side gives offsets 0 and 416, so the
    608px of overlap covers a centred headline in one piece; a 2560px side gives
    0, 768 and 1536. An axis shorter than one tile gives a single offset and the
    crop is padded, never upscaled.
    """
    if size <= tile:
        return [0]
    count = math.ceil(size / tile)
    span = size - tile
    return [round(i * span / (count - 1)) for i in range(count)]


def tile_image(source: str | Path | bytes, tile_px: int | None = None) -> list[bytes]:
    """Cut an image into native-resolution square tiles, in reading order.

    Returns JPEG bytes per tile, row-major (left to right, top to bottom), which
    is also the order the transcripts are concatenated in — the join is what
    lets a string split across a tile boundary still be recognised.

    Tiles are **crops**, never resizes. A 1024x1024 payload answers in 41–109
    seconds; the whole 2048x2048 image times out past 180, and downscaling it
    first makes the model quietly repair the defects this gate exists to find.
    Any region falling outside the source is filled white rather than black, so
    a padded tile of a small photo still looks like a product shot to the model.
    """
    tile = tile_px or studio_settings.QA_TILE_PX
    raw = source if isinstance(source, (bytes, bytearray)) else Path(source).read_bytes()
    with Image.open(io.BytesIO(bytes(raw))) as opened:
        image = opened.convert("RGB")

    width, height = image.size
    tiles: list[bytes] = []
    for top in _tile_origins(height, tile):
        for left in _tile_origins(width, tile):
            canvas = Image.new("RGB", (tile, tile), (255, 255, 255))
            crop = image.crop(
                (left, top, min(left + tile, width), min(top + tile, height))
            )
            canvas.paste(crop, (0, 0))
            buffer = io.BytesIO()
            canvas.save(buffer, format="JPEG", quality=95)
            tiles.append(buffer.getvalue())
    return tiles


# --------------------------------------------------------------------------
# transcription
# --------------------------------------------------------------------------

def parse_transcript(raw: str) -> list[str]:
    """Turn one model reply into a list of strings.

    The prompt asks for a bare JSON array and usually gets one, but the reply
    also arrives fenced in ``` blocks or with a sentence in front of it. A
    transcription is too expensive to throw away over punctuation, so this
    peels the fence, takes the outermost bracketed span, and falls back to
    reading quoted or line-separated fragments.
    """
    if not raw:
        return []
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    start, end = text.find("["), text.rfind("]")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

    quoted = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', text)
    if quoted:
        return [q.strip() for q in quoted if q.strip()]

    return [line.strip(" -\t") for line in text.splitlines() if line.strip(" -\t")]


def transcribe_tiles(tiles: Sequence[bytes], concurrency: int | None = None) -> tuple[list[list[str]], list[str]]:
    """Transcribe every tile in parallel. Returns `(per_tile_strings, notes)`.

    Calls run concurrently because a single tile takes 41–109 seconds and the
    tiles are independent; serialising four of them would put the gate on the
    same order as the render it is checking.

    A tile that fails to transcribe is recorded as a note and the remaining
    tiles are still judged. Failing the whole gate on one flaky vision call
    would block an asset that is probably fine, but a partial inspection can
    miss a defect, so the gap is always written down rather than swallowed.
    """
    workers = max(1, min(concurrency or studio_settings.VISION_CONCURRENCY, len(tiles) or 1))
    notes: list[str] = []

    def read_one(index_and_tile: tuple[int, bytes]) -> list[str]:
        index, tile = index_and_tile
        try:
            return parse_transcript(ark.describe_image(tile, TRANSCRIBE_PROMPT))
        except Exception as exc:  # noqa: BLE001 - a dead tile must not kill the gate
            notes.append(f"tile {index}: transcription failed ({type(exc).__name__}: {exc})")
            return []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        per_tile = list(pool.map(read_one, enumerate(tiles)))
    return per_tile, notes


# --------------------------------------------------------------------------
# judgement — all of it in Python, none of it in the model
# --------------------------------------------------------------------------

def _is_measurement(text: str) -> bool:
    """True when a string is only numbers and units, e.g. `100ml`, `96%`.

    Volumes and percentages appear on every product shot and are never brand
    names, so they are excluded from the invented-name check before anything
    else looks at them.
    """
    remaining = []
    for token in _tokens(text):
        if token in UNIT_WORDS:
            continue
        match = _MEASURE_TOKEN_RE.match(token)
        if match and (match.group(1) is None or match.group(1) in UNIT_WORDS):
            continue
        remaining.append(token)
    return not remaining


def _is_brandlike(text: str) -> bool:
    """True when a string reads as a name or a tagline rather than a sentence.

    Two accepted shapes: mostly uppercase (`LUNAÁIRA`, `CLEAN. GENTLE.
    EFFFECTIVE.`, `COSRᴀ`) or title case (`Advanced Snail`). Vietnamese
    sentence case such as `Tinh chất ốc sên 96%` matches neither, which is the
    point — that is body copy, not a brand the model invented.
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    if sum(1 for c in letters if c.isupper()) / len(letters) >= UPPERCASE_NAME_RATIO:
        return True
    words = [w for w in re.split(r"[\s.,;:!?/|()\[\]-]+", text) if w and w[0].isalpha()]
    return bool(words) and all(w[0].isupper() for w in words)


def _is_present(needle: str, entries: list[str], haystack: str, haystack_tokens: set[str], squashed: str) -> bool:
    """Decide whether one required string made it into the picture.

    Three layers, tried in order, each answering a different way a correct
    string arrives looking broken:

    1. **Substring of the joined transcript.** Covers the ordinary case and a
       headline the model split over two lines, since the tiles are joined in
       reading order.
    2. **Every token present.** Covers a string cut by a tile seam and read as
       two overlapping halves (`HÀNG RÀO D` + `NG RÀO DA`). Tokens are compared
       with their diacritics intact, so this loosens word boundaries and
       nothing else — `phuc` still does not satisfy `phục`.
    3. **Whitespace-squashed substring.** Covers a short single-token string
       sheared in half at a seam (`COSR` + `X`).

    None of the three can rescue a wrong diacritic or a doubled letter, which is
    what keeps the gate honest while making it survive its own tiling.
    """
    target = normalise(needle)
    if not target:
        return True
    if target in haystack:
        return True
    if any(target == normalise(entry) for entry in entries):
        return True
    target_tokens = _tokens(needle)
    if target_tokens and all(token in haystack_tokens for token in target_tokens):
        return True
    return _squash(needle) in squashed


def _accounted_for(entry: str, permitted: list[str]) -> bool:
    """True when a transcript entry is explained by a string we asked for.

    Containment runs both ways on purpose. A tile seam or a line break turns one
    requested string into several fragments (`Adva`, `nced`, `PHỤC HỒ`), each a
    substring of the original; conversely the model merges two requested lines
    into one entry that contains them. Both are correct work and neither may be
    reported as an invented name — that is exactly the mistake the vision model
    made when it was asked to judge for itself.

    `COSRᴀ` survives this filter because `cosra` is a substring of nothing we
    asked for, which is how the redrawn-packaging defect is caught.
    """
    normalised = normalise(entry)
    if not normalised:
        return True
    return any(normalised in item or item in normalised for item in permitted)


def inspect_image(
    path: str | Path | bytes,
    expected_texts: Sequence[str] = (),
    label_text: Sequence[str] = (),
    forbidden_claims: Sequence[str] = (),
    *,
    tile_px: int | None = None,
    concurrency: int | None = None,
) -> VisualVerdict:
    """Inspect one generated image and return a `VisualVerdict`.

    `path` is a file on disk or raw image bytes. `expected_texts` are the
    marketing strings the prompt asked for; `label_text` is what is printed on
    the product's own packaging; `forbidden_claims` come straight from
    `campaign_input.product_brief.forbidden_claims`.

    `label_text` is treated as both permitted and **required**: permitted so the
    bottle's own label is never reported as unexpected text, required because a
    redrawn label misspelling the brand name is the most expensive defect this
    system can ship, and it has been observed in every generated frame of a real
    product (`COSRᴀ` for `COSRX`).

    The image is cropped into native-resolution tiles and transcribed in
    parallel; every comparison after that happens here in Python. Budget 41–109
    seconds per tile wave — four tiles run as one wave.
    """
    started = time.time()
    tiles = tile_image(path, tile_px)
    per_tile, notes = transcribe_tiles(tiles, concurrency)

    # Reading order matters: it is what makes a string split across a seam
    # reappear when the transcripts are joined.
    transcript: list[str] = []
    seen: set[str] = set()
    for entries in per_tile:
        for entry in entries:
            key = normalise(entry)
            if key and key not in seen:
                seen.add(key)
                transcript.append(entry.strip())

    haystack = " ".join(normalise(entry) for entry in transcript)
    haystack_tokens = set(_TOKEN_RE.findall(haystack))
    squashed = haystack.replace(" ", "")

    # Two parallel lists: normalised forms to compare against, and the strings
    # as the brief wrote them, so a note can quote the brand name back.
    requested = [s for s in list(expected_texts) + list(label_text) if normalise(s)]
    permitted = [normalise(s) for s in requested]

    required: list[tuple[str, bool]] = [(s, False) for s in expected_texts if s.strip()]
    required += [(s, True) for s in label_text if s.strip()]

    missing: list[str] = []
    for needle, is_label in required:
        if _is_present(needle, transcript, haystack, haystack_tokens, squashed):
            continue
        missing.append(needle)
        notes.append(
            f"required label text {needle!r} was not readable — a wrong brand name "
            f"on a listing is not recoverable"
            if is_label
            else f"expected text {needle!r} was not rendered as written"
        )

    unexpected: list[str] = []
    flagged: set[str] = set()
    for entry in transcript:
        normalised = normalise(entry)
        if len(normalised) <= MIN_BRANDLIKE_CHARS or normalised in flagged:
            continue
        if _accounted_for(entry, permitted) or _is_measurement(entry):
            continue
        if not _is_brandlike(entry):
            continue
        flagged.add(normalised)
        unexpected.append(entry)
        near = _nearest_permitted(normalised, permitted, requested)
        notes.append(
            f"{entry!r} looks like a corrupted rendering of {near!r} — the model "
            f"redrew the packaging"
            if near
            else f"{entry!r} is text nobody asked for"
        )

    forbidden: list[str] = []
    for claim in forbidden_claims:
        needle = normalise(claim)
        if not needle:
            continue
        if needle in haystack or any(needle in normalise(e) for e in transcript):
            forbidden.append(claim)
            notes.append(f"forbidden claim {claim!r} is visible in the image")

    return VisualVerdict(
        passed=not (missing or unexpected or forbidden),
        missing_text=missing,
        unexpected_brandlike=unexpected,
        forbidden_hits=forbidden,
        transcript=transcript,
        notes=notes,
        elapsed_sec=round(time.time() - started, 1),
    )


def _nearest_permitted(normalised: str, permitted: list[str], requested: list[str]) -> str | None:
    """The requested string a flagged entry is one or two edits away from.

    Explanation only — the entry is already flagged by the time this runs. It
    exists so the note reads "COSRA looks like a corrupted rendering of COSRX"
    instead of "unexpected text", which is the difference between a log line an
    operator can act on and one they ignore. `requested` holds the strings as
    the brief wrote them, so the brand name is quoted back in its own casing.
    """
    best: tuple[int, str] | None = None
    for index, candidate in enumerate(permitted):
        budget = max(1, min(len(normalised), len(candidate)) // 4)
        distance = _levenshtein(normalised, candidate)
        if distance <= budget and (best is None or distance < best[0]):
            best = (distance, requested[index])
    return best[1] if best else None


# --------------------------------------------------------------------------
# regeneration
# --------------------------------------------------------------------------

def corrective_hint(verdict: VisualVerdict, attempt: int = 1) -> str:
    """The instruction appended to the prompt when an asset is re-rendered.

    `attempt` is the retry about to be made, so it starts at 1 and stops at
    `studio_settings.QA_MAX_ATTEMPTS`. The escalation is deliberate: the model
    renders text reliably in proportion to how little of it there is, so the
    first retry asks for less text drawn larger, and the second abandons the
    layout and demands a single string with nothing else in frame. Repeating the
    same instruction twice reliably produced the same defect twice.

    An invented name is always quoted back in the negative instruction. "Do not
    add extra text" is ignored; "Do not render the words 'LUNAÁIRA'" is not.

    Returns an empty string for a passing verdict, so a caller can append it
    unconditionally.
    """
    parts: list[str] = []

    if verdict.forbidden_hits:
        claims = ", ".join(f'"{c}"' for c in verdict.forbidden_hits)
        parts.append(
            f"Never render these words anywhere in the image: {claims}. "
            f"They are prohibited marketing claims."
        )

    if verdict.unexpected_brandlike:
        hits = ", ".join(f'"{h}"' for h in verdict.unexpected_brandlike)
        parts.append(
            f"Do not render the words {hits}. No text on background surfaces or "
            f"packaging other than the product's own label."
        )

    if verdict.missing_text:
        if attempt >= 2:
            only = verdict.missing_text[0]
            parts.append(
                f'Render exactly one text string: "{only}". No other text anywhere.'
            )
        else:
            wanted = ", ".join(f'"{t}"' for t in verdict.missing_text)
            parts.append(
                f"Reduce the amount of text. Render only: {wanted}. "
                f"Make them larger and unobstructed. Spell every character and "
                f"every diacritic exactly as written."
            )
    elif verdict.unexpected_brandlike and attempt >= 2:
        parts.append("Render no text anywhere except the product's own printed label.")

    return " ".join(parts)
