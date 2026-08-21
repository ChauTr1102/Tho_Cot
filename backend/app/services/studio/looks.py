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
# Each one is a small brief you could hand to a photographer, and the standard
# is a lighting diagram rather than an adjective. Four rules, all of them
# learned from looking at output rather than from theory:
#
#   lens     names a focal length AND an aperture. "85mm macro, shallow depth
#            of field" is a wish; "100mm macro at f/8, focus-stacked" is an
#            instruction, and the f-number is what actually moves the image.
#   light    describes a SETUP - key, fill, modifier, direction, what the
#            shadow does - not a weather condition. "bright even daylight"
#            produced a supermarket flyer; "hard sun through a slatted blind
#            raking from back-left" produced a campaign.
#   surface  describes a SET, not a noun. "a wooden board with fresh
#            ingredients" is a prop list; a set says what is on the table,
#            where it is, and what has already happened on it.
#   grade    describes a LOOK - black point, split tone, grain, saturation
#            discipline - not a mood word.
#
# Concrete beats abstract throughout: the model renders nouns and named
# techniques, and ignores adjectives it cannot picture. Every look is also
# written to hold one disciplined palette - warm subject against one cool
# shadow tone - because an undisciplined palette is the single thing that most
# reliably makes a generated image read as stock rather than as advertising.

