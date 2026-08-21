"""
Confectionery and premium food — chocolate, bean-to-bar, bánh kẹo, dessert.

Chocolate is the hardest thing in this library to photograph and the easiest to
photograph badly, because it breaks the assumption every other category rests
on. A serum bottle is lit by the light that *falls on it*. A tempered chocolate
bar is a dark, glossy, near-mirrored surface: it is lit almost entirely by what
it *reflects*. Point a big soft box at it and it returns a grey smear and a
muddy brown midtone — the supermarket-flyer failure. Every technique in this
pack follows from that one fact:

* **Light the reflection, not the object.** A tall white card stood just out of
  frame, edge-on to the bar, is what draws the single clean specular down the
  tempered face that says "this chocolate is in temper". The key light's job is
  to light *that card*.
* **Negative fill is not optional.** Black flags on the opposite side keep the
  shadow flank genuinely black. Without them the room fills the shadow with more
  brown and the picture goes brown-on-brown, which is the muddiest thing a
  camera can do.
* **The two faces of a bar want opposite light.** The moulded top is glossy and
  reads as *reflection*; the fracture edge of a snapped bar is matte,
  crystalline and granular and reads as *texture*. Gloss wants a large source at
  a glancing angle; the break wants a hard narrow one raking across it at nearly
  ninety degrees. A frame that shows both has to serve both.
* **Separate dark from dark.** The category's home is a near-black set, so a
  warm rim or kicker from behind is the only thing standing between a 70% bar
  and the background it is sitting on.
* **Cocoa dust is a backlight problem.** Sifted powder falling through a bare
  back light against a dark set lights up; the same powder in front light
  disappears. This is the vendor's own `Tyndall Effect` in its edible form.

The second thing that separates paid work from stock here: a chocolate scene
describes an **event**, not an arrangement. Props scattered around a bar is a
flyer. A bar snapping with crumbs still in the air, powder falling through the
key, a wrapper torn open with the foil lifting, a ribbon of couverture folding
off a palette knife — those are photographs. Every scene in `scene_grammar` is
written as something happening.

Two registers are worth building for this category and they photograph nothing
alike, which is exactly why they make the pack's A/B pair:

  origin   the terroir story — cacao pods, drying beds, fermentation crates,
           hard tropical sun through slats. Sells the craft and the province.
  gift     the bar as an object you hand to someone — near-black set, one hard
           light, gold, ribbon, a mirror plinth. Sells the occasion.

`snap_macro` is the appetite register: no packaging, just the break. It is the
workhorse for benefit beats and SKU detail. `chocolatier_bench` is the maker's
atelier, the warm daylight counterweight to three dark looks.
"""
from __future__ import annotations

from app.services.studio.looks import Look
from app.services.studio.packs import CategoryPack

# ---------------------------------------------------------------------------
# The looks
# ---------------------------------------------------------------------------
# Each `light` is a lighting *setup* an assistant could rig — sources, angles,
# flags — never a weather report. Each `surface` is a *set* with things in it,
# because the scene templates below say "on {surface}" and the model renders the
# nouns it is given.

