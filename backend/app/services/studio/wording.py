"""
Turning a planner's prose into strings short enough to set on artwork.

Copy is authored upstream and the studio only shortens it — inventing a slogan
is the one thing this codebase must never do, because a model asked to invent
lettering returns `LUNAÁIRA` and `EFFFECTIVE`. But upstream writes for a brief,
not for a frame: `hook_idea` arrives as a quoted sentence of nineteen words,
`key_selling_message` arrives with its own field name glued to the front, and
the offer arrives inside a price line. All three have to be reduced, and *how*
they are reduced is visible in the finished artwork.

This module exists because `direct.py` and `director.py` had grown one of these
each and they disagreed. On the same G7 brief — `"135.000đ / túi 50 gói · Mua 3
tặng 1 trong chiến dịch 9.9"` — the director's badge read `MUA 3 TẶNG 1` and the
worksheet's read `135.000Đ / TÚI 50 GÓI ·`: a price with a dangling separator
where the offer should have been. Two implementations of one idea is one too
many when the output is a marketplace banner.

The rule behind every function here: **drop whole units, never cut through
one.** A headline that loses a clause still reads; a headline cut at a character
count reads as a defect even when every glyph is correct. Measured on the real
plan, character truncation produced "Đặc sản Việt Nam vị đậm Robusta Buôn Ma" —
Buôn Ma Thuột is a city, and "Buôn Ma" is not.
"""
from __future__ import annotations

import re

#: Quote pairs upstream wraps its on-screen copy in. The quotes are markup —
#: they say "this is the line", they are not part of the line — so a headline
#: that keeps them renders a stray " in display type at the top of the frame.
_QUOTE_PAIRS: tuple[tuple[str, str], ...] = (
    ('"', '"'),
    ("'", "'"),
    ("“", "”"),
    ("‘", "’"),
    ("«", "»"),
)

#: Where a sentence may be broken without breaking a phrase: an em dash or a
#: middot separates two complete thoughts, a comma separates clauses within one.
#: A full stop only counts when whitespace follows, so `product_01.jpg` and
#: `135.000đ` stay in one piece — this is the rule that keeps a price from being
#: split at its own thousands separator.
_CLAUSE_RE = re.compile(r"\s*[–—;·]\s*|\s+-\s+|,\s+|(?<=[.!?])\s+")

#: A complete clause a little over the limit still sets better than the same
#: clause cut in half, so the limit is a target with give rather than a cliff.
#: "Đặc sản Việt Nam vị đậm Robusta Buôn Ma Thuột" is 45 characters against a
#: 42-character target; the slack is what keeps Buôn Ma Thuột whole.
DEFAULT_SLACK = 8

#: Planning output writes its own field names into its values — "Thông điệp bán
#: hàng cốt lõi: Cà phê đậm…". Taken whole, the label is what lands on the
#: poster: a real render came back reading "Thông điệp bán hàng cốt lõi: Cà phê
#: đậm" in display type.
_LABEL_RE = re.compile(r"^([^:：]{4,48})[:：]\s+(?=\S)")

#: Offer shapes, strongest first. Vietnamese character classes are a trap here:
#: `[ăa]` does not match "ặ", because ă and ặ are different characters rather
#: than one letter with a mark — `t[ăa]ng` silently failed on "tặng" and let a
#: freeship badge win over "MUA 3 TẶNG 1". Match whole words and let `\w` carry
#: the diacritics.
_OFFER_PATTERNS: tuple[str, ...] = (
    r"(mua\s*\d+\s*\w+\s*\d+)",           # mua 3 tặng 1
    r"(\w+\s*đến\s*\d+\s*%)",             # giảm đến 50%
    r"(\w+\s*\d+\s*%)",                   # giảm 25%
    r"(\d+\s*%\s*off)",
    r"(miễn\s*phí\s*vận\s*chuyển)",
    r"(freeship)",
    r"(free\s*ship)",
)


def clean(text: str | None) -> str:
    """Collapse whitespace and drop braces, which would break prompt formatting."""
    if not text:
        return ""
    return " ".join(str(text).replace("{", "").replace("}", "").split())


