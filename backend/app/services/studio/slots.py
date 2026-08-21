"""
Scene templates - what actually happens inside each frame, and the storyboard
of the ad.

`SLOT_SCENES` gives every kit slot one sentence of staging. The sentence is
deliberately incomplete: `{surface}` and `{light}` are filled in from the
route's look. So the same slot is shot on wet travertine under a cool softbox
in route A and on washed linen in morning sun in route B, while the staging -
what the product is doing, where the eye goes, where the text sits - stays
identical. Slot describes the *shot*; look describes the *room*.

`SHOT_TEMPLATES` is the ad itself: four beats, hook, product, benefit, cta.

This module is DATA. Every string here is written to be rewritten. Five rules
to keep in mind while rewriting, four of them learned from looking at output:

  * The only placeholders allowed in a scene are `{surface}` and `{light}`.
    Any other brace will raise when the prompt is assembled.
  * Nouns beat adjectives. "a wooden board with fresh ingredients" renders;
    "a lovely natural feel" does not.
  * A scene states a COMPOSITION, not a location. "three products arranged on
    a board" is a location; "three in a tight overlapping row, the nearest
    turned three-quarters, the two behind falling out of focus" is a picture.
  * A scene states an EVENT. Props that are merely present read as a
    supermarket flyer; props that are doing something - a pour frozen
    mid-arc, steam curling, an ingredient still falling - read as a campaign.
    Every scene therefore names the product's own material in motion, in a
    form general enough that the model picks the right one for the category.
  * A scene that carries copy must RESERVE THE SPACE FOR IT, out loud. This is
    measured, not stylistic: the same headline that rendered correctly over a
    frame whose scene said "generous empty space in the top third" vanished
    entirely from a busier frame whose scene did not say it. Elaborate staging
    and legible type are not in tension, but the negative space has to be
    written down.
"""
from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# The text vocabulary
# ---------------------------------------------------------------------------
# Every string that appears inside a frame is named here and nowhere else. This
# matters more than it looks: text the image model invents comes back garbled
# ("LUNAÁIRA", "EFFFECTIVE"), while text it is told to render comes back exact,
# in Vietnamese as well as English. So the studio never lets the model choose a
# word - it hands it the words.
#
# `SlotSpec.text_keys` and `ShotTemplate.text_key` may only use these keys. The
# right-hand side records which field of the brief or the plan fills each one.

TEXT_KEYS: dict[str, str] = {
    "headline": "the route's hook line - plan.creative_routes[route].hook_idea",
    "benefit": "the single strongest benefit - plan.positioning.key_selling_message",
    "name_claim": "product name plus its required claim - product_brief.product_name",
    "badge": "a short offer badge such as GIẢM 25% - product_brief.price_or_promotion",
    "promo": "the promotion in full - product_brief.price_or_promotion",
    "badge_cta": "offer badge plus a call to action - product_brief.price_or_promotion",
}


# ---------------------------------------------------------------------------
# Slot scenes
# ---------------------------------------------------------------------------
# Keyed by SlotSpec.id from platforms.py. Every slot needs an entry, including
# the ones that usually reuse a real photograph, because "usually" fails the
# moment a brand turns up with nothing but a logo.