LOOKS: dict[str, Look] = {
    # ---- the gift register -------------------------------------------------
    # Near-black, one hard source, gold. This is the look the whole premium
    # confectionery category is built on, and the one thing that ruins it is
    # fill: the moment a second soft source opens the shadow, the bar stops
    # looking expensive and starts looking like a vending machine.
    "gift_noir": Look(
        lens="100mm macro at f/8, focus-stacked, camera a few degrees above the bar's own height",
        light=(
            "a single hard fresnel key from back-left at forty-five degrees skimming the top "
            "edge, a tall white card standing edge-on just out of frame camera-left so its "
            "reflection draws one clean unbroken specular down the tempered face, black flags "
            "on the right and beneath the lens for negative fill so the shadow flank stays "
            "genuinely black, and a narrow warm kicker from behind separating dark chocolate "
            "from the dark set"
        ),
        surface=(
            "a low black-acrylic plinth on a near-black seamless sweep with a mirror "
            "reflection under everything standing on it, a drift of cacao nibs at the base "
            "and a length of grosgrain ribbon running out of frame"
        ),
        grade=(
            "deep contrast with the blacks held just off zero and detail still alive in them, "
            "warm mahogany midtones against one cool blue-grey shadow, gold speculars kept a "
            "stop under clipping, no lifted haze"
        ),
        palette_hint="near-black, warm mahogany, one gold specular, a single cream accent",
        axes={"light": "single_hard", "contrast": "high", "surface": "studio"},
    ),

    # ---- the origin register -----------------------------------------------
    # The province, not the product. Hard equatorial sun broken by slats is the
    # signature of every serious bean-to-bar origin shoot, and the striped
    # shadow it throws is what stops a plantation frame reading as a stock photo
    # of some beans.
    "cacao_origin": Look(
        lens="50mm at f/2.8, chest height, the near foreground dropping out of focus",
        light=(
            "hard equatorial midday sun coming through the bamboo slats of a drying shed so a "
            "striped shadow falls right across the set, a large silver bounce from camera-right "
            "lifting the undersides just enough to keep them readable, and a flag cutting the "
            "sky behind so the background sits a stop and a half down"
        ),
        surface=(
            "a rough-sawn fermentation crate standing on a drying yard of raked cacao beans, "
            "jute sacking, a split cacao pod with the wet white pulp still showing, and a sheet "
            "of hand-torn kraft paper"
        ),
        grade=(
            "warm high-contrast daylight, sunlit ochre against a deep green-black shade, "
            "saturated without going sweet, fine grain, highlights allowed to run hot on the "
            "beans"
        ),
        palette_hint="sun-bleached ochre, jute, wet-pulp cream, one deep foliage green",
        axes={"light": "mixed_daylight", "contrast": "high", "surface": "natural"},
    ),

    # ---- the appetite register ---------------------------------------------
    # No packaging at all. A snapped bar's fracture face is matte, crystalline
    # and granular — a completely different material from the glossy top — and a
    # narrow source raking it at nearly ninety degrees is the only way that
    # texture reads. The dust needs the opposite treatment: a bare light behind
    # it, against black.
    "snap_macro": Look(
        lens="100mm macro at f/11, one-to-one magnification, focus-stacked across the break",
        light=(
            "a single narrow strip softbox raking the fracture from camera-left at almost "
            "ninety degrees so the crystalline break reads as texture rather than as a shadow, "
            "black card pressed in hard on the right for negative fill, and a bare back light "
            "behind the falling cocoa so the powder lights up against the dark set"
        ),
        surface=(
            "a honed black slate slab dusted with sifted cocoa, on a near-black background with "
            "no visible horizon, cacao nibs and two broken shards lying where they fell"
        ),
        grade=(
            "near-black with one bright band across the break, warm cocoa midtones against a "
            "cool shadow, texture held all the way down into the shadows, nothing crushed"
        ),
        palette_hint="near-black, cocoa brown, one rim of warm amber",
        axes={"light": "hard_key", "contrast": "high", "surface": "studio"},
    ),

    # ---- the maker register ------------------------------------------------
    # The atelier: marble, a palette knife, paper. The one daylight look in the
    # pack, and the reason the pack does not read as four versions of the same
    # dark room. Low raking window light does the work a hard key does in the
    # other three — it is still a rake, just a softer one.
    "chocolatier_bench": Look(
        lens="50mm at f/4, slightly above, the far end of the bench falling soft",
        light=(
            "low late-afternoon window light raking straight across the bench from camera-left "
            "through a half-drawn linen blind, one white bounce opened on the right only far "
            "enough to keep the shadows readable, and a flag over the lens holding the marble's "
            "sheen out of the top of frame"
        ),
        surface=(
            "a cocoa-dusted marble tempering slab on a worn wooden bench, an offset palette "
            "knife lying in a smear of tempered couverture, a stack of hand-printed wrapper "
            "paper and a dish of cacao nibs"
        ),
        grade=(
            "warm mid contrast, creamy highlights on the marble, cocoa brown against paper "
            "cream, gentle falloff into the room behind"
        ),
        palette_hint="paper cream, kraft, cocoa brown, warm marble grey",
        axes={"light": "warm_window", "contrast": "mid", "surface": "domestic"},
    ),
}


