"""
The look library - the studio's art direction vocabulary.

A *look* is one complete photographic recipe: a lens, a light, a surface and a
grade. Every image in a creative route is given the same four sentences, word
for word. That repetition is the entire mechanism by which eight images come
back looking like one photoshoot instead of eight unrelated pictures.

A campaign always ships two routes, A and B, so the seller can A/B test them.
`pick_looks` chooses that pair, and its one hard job is to make the two routes
genuinely different to the eye: if A and B are near-twins the test measures
nothing. The pair is therefore required to disagree on at least two of the
three `axes` below.

Four tables, one job each:

  LOOKS              the six recipes themselves.
  CATEGORY_LOOKS     product category  -> route A's look.
  MOOD_LOOKS         tone and trend    -> route A's look, when the category is
                                          unrecognised (e.g. a brief that is
                                          nothing but product photos).
  CONTRAST_PARTNERS  route A's look    -> the challenger to run against it.

This module is DATA. Read it as a mood board, not as code. Rewrite the wording,
add a look, re-point a category, and the studio's whole output changes with it.
Nothing here calls an API or touches a file.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# The three axes on which two looks are compared. They are deliberately coarse:
# they exist to answer one question - "would a shopper scrolling past notice
# these are different pictures?" - not to describe the look in full.
#
#   light     cool_diffuse | warm_window | hard_key | mixed_daylight | single_hard
#   contrast  low | mid | high
#   surface   clinical | domestic | studio | natural
AXES = ("light", "contrast", "surface")

# Two routes must disagree on at least this many axes to be worth A/B testing.
MIN_AXIS_DISTANCE = 2


@dataclass(frozen=True)
class Look:
    """One complete art direction.

    The four text fields are injected verbatim into the STYLE block of every
    prompt in a route - that repetition is what makes a kit look like a single
    shoot. `axes` is the machine-comparable summary used to guarantee that
    routes A and B are visually distant from each other.
    """

    lens: str
    light: str
    surface: str
    grade: str
    palette_hint: str
    axes: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The six looks
# ---------------------------------------------------------------------------
# Each one is a small brief you could hand to a photographer. Keep them
# concrete: "wet travertine" beats "a nice surface", because the image model
# renders nouns and ignores adjectives it cannot picture.

LOOKS: dict[str, Look] = {
    # Laboratory-clean. The default for serums, essences and anything that
    # sells on efficacy rather than on feeling.
    "clinical_lab": Look(
        lens="85mm macro, shallow depth of field",
        light="cool diffused softbox from the left, gentle falloff",
        surface="wet travertine and white acrylic",
        grade="neutral, low contrast, airy",
        palette_hint="white, pale grey, one cool accent",
        axes={"light": "cool_diffuse", "contrast": "low", "surface": "clinical"},
    ),
    # A real home in the morning. Sells ritual and habit: the coffee you make
    # every day, the chocolate you give someone.
    "warm_home": Look(
        lens="50mm, eye level",
        light="morning window sunlight with soft falling shadow",
        surface="washed linen and light oak",
        grade="warm, mid contrast, creamy highlights",
        palette_hint="cream, oat, warm wood",
        axes={"light": "warm_window", "contrast": "mid", "surface": "domestic"},
    ),
    # Deliberately unpolished - it should read as a customer's own photo, not
    # as advertising. Reserved for routes that past performance has proven.
    "street_ugc": Look(
        lens="35mm handheld, slight tilt",
        light="mixed uneven daylight, small blown highlights",
        surface="a real cluttered desk with everyday objects",
        grade="warm, high contrast, slight grain",
        palette_hint="unstyled everyday colour",
        axes={"light": "mixed_daylight", "contrast": "high", "surface": "domestic"},
    ),
    # Loud and graphic. Reads at thumbnail size on a scrolling feed, and is the
    # safe choice for a product category the studio does not recognise.
    "studio_pop": Look(
        lens="50mm, straight on",
        light="hard key light with a coloured rim",
        surface="seamless coloured backdrop",
        grade="saturated, high contrast, punchy",
        palette_hint="one bold brand colour plus white",
        axes={"light": "hard_key", "contrast": "high", "surface": "studio"},
    ),
    # Expensive and quiet. Hardware, premium confectionery, anything where the
    # object itself is the argument.
    "dark_luxe": Look(
        lens="100mm macro",
        light="single hard light with deep falloff",
        surface="black stone with a mirror reflection",
        grade="deep contrast, cool specular highlights",
        palette_hint="near-black, graphite, one metallic accent",
        axes={"light": "single_hard", "contrast": "high", "surface": "studio"},
    ),
    # Ingredients on a board. Food, drink, and the botanical end of beauty,
    # where the raw material is the story.
    "fresh_market": Look(
        lens="35mm, slightly above",
        light="bright even daylight",
        surface="a wooden board with fresh ingredients",
        grade="natural, saturated, clean whites",
        palette_hint="fresh greens and warm neutrals",
        axes={"light": "mixed_daylight", "contrast": "mid", "surface": "natural"},
    ),
}


# ---------------------------------------------------------------------------
# Category -> route A's look
# ---------------------------------------------------------------------------
# Read top to bottom: the FIRST row with a keyword appearing anywhere in the
# product category wins. Specific rows therefore sit above general ones, which
# is how "F&B / cà phê hoà tan" is read as coffee rather than as generic food.
#
# Matching is a plain case-folded substring test, so keep keywords long enough
# to be unambiguous. ("tea" would match "steamed"; "pin" would match "shopping".)

CATEGORY_LOOKS: tuple[tuple[tuple[str, ...], str], ...] = (
    # Vegan / botanical beauty, before general beauty: these brands sell the
    # plant, not the laboratory, so a lab bench is the wrong room for them.
    (
        ("thuần chay", "vegan", "botanical", "natural skincare", "organic skincare"),
        "fresh_market",
    ),
    # Skincare and cosmetics.
    (
        (
            "skincare", "chăm sóc da", "mỹ phẩm", "serum", "essence", "tinh chất",
            "cosmetic", "beauty", "kem dưỡng", "rửa mặt", "tẩy da chết",
            "body scrub", "sunscreen", "chống nắng",
        ),
        "clinical_lab",
    ),
    # Coffee: a warm daily ritual in almost every market that buys it.
    (("coffee", "cà phê", "ca phe", "cafe", "espresso"), "warm_home"),
    # Chocolate and fine confectionery: dark, glossy, given as a gift.
    (
        ("chocolate", "socola", "sô cô la", "cacao", "cocoa", "confection", "bean-to-bar"),
        "dark_luxe",
    ),
    # Consumer electronics: the object is the hero, lit like jewellery.
    (
        (
            "electronic", "điện tử", "power bank", "sạc", "charger", "gadget",
            "device", "tech", "công nghệ", "headphone", "audio",
        ),
        "dark_luxe",
    ),
    # Everything else edible or drinkable.
    (
        (
            "f&b", "food", "thực phẩm", "drink", "đồ uống", "beverage", "milk",
            "sữa", "juice", "nước ép", "snack", "bánh", "kẹo", "trà",
        ),
        "fresh_market",
    ),
)

# Used when the category is unrecognised - typically a brief that arrived as
# nothing but product photos. The brand's own tone words then choose the look.
MOOD_LOOKS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("luxury", "premium", "cao cấp", "sang trọng", "tinh tế", "elegant", "gifting"), "dark_luxe"),
    (("authentic", "honest", "real people", "chân thật", "gần gũi", "review", "unboxing"), "street_ugc"),
    (("clinical", "scientific", "khoa học", "dermatolog", "tinh khiết", "glass skin"), "clinical_lab"),
    (("cosy", "cozy", "morning", "ritual", "ấm áp", "thủ công", "handmade", "homely"), "warm_home"),
    (("fresh", "natural", "organic", "tươi", "thiên nhiên", "plant-based"), "fresh_market"),
    (("bold", "playful", "energetic", "punchy", "năng lượng", "trẻ trung", "vibrant"), "studio_pop"),
)

# Last resort. A hard key light on a seamless coloured backdrop flatters almost
# any object and reads at thumbnail size, so an unknown product still ships.
DEFAULT_LOOK = "studio_pop"


# ---------------------------------------------------------------------------
# Route A's look -> the challenger to run against it
# ---------------------------------------------------------------------------
# The art director's preferred pairings, chosen by eye. They are a preference,
# not a command: `pick_looks` only honours a pairing that is as far apart as the
# widest available, so a pair can never quietly become too similar to test.
#
# The table is intentionally not symmetric. The best challenger for "warm home"
# is not necessarily the look whose best challenger is "warm home".

CONTRAST_PARTNERS: dict[str, str] = {
    # Lab bench versus bathroom shelf: does efficacy or ritual sell better?
    "clinical_lab": "warm_home",
    # Morning ritual versus loud graphic: quiet habit or high energy?
    "warm_home": "studio_pop",
    # Customer's phone versus brand campaign: the classic UGC test.
    "street_ugc": "clinical_lab",
    # Loud versus clean, the widest possible swing for an unknown product.
    "studio_pop": "clinical_lab",
    # Hero object versus the same object living in someone's home.
    "dark_luxe": "warm_home",
    # Daylight kitchen versus dark café counter.
    "fresh_market": "dark_luxe",
}


# ---------------------------------------------------------------------------
# Performance learning override
# ---------------------------------------------------------------------------
# When past campaign data says a user-generated or testimonial route won, that
# measured result beats category convention: the proven look leads as route A
# and the category's own look becomes the challenger. Add a phrase here if the
# performance notes in your market use different wording.

UGC_LOOK = "street_ugc"
UGC_ROUTE_MARKERS = ("ugc", "testimonial", "người dùng thật", "khách hàng thật")


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def _match(text: str | None, table: tuple[tuple[tuple[str, ...], str], ...]) -> str | None:
    """Return the look key of the first table row whose keyword appears in `text`.

    Case-folded substring matching, top row first. Returns None when nothing
    matches, so the caller can fall through to the next table.
    """
    haystack = (text or "").casefold()
    for keywords, look_key in table:
        if any(keyword in haystack for keyword in keywords):
            return look_key
    return None


def _axis_distance(a: str, b: str) -> int:
    """Count how many of the three axes two looks disagree on (0 to 3)."""
    left, right = LOOKS[a].axes, LOOKS[b].axes
    return sum(1 for axis in AXES if left.get(axis) != right.get(axis))


def _pick_partner(primary: str) -> str:
    """Return the look that best contrasts with `primary`.

    Ranked, in order:
      1. widest axis distance - visible contrast is the point of an A/B test,
         and this is what stops a near-twin pairing such as dark_luxe with
         studio_pop, which share both contrast and surface;
      2. the art director's preferred partner from CONTRAST_PARTNERS;
      3. alphabetical order, so the same brief always produces the same pair.
    """
    candidates = [key for key in LOOKS if key != primary]
    preferred = CONTRAST_PARTNERS.get(primary)
    candidates.sort(
        key=lambda key: (
            -_axis_distance(primary, key),
            0 if key == preferred else 1,
            key,
        )
    )
    return candidates[0]


def pick_looks(
    category: str,
    tone: str = "",
    trend: str = "",
    winning_route: str | None = None,
) -> tuple[str, str]:
    """Choose the two looks for a campaign's A and B routes.

    Returns `(route_a_look_key, route_b_look_key)`, both keys into `LOOKS`. The
    caller takes index 0 for route A and index 1 for route B.

    The category chooses route A. When the category is unrecognised - a brief
    that arrived as bare product photos, say - the brand's tone and the market
    trend choose it instead, and `DEFAULT_LOOK` catches whatever is left.
    Route B is then the look that contrasts most strongly with route A.

    `winning_route` is the route that past campaign data says performed best.
    When it names a user-generated or testimonial route, `street_ugc` leads as
    route A and the category's own look becomes the challenger: a measured
    result outranks a convention. The two are always at least
    `MIN_AXIS_DISTANCE` axes apart, because `street_ugc` is far from every
    other look in the library.
    """
    primary = (
        _match(category, CATEGORY_LOOKS)
        or _match(f"{tone or ''} {trend or ''}", MOOD_LOOKS)
        or DEFAULT_LOOK
    )

    past_winner = (winning_route or "").casefold()
    if any(marker in past_winner for marker in UGC_ROUTE_MARKERS):
        if primary == UGC_LOOK:
            return UGC_LOOK, _pick_partner(UGC_LOOK)
        return UGC_LOOK, primary

    return primary, _pick_partner(primary)