LOOKS: dict[str, Look] = {
    # Laboratory-clean. The default for serums, essences and anything that
    # sells on efficacy rather than on feeling. The setup is the cosmetics
    # advertising standard: a big overhead scrim for weightless shadows,
    # clamshell fill from below, and a gridded strip behind the bottle so the
    # liquid inside lights up.
    "clinical_lab": Look(
        lens="100mm macro at f/8, focus-stacked so the label stays sharp corner to corner",
        light=(
            "a large diffusion scrim overhead and a white clamshell bounce below, both out of frame, "
            "filling the shadow to almost nothing, and a gridded strip softbox hidden behind the "
            "product throwing a cold edge light through the liquid"
        ),
        surface=(
            "a pale grey-to-white gradient sweep, a low frosted acrylic riser at its centre, a "
            "shallow film of water returning one clean mirror reflection, a few deliberate "
            "droplets, nothing else"
        ),
        grade=(
            "high-key and airy, lifted blacks, near-neutral white balance with one cool cyan cast "
            "held in the shadows, low contrast, no grain"
        ),
        palette_hint="paper white, pale grey, water-clear, one cool cyan accent",
        axes={"light": "cool_diffuse", "contrast": "low", "surface": "clinical"},
    ),
    # A real home in the morning. Sells ritual and habit: the coffee you make
    # every day, the chocolate you give someone. One window, one cookie, one
    # black flag - the cheapest lighting diagram in advertising and still the
    # most persuasive, because it is the light the buyer already lives in.
    "warm_home": Look(
        lens="50mm at f/2.0 at eye level across the table, the far side of the room out of focus",
        light=(
            "one soft window as the only key, from camera-left and slightly behind, broken by a "
            "cookie so a dappled leaf shadow falls across the table, a black flag just out of frame "
            "opposite for negative fill so the shadow side stays rich instead of grey"
        ),
        surface=(
            "a linen-covered oak table beside that window, a folded napkin, a ceramic cup ringed "
            "with coffee, a brass spoon and a jug of milk within arm's reach of someone who has "
            "just sat down"
        ),
        grade=(
            "warm and creamy, gently lifted shadows, split-toned amber highlights against a cool "
            "blue shade, mid contrast, fine Portra 400 grain"
        ),
        palette_hint="cream, oat, honey, warm oak, one cool blue shade tone",
        axes={"light": "warm_window", "contrast": "mid", "surface": "domestic"},
    ),
    # Deliberately unpolished - it should read as a customer's own photo, not
    # as advertising. Not sloppy, though: direct on-camera flash against warm
    # room light is a deliberate, current commercial look, and it is what makes
    # a phone snapshot read as authentic rather than as a bad photograph.
    # Reserved for routes that past performance has proven.
    "street_ugc": Look(
        lens="26mm phone camera at f/1.8, handheld a little too close and a few degrees off level",
        light=(
            "direct on-camera phone flash as the key against warm apartment tungsten, a hard-edged "
            "shadow thrown on the wall right behind, mixed colour temperature left uncorrected, "
            "one window corner blown out"
        ),
        surface=(
            "a real desk in a rented flat with the edge of a laptop, an open notebook, a set of "
            "keys and an iced coffee sweating a ring into the wood"
        ),
        grade=(
            "punchy phone-camera contrast, crushed blacks, over-sharpened edges, a green tungsten "
            "cast the phone failed to correct, visible sensor noise in the shadows"
        ),
        palette_hint="unstyled everyday colour with one blown flash-white hotspot",
        axes={"light": "mixed_daylight", "contrast": "high", "surface": "domestic"},
    ),
    # Loud and graphic. Reads at thumbnail size on a scrolling feed, and is the
    # safe choice for a product category the studio does not recognise. Hard
    # bare-bulb key plus a gelled kicker: a poster, not a photograph.
    "studio_pop": Look(
        lens="85mm at f/8, straight on at product centre height, sharp front to back",
        light=(
            "one bare-bulb hard key high camera-right cutting a crisp graphic shadow to the left, "
            "a gelled kicker opposite rimming the product in a saturated complementary colour, a "
            "bright halo burnt onto the sweep behind it by a gridded light out of frame, nothing "
            "soft anywhere"
        ),
        surface=(
            "a saturated seamless colour sweep, a stepped colour-block plinth at its centre, one "
            "hard sun-shaped shadow cut across the sweep, one or two geometric props placed like "
            "a poster layout"
        ),
        grade=(
            "high saturation, deep contrast, punchy blacks, colours pushed to poster strength, "
            "crisp digital cleanliness, no grain"
        ),
        palette_hint="one bold brand colour at full strength, its complementary as the rim, white",
        axes={"light": "hard_key", "contrast": "high", "surface": "studio"},
    ),
    # Expensive and quiet. Hardware, premium confectionery, anything where the
    # object itself is the argument. Classic low-key chiaroscuro: one snooted
    # key carves the form, black flags kill everything else, the object floats
    # out of the dark on its own reflection.
    "dark_luxe": Look(
        lens=(
            "100mm macro at f/2.8, low three-quarter hero angle looking slightly up so the "
            "product towers"
        ),
        light=(
            "a single snooted hard key from high back-left carving one bright edge down the front "
            "face and letting the rest fall to black, a gridded strip behind camera-right as a "
            "cold specular rim, black flags out of frame either side"
        ),
        surface=(
            "a black acrylic tabletop returning one clean mirror reflection, an unlit room behind it, "
            "a faint pool of light on the far wall, slow smoke drifting through the beam"
        ),
        grade=(
            "low-key chiaroscuro, crushed blacks, one warm specular highlight against cold "
            "graphite shadow, deep contrast, gentle halation on the brightest edges"
        ),
        palette_hint="near-black, graphite, one warm metallic accent",
        axes={"light": "single_hard", "contrast": "high", "surface": "studio"},
    ),
    # Food, drink, and the botanical end of beauty, where the raw material is
    # the story. This is NOT flat daylight on a chopping board - that reads as a
    # supermarket flyer. It is hard directional sun through a slatted blind:
    # long striped shadows, one cool shadow tone against warm highlights, and
    # the ingredient caught doing something rather than merely lying there.
    "fresh_market": Look(
        lens="35mm at f/4 from just above the tabletop, tilted a few degrees down",
        light=(
            "hard late-morning sun through a slatted blind as the only key, raking from back-left "
            "so long striped shadows run diagonally across the table, a white bounce card "
            "just out of frame camera-right opening the shadow side"
        ),
        surface=(
            "a pale sun-bleached wooden table laid for a real morning, the raw ingredient scattered loose "
            "across it, a linen cloth pushed aside, a glass and a ceramic bowl, condensation "
            "beading and one spill left where it fell"
        ),
        grade=(
            "sunlit and natural, warm cream highlights against one cool shadow tone, mid contrast, "
            "clean whites, fine film grain, saturation held back"
        ),
        palette_hint="warm cream and toasted amber against one cool shadow tone, a single fresh green",
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