# ---------------------------------------------------------------------------
# Scene grammar
# ---------------------------------------------------------------------------
# Overrides for the slots where confectionery wants a different frame from the
# generic library. Only `{surface}` and `{light}` may appear.
#
# `shopee_main` is deliberately absent: it is a marketplace listing image on
# pure white and that rule outranks any art direction. `tiktok_product` is
# absent too — the shop tile is the plain truth of the object and props would
# only make a buyer distrust it.
#
# The rule every one of these follows: something is *happening*. A bar snapping,
# powder falling, paper being torn, couverture folding. An arrangement of props
# around a product is the exact thing that made the old presets read as stock.

SCENE_GRAMMAR: dict[str, str] = {
    # Vertical hook frame. The snap is the event; the top third stays dark and
    # empty so the headline has somewhere to live, which is also the frame's
    # known failure mode — an elaborate scene will swallow the copy if the
    # negative space is not written into the sentence.
    "tiktok_cover": (
        "the product standing low in the frame on {surface}, {light}, a second piece of it "
        "snapped clean in two just behind and a little out of focus with both fracture faces "
        "turned into the light and crumbs still falling from the break, the top third of the "
        "frame left dark and empty for the headline, nothing important in the bottom fifth or "
        "along the right edge"
    ),

    # The offer frame. Read as the moment after a gift is opened rather than as
    # a price card sitting next to a product.
    "tiktok_promo": (
        "the product lying on {surface} beside a clean rectangular offer card, {light}, a torn "
        "strip of its own wrapper and a length of ribbon trailing out of frame as if the gift "
        "has just been opened, the offer card brighter than everything around it and sitting "
        "above the centre line"
    ),

    # Label close-up. A shopper is reading this, so the packaging stays square
    # to camera and fully legible — but the light rakes the paper so printed ink
    # and paper grain sit proud, which is what makes hand-printed packaging look
    # hand-printed instead of like a flat scan.
    "shopee_sku": (
        "a close macro of the product's own printed wrapper filling the frame on {surface}, "
        "{light} raking across the paper at a shallow angle so the printed ink and the paper "
        "grain sit proud of the surface, the wrapper squared to the camera with every printed "
        "character legible and sharp, one corner lifted just far enough to show the foil beneath"
    ),

    # The range. Still a legible row, but caught mid-gesture: the nearest one is
    # being opened, so the family reads as a family and as something in use.
    "shopee_collection": (
        "the full product range standing in a shallow arc on {surface}, {light}, each wrapper "
        "turned a few degrees further than the last so the row reads as a fan, the nearest one "
        "half-opened with the bar sliding out of its paper and one square already broken off "
        "and leaning against it, even spacing, every printed panel facing the camera"
    ),

    # Wide banner. The product holds the left, a fall of cocoa through the key
    # gives the right half something to be made of, and the copy still lands on
    # a clean dark field.
    "shopee_banner": (
        "the product standing to the left on {surface}, {light}, sifted cocoa powder falling "
        "through the key light behind it and settling into a fine drift at its base, the right "
        "half of the frame left dark and open for the promotion text"
    ),
}


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------
# One camera move per storyboard beat. These are pasted into the video prompt's
# ACTION + CAMERA line, so they are written as instructions to a camera
# operator, in the vendor's own vocabulary (`Push-in`, `Pull-out`, `Orbit
# Shot`, `Slow Motion`, `Close-up`).

MOTION: dict[str, str] = {
    # The snap is the hook. Nothing else in this category stops a thumb faster.
    "hook": (
        "a fast macro push-in that lands exactly as the bar snaps, the two halves parting and "
        "crumbs falling through the key light in slow motion"
    ),
    # A few degrees of orbit walks the specular along the tempered face, which
    # is the only way a still camera can show that a surface is glossy.
    "product": (
        "a slow orbit shot of a few degrees around the bar so the raking key travels along the "
        "tempered face and lifts the moulded pattern out of it"
    ),
    # The reason to believe is the texture of the break.
    "benefit": (
        "a slow tilt down the fracture face in extreme close-up, the plane of focus travelling "
        "across the crystalline break"
    ),
    # Pull out to the whole gift, because the offer is the box, not the bar.
    "cta": (
        "a slow pull-out from the opened wrapper to the whole gift box, the ribbon settling as "
        "the frame widens"
    ),
}

