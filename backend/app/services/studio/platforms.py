"""
Platform kit specifications - what a finished kit contains, marketplace by
marketplace.

A kit is not one set of pictures resized twice. The two audiences are in
different states of mind, so they get different pictures:

  TikTok Shop  the viewer is scrolling and has not decided to buy anything.
               The kit is video-first - a four-beat ad - plus a few staged,
               high-contrast, text-forward stills whose only job is to stop the
               thumb. Almost everything here is built for the campaign.

  Shopee       the shopper already wants the product and is comparing sellers
               before paying. The kit is image-first, calm and informative, and
               prefers the brand's own photographs, because on this screen an
               invented pixel is what causes a return and a bad review.

`KITS` is the table the rest of the studio walks: `direct.py` turns each
`SlotSpec` into a work item and decides where its pixels come from, `render.py`
fills it, `pipeline.py` collects the results into an AssetBundle.

This module is DATA. Adding a slot here adds an image to every campaign the
studio produces, so add deliberately.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.studio import AssetOrigin, ImageKind, Platform


@dataclass(frozen=True)
class SlotSpec:
    """One still image in a kit.

    id            stable name for this slot. `slots.SLOT_SCENES` is keyed by it,
                  `inventory.py` reports which brand photos may fill it, and the
                  finished ImageAsset carries it - so renaming one is a change
                  across four modules.
    kind          the BP-01 image kind, which is what the QA agent counts.
    ratio         the shape as written in a prompt, e.g. "1:1" or "9:16".
    size_key      the name of a field on `studio_settings` holding the pixel
                  size, e.g. "IMAGE_SIZE_SQUARE". Never a literal size: the
                  studio's control panel owns those.
    text_keys     which strings from the brief may appear in this frame, in
                  reading order. See `slots.TEXT_KEYS` for the vocabulary. An
                  empty list means the frame carries no text at all.
    prefer_origin where the pixels should ideally come from. A preference, not
                  a guarantee: if the brand has no suitable photograph the slot
                  falls back to generating one.
    rule          a hard marketplace rule that overrides the art direction.
                  Currently only "pure_white_bg".
    """

    id: str
    kind: ImageKind
    ratio: str
    size_key: str
    text_keys: list[str] = field(default_factory=list)
    prefer_origin: AssetOrigin = AssetOrigin.GENERATE
    rule: str | None = None


@dataclass(frozen=True)
class VideoSlot:
    """One video in a kit.

    shots      how many beats of `slots.SHOT_TEMPLATES` this cut uses. The full
               four-beat storyboard is the master; a shorter cut takes a prefix.
    cutdowns   extra derived cuts to publish alongside the master, by label.
    voiceover  whether to speak the script. Sound-off feeds do not need it.
    """

    id: str
    ratio: str
    shots: int
    cutdowns: list[str] = field(default_factory=list)
    voiceover: bool = False


@dataclass(frozen=True)
class KitSpec:
    """Everything one platform receives.

    `hard_rules` are non-negotiable platform requirements, written as plain
    sentences because they are pasted straight into prompts and shown to the
    seller in the UI. They are not style notes - a style note belongs in a look.
    """

    hard_rules: list[str] = field(default_factory=list)
    slots: list[SlotSpec] = field(default_factory=list)
    video_slots: list[VideoSlot] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The kits
# ---------------------------------------------------------------------------

KITS: dict[Platform, KitSpec] = {
    # -- TikTok Shop: video-first, staged, text-forward ------------------
    Platform.TIKTOK_SHOP: KitSpec(
        hard_rules=[
            "keep text clear of the right 15% and bottom 20% (platform UI overlay)",
            "the hook must land within the first 3 seconds",
            "the frame must read at thumbnail size on a phone",
        ],
        slots=[
            # The cover frame. No stock product photo is a vertical hook frame
            # with a headline on it, so this is always built for the campaign.
            SlotSpec(
                id="tiktok_cover",
                kind=ImageKind.THUMBNAIL,
                ratio="9:16",
                size_key="IMAGE_SIZE_PORTRAIT",
                text_keys=["headline"],
                prefer_origin=AssetOrigin.GENERATE,
            ),
            # The shop tile beside the video. It is the one TikTok frame the
            # buyer studies rather than scrolls past, so a real photograph wins.
            SlotSpec(
                id="tiktok_product",
                kind=ImageKind.HERO,
                ratio="1:1",
                size_key="IMAGE_SIZE_SQUARE",
                text_keys=[],
                prefer_origin=AssetOrigin.REUSE,
            ),
            # The offer frame - the one that carries the discount. Pinned to a
            # comment or used as the end card, so the number must be legible at
            # a glance and correct to the letter.
            SlotSpec(
                id="tiktok_promo",
                kind=ImageKind.BANNER,
                ratio="9:16",
                size_key="IMAGE_SIZE_PORTRAIT",
                text_keys=["badge", "promo"],
                prefer_origin=AssetOrigin.GENERATE,
            ),
        ],
        video_slots=[
            # The full four-beat ad. The 15s cutdown exists because feed
            # placements and ad formats often cap shorter than the master.
            VideoSlot(
                id="tiktok_master",
                ratio="9:16",
                shots=4,
                cutdowns=["15s"],
                voiceover=True,
            ),
        ],
    ),

    # -- Shopee: image-first, informative, real photographs --------------
    Platform.SHOPEE: KitSpec(
        hard_rules=[
            "main image must be a pure white background",
            "minimum 1000x1000",
            "no promotional text burned into the main image",
        ],
        slots=[
            # The listing thumbnail, and the strictest slot in the studio. The
            # marketplace rule beats the art direction here: white seamless, one
            # product, nothing else. Reused from the brand's own catalogue
            # whenever a photograph qualifies.
            SlotSpec(
                id="shopee_main",
                kind=ImageKind.HERO,
                ratio="1:1",
                size_key="IMAGE_SIZE_SQUARE",
                text_keys=[],
                prefer_origin=AssetOrigin.REUSE,
                rule="pure_white_bg",
            ),
            # The close look at the label - ingredients, volume, certification.
            # This is where a shopper checks they are buying the real thing, so
            # a genuine photograph is worth far more than a beautiful render.
            SlotSpec(
                id="shopee_sku",
                kind=ImageKind.SKU_DETAIL,
                ratio="1:1",
                size_key="IMAGE_SIZE_SQUARE",
                text_keys=[],
                prefer_origin=AssetOrigin.REUSE,
            ),
            # The range shot, carrying the campaign message. Remixed from a real
            # photo so the products stay right while the scene becomes the
            # route's own.
            SlotSpec(
                id="shopee_collection",
                kind=ImageKind.COLLECTION,
                ratio="1:1",
                size_key="IMAGE_SIZE_SQUARE",
                text_keys=["headline"],
                prefer_origin=AssetOrigin.REMIX,
            ),
            # The wide promotion banner for the shop front and the campaign
            # section of the listing.
            SlotSpec(
                id="shopee_banner",
                kind=ImageKind.BANNER,
                ratio="2:1",
                size_key="IMAGE_SIZE_LANDSCAPE",
                text_keys=["badge", "promo"],
                prefer_origin=AssetOrigin.REMIX,
            ),
        ],
        video_slots=[
            # A short square cut for the listing gallery. It plays silently
            # beside the photographs, so there is no voiceover and no cutdown -
            # the shopper is reading, not watching.
            VideoSlot(
                id="shopee_square",
                ratio="1:1",
                shots=2,
                cutdowns=[],
                voiceover=False,
            ),
        ],
    ),
}
