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

This module is DATA. Every string here is written to be rewritten. Two rules to
keep in mind while rewriting:

  * The only placeholders allowed in a scene are `{surface}` and `{light}`.
    Any other brace will raise when the prompt is assembled.
  * Nouns beat adjectives. "a wooden board with fresh ingredients" renders;
    "a lovely natural feel" does not.
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
    # Cover frame. The product sits low so the headline has the top third to
    # itself, and the platform's own buttons live in the corners we keep empty.
    "tiktok_cover": (
        "the product held towards the camera on {surface}, {light}, the product low "
        "in the frame with the top third left empty for the headline, and nothing "
        "important in the bottom fifth or along the right edge"
    ),
    # Shop tile. The buyer taps this to inspect the product, so it is the plain
    # truth of the object: no props, no words, nothing to distrust.
    "tiktok_product": (
        "the product standing alone and filling most of the frame on {surface}, "
        "{light}, straight on, no props and no text"
    ),
    # Offer frame. The discount is the subject; the product is the evidence.
    "tiktok_promo": (
        "the product on {surface} beside a clean rectangular offer card, {light}, the "
        "offer card brighter than everything around it and sitting above the centre line"
    ),

    # --- Shopee -------------------------------------------------------
    # The one slot with no look placeholders. Shopee's white-background rule
    # overrides the art direction, and a marketplace takedown costs more than a
    # consistent kit. Do not add {surface} or {light} here.
    "shopee_main": (
        "the product centred on a pure white seamless background, soft contact shadow "
        "under it, nothing else in the frame"
    ),
    # Label close-up. Square to the camera because a shopper is reading it, not
    # admiring it.
    "shopee_sku": (
        "a close macro of the product's label and cap on {surface}, {light}, square to "
        "the camera with the whole label legible"
    ),
    # The range. Even spacing and matching angles, so it reads as one family.
    "shopee_collection": (
        "the full product range lined up in a row on {surface}, {light}, even spacing "
        "between items, every label facing the camera"
    ),
    # Wide banner. The product holds one side and cedes the other to the copy.
    "shopee_banner": (
        "the product standing to the left on {surface}, {light}, the right half of the "
        "frame left open for the promotion text"
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