# The variant used when the frame already carries on-screen text. Measured: a
# push-in over a 9:16 keyframe carried its headline straight out of frame. So
# none of these may reframe — every one of them moves the *material* and leaves
# the camera exactly where it was. Confectionery is unusually well served by
# this constraint: falling powder, a travelling specular and a shifting
# reflection are all things this category wants anyway.
MOTION_LOCKED: dict[str, str] = {
    "hook": (
        "the camera holds its framing exactly, no zoom and no reframing; cocoa powder falls "
        "through the key light and settles, and the crumbs at the break drift down out of frame"
    ),
    "product": (
        "the camera holds its framing exactly, no zoom and no reframing; only the specular "
        "highlight travels along the tempered face as if the key were being walked slowly "
        "across it"
    ),
    "benefit": (
        "the camera holds its framing exactly, no zoom and no reframing; a fine cocoa dust "
        "drifts across the frame in the back light and the reflection under the bar shifts with "
        "it"
    ),
    "cta": (
        "the camera holds its framing exactly, no zoom and no reframing; the ribbon's sheen "
        "turns and the gold on the wrapper catches the light and releases it"
    ),
}


CRAFT_NOTES = """\
Chocolate is a dark specular surface, so it is lit by what it reflects rather \
than by what falls on it: every look here places a source to be *seen in* the \
bar and then flags the opposite side hard, because the fastest way to make \
chocolate look cheap is to let a second soft source fill the shadow with more \
brown. Brown against brown is the category's characteristic mud, which is why \
every grade pins the warm midtone against one cool shadow and keeps the whole \
palette to three notes. The moulded top and the fracture edge are different \
materials — one glossy, one matte and crystalline — and want opposite \
treatment, so `gift_noir` builds a single clean specular with a white card \
while `snap_macro` rakes a narrow strip across the break at almost ninety \
degrees; cocoa dust wants a third answer again, a bare back light against \
black. Focal lengths are long and apertures small because a bar is flat and a \
premium frame cannot have half its moulded pattern soft, hence 100mm and focus \
stacking; `cacao_origin` and `chocolatier_bench` are the two looks with depth \
in the set, so they open up and shorten. The two registers exist because they \
sell different things — origin sells the province and the craft, gift sells the \
occasion — and they disagree on light and on set, which is what makes the A/B \
pair worth running. Finally, every scene is written as an event: a bar \
snapping, powder falling, paper being torn open. Props merely present around a \
product is precisely the arrangement that reads as a supermarket flyer."""


SOURCES: list[str] = []


PACK = CategoryPack(
    key="confectionery",
    label="Confectionery & premium food",
    matches=[
        # Vietnamese first — this is what the upstream crawler actually emits.
        "socola", "sô cô la", "sô-cô-la", "ca cao", "cacao", "bánh kẹo", "kẹo",
        "bánh ngọt", "quà bánh",
        # English / French. "chocolat" subsumes "chocolate" and catches the
        # French wording that turns up on real bean-to-bar packaging.
        "chocolat", "chocolate", "cocoa", "bean-to-bar", "bean to bar",
        "confection", "confectionery", "dessert", "praline", "truffle",
        "patisserie", "pâtisserie", "candy", "sweets",
    ],
    looks=LOOKS,
    # Two axes apart (light and surface), and two genuinely different
    # commercial arguments: the object you give versus the place it came from.
    default_pair=("gift_noir", "cacao_origin"),
    scene_grammar=SCENE_GRAMMAR,
    motion=MOTION,
    motion_locked=MOTION_LOCKED,
    craft_notes=CRAFT_NOTES,
    sources=SOURCES,
)