SLOT_SCENES: dict[str, str] = {
    # --- TikTok Shop --------------------------------------------------
    # Cover frame. A low hero angle so the product towers, its own material
    # caught mid-motion beside it, and the top third held empty - measured: a
    # busy frame with no reserved space swallowed the headline completely.
    "tiktok_cover": (
        "one full-bleed photograph filling the whole frame with no band, border or panel of flat "
        "colour, generous empty space kept in its top third where only clean out-of-focus "
        "background shows and no object stands, so the headline sits directly over the "
        "photograph; below that a low hero angle looking up at the product standing tall, its own "
        "material in motion and physically touching it - a pour, a splash, a drift of steam, a "
        "scatter of its raw ingredient, or, for a product with no material of its own, a sweep of "
        "light and colour - frozen as it arcs through the key light on {surface}, "
        "{light}, one element far behind in deep bokeh, nothing important in the bottom fifth or "
        "along the right edge"
    ),
    # Shop tile. The buyer taps this to inspect the product, so it is the plain
    # truth of the object: no props, no words, nothing to distrust. Beautiful,
    # though - a rim light and one honest contact shadow cost nothing.
    "tiktok_product": (
        "the product alone and filling most of the frame, turned a few degrees off square so one "
        "front face and one side face both read, a specular rim separating its edge from the "
        "background and one soft contact shadow anchoring it to {surface}, {light}, the label "
        "square enough to stay fully legible, no props and no text anywhere"
    ),
    # Offer frame. The discount is the subject; the product is the evidence, so
    # the light is aimed at the card and everything else falls away.
    "tiktok_promo": (
        "the product standing in the lower half of the frame on {surface}, {light}, a hard-edged "
        "beam of the key light landing on one clean flat rectangular card standing just above and "
        "behind it so the card is the brightest thing in the picture, everything else falling off "
        "into shadow, the face of the card left completely empty for the offer text, nothing "
        "important in the bottom fifth or along the right edge"
    ),

    # --- Shopee -------------------------------------------------------
    # The one slot with no look placeholders, and deliberately the one plain
    # picture in the kit. Shopee's white-background rule overrides the art
    # direction, and a marketplace takedown costs more than a consistent kit.
    # Do not add {surface} or {light} here, and do not make this cinematic.
    "shopee_main": (
        "the product centred on a pure white seamless background, square to the camera with "
        "the whole label legible, evenly lit with no strong shadow, a soft contact shadow "
        "under it, nothing else in the frame"
    ),
    # Label close-up. Square to the camera because a shopper is reading it, not
    # admiring it - and focus-stacked, because a soft corner on a label is the
    # difference between reading an ingredient list and guessing at it.
    "shopee_sku": (
        "a tight macro of the product's label and cap filling the frame edge to edge, the label "
        "square to the camera and focus-stacked so every printed character stays sharp corner to "
        "corner, only the nearest edge of {surface} showing below it, {light} raking across the "
        "pack so the emboss and the paper texture read, no props and no text beyond what is "
        "printed on the pack itself"
    ),
    # The range. Not a row of identical items evenly spaced - that is a
    # catalogue page. A tight overlapping row with one unit turned forward
    # reads as a family and gives the frame depth.
    "shopee_collection": (
        "one full-bleed photograph filling the whole frame with no band, border or panel of flat "
        "colour, generous empty space kept in its top third where only clean out-of-focus "
        "background shows, so the headline sits directly over the photograph; below that three of "
        "the product in a tight overlapping row, the nearest turned three-quarters and closest to "
        "the lens, the two behind stepped back and falling out of focus, the product's own "
        "material in motion between them - a pour, a splash, a scatter of its raw ingredient, or, for "
        "a product with no material of its own, a sweep of light and colour - catching the key "
        "light on {surface}, {light}"
    ),
    # Wide banner. The product holds one side and cedes the other to the copy,
    # and the light does the handover: the shadow and the ingredient trail lead
    # the eye from the product into the empty half.
    "shopee_banner": (
        "the product standing in the left third of the frame, turned three-quarters, a long "
        "shadow and a trail of its own raw ingredient running away from it across {surface} into "
        "the right of the picture, {light}, the right half of the same photograph falling into an "
        "even uncluttered gradient with no object in it, left empty for the promotion text"
    ),
}


# ---------------------------------------------------------------------------
# The storyboard
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShotTemplate:
    """One beat of the ad.

    role        hook | product | benefit | cta. Carried through to the finished
                ShotAsset so the seller can see why each shot exists.
    scene_from  which part of the brief supplies this beat's subject. One of:
                  consumer_pain_point   market_signal.consumer_pain_point
                  product_photo         the brand's own product photograph
                  key_selling_points[0] product_brief.key_selling_points[0]
                  promotion             product_brief.price_or_promotion
    text_key    which string is rendered into this shot's keyframe. A key of
                `TEXT_KEYS`. The text is drawn by the image model into the first
                frame and survives the clip intact - the video model must never
                be asked to draw Vietnamese, which it spells wrongly.
    seconds     length of the beat.
    """

    role: str
    scene_from: str
    text_key: str
    seconds: int


# Four beats of five seconds - twenty seconds in total.
#
# Two limits constrain the numbers, and they are tighter than they look:
#   * the video model accepts 4 to 15 seconds per shot;
#   * the QA agent wants the finished master between 15 and 30 seconds, so the
#     four beats have to add up inside that window.
# Twenty sits comfortably in the middle, and leaves room for a 15s cutdown.
#
# The order is the classic short-form ad shape and should not be reshuffled: a
# viewer who has not felt the problem does not care about the product, and one
# who has not seen the product will not act on the offer.

SHOT_TEMPLATES: list[ShotTemplate] = [
    # Name the problem the viewer already has. This must land within the first
    # three seconds or the thumb keeps moving.
    ShotTemplate(role="hook", scene_from="consumer_pain_point", text_key="headline", seconds=5),
    # Show the actual product, clearly and honestly.
    ShotTemplate(role="product", scene_from="product_photo", text_key="name_claim", seconds=5),
    # Give one reason to believe. One - a second reason weakens the first.
    ShotTemplate(role="benefit", scene_from="key_selling_points[0]", text_key="benefit", seconds=5),
    # Ask for the sale, with the offer on screen.
    ShotTemplate(role="cta", scene_from="promotion", text_key="badge_cta", seconds=5),
]