def unquote(text: str | None) -> str:
    """Remove the quotation marks upstream wrapped a line of copy in.

    Only a matched pair enclosing the whole string is removed. An apostrophe
    inside the line, or a quoted phrase within a longer sentence, is left alone:
    those are part of the copy.
    """
    value = clean(text)
    for opener, closer in _QUOTE_PAIRS:
        if len(value) > 2 and value.startswith(opener) and value.endswith(closer):
            return value[1:-1].strip()
    return value


def strip_label(text: str | None) -> str:
    """Drop a leading `Field name:` prefix, but only when it reads as one.

    Two things must not be stripped. A hook can open with a question — "Mệt buổi
    sáng? Pha nhanh…" — and an offer can open with a date — "11.11: giảm 25%",
    where the prefix carries the whole point. So a prefix is only a label when it
    runs to several words, holds no digits, and ends no sentence.
    """
    value = clean(text)
    match = _LABEL_RE.match(value)
    if not match:
        return value
    prefix = match.group(1).strip()
    if any(ch.isdigit() for ch in prefix):
        return value
    if any(ch in prefix for ch in ".?!"):
        return value
    if len(prefix.split()) < 2:
        return value
    return value[match.end():].strip()


def shorten(text: str | None, limit: int, slack: int = DEFAULT_SLACK) -> str:
    """Reduce copy to roughly `limit` characters by dropping clauses.

    Takes the longest run of leading clauses that fits, because the opening of a
    hook is what the hook is about. When even the first clause is too long, the
    shortest complete clause is preferred over a cut through the first one — a
    shorter true sentence beats a longer broken one. Character truncation is the
    last resort, and only for copy with no clause boundary at all.

    Quotation marks and field-name prefixes are removed first, so callers do not
    each have to remember to.
    """
    value = strip_label(unquote(text))
    if not value:
        return ""
    tolerance = limit + max(0, slack)
    if len(value) <= tolerance:
        return value

    # Cut at a boundary in the original string rather than re-joining the pieces,
    # so upstream's own punctuation survives: "135.000đ / túi 50 gói · Mua 3 tặng
    # 1" is written with a middot, and rebuilding it with a comma would quietly
    # restyle copy this module has no business restyling.
    kept = ""
    for boundary in (m.start() for m in _CLAUSE_RE.finditer(value)):
        head = value[:boundary].rstrip(" ,;:·—–-")
        if len(head) > tolerance:
            break
        kept = head
    if kept:
        return kept

    # Even the first clause is too long. A shorter whole clause reads better
    # than a longer broken one, so try the shortest before cutting anything.
    clauses = [c for c in (p.strip(" ,;:·") for p in _CLAUSE_RE.split(value)) if c]
    if clauses:
        shortest = min(clauses, key=len)
        if len(shortest) <= tolerance:
            return shortest
        return _hard_cut(shortest, limit)
    return _hard_cut(value, limit)


def _hard_cut(text: str, limit: int) -> str:
    """Last resort: cut at a word boundary and tidy the punctuation left behind."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.-·—–")
    return cut or text[:limit]


def offer_badge(text: str | None, limit: int = 22) -> str:
    """The offer inside a price line, as a badge reads it: a few words, loud.

    `"135.000đ / túi 50 gói · Mua 3 tặng 1 trong chiến dịch 9.9"` is a price line
    that happens to contain an offer; a badge wants `MUA 3 TẶNG 1`. Pulling the
    strongest fragment beats truncating, because a truncated offer — `135.000Đ /
    TÚI 50 GÓI ·` — is worse than no badge at all: it promises nothing and ends
    mid-punctuation.

    Returns "" when the line carries no offer, which is a legitimate answer. A
    campaign with no promotion should render no badge rather than a price
    pretending to be one.
    """
    value = clean(text)
    if not value:
        return ""
    for pattern in _OFFER_PATTERNS:
        found = re.search(pattern, value, re.IGNORECASE)
        if found:
            return _hard_cut(found.group(1).strip().upper(), limit)
    return ""
