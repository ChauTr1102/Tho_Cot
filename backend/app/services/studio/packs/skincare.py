"""
Skincare and beauty.

Beauty is the one category where the lighting *is* the claim. A serum does not
photograph as a thing; it photographs as evidence. The light has to make a
liquid read as clinical, a wet surface read as repaired skin, a frosted bottle
read as expensive - and those are three different rigs, not three adjectives.
So this pack is built out of setups rather than weather: bright-field backlights
and dark edge lines, caustics thrown through a tray of water, a raking key
through a slatted gobo, a rectangle of morning sun on a tiled shelf.

Two rules learned by rendering these against the real COSRX bottle and looking
at the results:

  * **Describe the effect, never the grip.** An early draft of `derm_lab` said
    "black flags close on both sides". Seedream drew two black cards standing in
    the frame. Rewritten as "both edges of the bottle defined by one clean dark
    line" - the thing the flags are *for* - the artifact vanished and the image
    got better. Cards, scrims and bounces belong in this docstring; only what
    the camera sees belongs in a `Look`.

  * **Copy wants a plain, lit field under it.** Across twelve 2:1 banner
    renders, the promotion string came back character-perfect only where the
    right half of the frame was one clean *bright* tone. `glass_skin`, whose
    whole grade is high-key, got "miễn phí vận chuyển" right three times out of
    three; the darker looks failed until `shopee_banner` was rewritten to hand
    the copy a lit field instead of merely an empty one. Negative space is not
    enough - the space has to be *bright*.

Everything here is data. Rewrite the sentences; the studio changes with them.
"""
from __future__ import annotations

from app.services.studio.looks import Look
from app.services.studio.packs import CategoryPack


# ---------------------------------------------------------------------------
# The looks
# ---------------------------------------------------------------------------
# Four registers a beauty client would actually recognise from a treatment:
# the lab, the wet high-key, the bathroom shelf, the spa. Each one is a rig, a
# set and a grade, written so an image model can picture all three.

LOOKS: dict[str, Look] = {
    # Efficacy. The bottle is lit from behind through a graduated scrim so the
    # liquid glows and the glass is carved out by two dark edge lines - the
    # bright-field setup every serum campaign is built on. Cold, dry, exact.
    "derm_lab": Look(
        lens="100mm macro at f/8, focus-stacked, square to the subject",
        light=(
            "a 5600K softbox behind a gradient scrim as a bright-field backlight so the glass "
            "lights from within, both edges of the bottle defined by one clean dark line, a "
            "single hard vertical specular down the shoulder, no fill and no warm light anywhere"
        ),
        surface=(
            "a sheet of white acrylic over brushed stainless with a shallow tray of water across "
            "it and a hard mirror reflection beneath"
        ),
        grade=(
            "neutral clinical grade, true white balance, mid contrast, speculars held just short "
            "of clipping, no grain"
        ),
        palette_hint="white, cold grey, surgical steel, one teal accent",
        axes={"light": "cool_diffuse", "contrast": "mid", "surface": "clinical"},
    ),
    # Glass skin, taken literally. Dermatologists point out the phrase describes
    # skin hydrated enough to *reflect light like polished glass*, so the set is
    # water: a hard key fired through a rippling tray throws caustics across a
    # wet acrylic sweep, and a silver bounce keeps anything from going black.
    # This is also the pack's safest look for on-screen copy.
    "glass_skin": Look(
        lens="85mm macro at f/4, slightly above, tight",
        light=(
            "one hard 6500K key punched through a tray of rippling water so caustic ripples of "
            "light fall across the set, a large silver bounce filling the shadow side back to "
            "near-white, nothing in the frame allowed to go black"
        ),
        surface=(
            "a wet white acrylic sweep with standing water and a scatter of clear droplets beaded "
            "across it"
        ),
        grade=(
            "high-key, crisp micro-contrast, pearlescent highlights, cool white balance with a "
            "faint pink cast"
        ),
        palette_hint="high-key white, water clear, pale pearl pink, one cool aqua",
        axes={"light": "hard_key", "contrast": "high", "surface": "studio"},
    ),
    # Habit rather than efficacy. One hard rectangle of low morning sun on a
    # tiled shelf, everything outside it in warm shade, no bounce card - the
    # subtractive version of a window look, which is what stops it collapsing
    # into the flat daylight of a catalogue.
    "ritual_window": Look(
        lens="50mm at f/2.8, eye level, slight three-quarter",
        light=(
            "low morning sun through a half-open window throwing a soft-edged rectangle of light "
            "across the set, everything outside that rectangle falling into warm shade, no fill"
        ),
        surface=(
            "a wet ceramic-tile bathroom shelf with a folded waffle towel, a toothglass and a "
            "fogged mirror behind"
        ),
        grade=(
            "warm 4300K grade, mid contrast, creamy highlights, gentle halation where the sun "
            "clips the glass"
        ),
        palette_hint="cream, terracotta, warm white tile, one sage accent",
        axes={"light": "warm_window", "contrast": "mid", "surface": "domestic"},
    ),
    # The treatment room. A hard key rakes in from back-left through a slatted
    # gobo - the pattern sits near the lamp, which is what keeps the shadow edge
    # crisp - and the shadow side is left unfilled so wet basalt and raw linen
    # are sculpted by subtraction. Sensorial, expensive, quiet.
    #
    # The palette is deliberately un-green. An earlier draft ended "one deep
    # green accent" and Seedream coloured the Vietnamese headline green with it.
    # A palette hint tints the type as readily as the props.
    "spa_noir": Look(
        lens="85mm at f/2.0, low three-quarter hero angle",
        light=(
            "a single hard tungsten key raking from back-left through a slatted gobo so bands of "
            "light cross the set, the shadow side left unfilled, a low warm rim separating the "
            "glass from the dark"
        ),
        surface=(
            "wet black basalt with a folded raw-linen cloth and low steam drifting across the stone"
        ),
        grade=(
            "deep warm-against-cool grade, crushed shadows, warm specular highlights, fine film grain"
        ),
        palette_hint="near-black, wet slate grey, warm amber highlight, bone white",
        axes={"light": "single_hard", "contrast": "high", "surface": "natural"},
    ),
}


# ---------------------------------------------------------------------------
# Scene grammar
# ---------------------------------------------------------------------------
# Overrides for the slots where skincare wants a different frame from the
# generic library. Only `{surface}` and `{light}` may appear.
#
# The rule the generic scenes miss: a beauty scene should describe an *event*.
# A bottle standing beside props is a catalogue page; a bottle with a bead of
# essence running down its shoulder and a ribbon still drawn from the nozzle is
# an advertisement. Every scene below has something mid-motion in it.
#
# `shopee_main` is deliberately absent. It is a marketplace listing image on a
# pure white background and its rule outranks art direction - making it
# cinematic is how a listing gets taken down. `tiktok_product` is absent for the
# same family of reason: it is the plain truth of the object, and props there
# read as something to distrust.

SCENE_GRAMMAR: dict[str, str] = {
    # 9:16 cover. The event is a pump mid-dispense. The top third is described
    # as an unbroken fall-off rather than merely "empty", because an elaborate
    # scene will happily grow into empty space and swallow the headline.
    "tiktok_cover": (
        "the bottle standing low in the frame on {surface}, {light}, a single bead of essence "
        "running down the glass shoulder and a thin ribbon of essence still drawn between the "
        "pump nozzle and the surface below it, the top third of the frame kept clean and empty "
        "as an unbroken fall-off of background with nothing crossing it, and nothing important "
        "in the bottom fifth or along the right edge"
    ),
    # 9:16 offer frame. The offer card is lit as a practical - a bright plate in
    # the set - rather than pasted on, which is both better photography and the
    # measured way to keep a Vietnamese promo string intact.
    "tiktok_promo": (
        "the bottle on {surface} beside a clean rectangular offer card lit as a bright even plate "
        "in the set, {light}, a fresh pump of essence pooling and spreading slowly on the surface "
        "between the two, the offer card the brightest unbroken thing in the frame and sitting "
        "above the centre line"
    ),
    # 1:1 label read. Close, but NOT an extreme macro: a tight crop on the label
    # alone made Seedream re-lay-out the packaging - COSRX migrated to the top of
    # the gold panel and the black band went missing. Framed from the collar down
    # past the base, the real label survives intact and still reads.
    "shopee_sku": (
        "a close square-to-camera shot of the bottle from the pump collar down past the base on "
        "{surface}, {light}, every printed character sharp and in its original position on the "
        "label, fine water droplets beaded across the glass around the label but not one droplet "
        "or highlight crossing the lettering, a shallow specular running down the shoulder "
        "beside it"
    ),
    # 1:1 range. The routine in order of use, standing in a shallow tray of
    # water, with the water still moving - a family shot that is also an event.
    "shopee_collection": (
        "the full range standing in a shallow tray of water on {surface}, {light}, evenly spaced "
        "and all turned to the same three-quarter angle in order of use, every label facing the "
        "camera, ripples still spreading out from the nearest bottle and one clean mirror "
        "reflection running under the whole row"
    ),
    # 2:1 banner. The right half is handed to the copy as a *lit* field, not an
    # empty one - see the module docstring; this is the single change that moved
    # promo-string accuracy on the dark looks.
    "shopee_banner": (
        "the bottle standing to the left on {surface}, {light}, a long specular down its shoulder "
        "and a shaped shadow raking away to the right, a slick of essence catching light in the "
        "lower left corner, and the right half of the frame given over to one clean, even, "
        "brightly lit unbroken field with no prop, no shadow edge and no texture crossing it, "
        "kept plain for the promotion text"
    ),
}


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------
# A storyboard role to a camera move. Beauty motion is slow and close: the
# category's whole argument is texture, and texture only reads when the camera
# gives it time.

MOTION: dict[str, str] = {
    "hook": (
        "a slow macro dolly in across the wet surface until the specular on the bottle's shoulder "
        "resolves into focus, shallow rack focus"
    ),
    "product": (
        "a quarter orbit around the bottle, the specular travelling along the glass shoulder as it "
        "turns"
    ),
    "benefit": (
        "an extreme macro push into a single droplet of essence spreading on the surface, focus "
        "racking from the droplet's edge to its centre"
    ),
    "cta": (
        "a slow pull-out from the bottle to reveal the offer card, the key light lifting as the "
        "frame widens"
    ),
}

# The variant used when Seedream has drawn copy into the first frame. Measured:
# a push-in carried "PHỤC HỒI HÀNG RÀO DA" straight out of a 9:16 frame. So none
# of these reframe. Beauty is lucky here - light, reflection, droplet, liquid and
# surface detail are exactly what the category wants moving anyway, so the
# locked variant is not a compromise.
MOTION_LOCKED: dict[str, str] = {
    "hook": (
        "the camera holds its framing exactly; a bead of condensation slides down the glass and "
        "the shaped shadow across the surface drifts a few degrees"
    ),
    "product": (
        "the camera holds its framing exactly; only the specular travels down the bottle's "
        "shoulder and the liquid inside settles"
    ),
    "benefit": (
        "the camera holds its framing exactly; a droplet of essence spreads and finds its edge on "
        "the surface, catching the light as it goes"
    ),
    "cta": (
        "the camera holds its framing exactly; the light on the offer card lifts and the "
        "reflection beneath the bottle brightens, nothing moving out of place"
    ),
}


CRAFT_NOTES = (
    "Skincare sells a result nobody can photograph, so the lighting has to stand in for it: a "
    "bright-field backlight makes a liquid look pure because you can see straight through it, a "
    "hard key through a tray of water writes caustics that read as hydration, a raking gobo on wet "
    "stone reads as a treatment room you would pay to sit in. That is why every look here is a rig "
    "rather than a mood - and why the rig is described by what it produces, not by the cards that "
    "produce it, since an image model given a black flag will draw a black flag. The pack's two "
    "poles are the A/B the category actually argues about: does this brand sell efficacy or does it "
    "sell ritual? `derm_lab` is the evidence case, cold and dry and dimensionally exact; `spa_noir` "
    "is the sensorial one, dark and warm and unfilled. They disagree on all three axes, which is the "
    "point - a test between two pretty pictures that look alike measures nothing. `glass_skin` and "
    "`ritual_window` sit either side as the K-beauty and the bathroom-shelf reads. Beyond the light, "
    "one discipline matters more than any other: props must be doing something. A bottle beside a "
    "folded towel is a catalogue page; a bottle with essence still drawn from its nozzle is an "
    "advertisement, and it costs nothing extra to render. The one place to hold back is the frame "
    "around the copy. A Vietnamese headline with stacked diacritics needs a plain, evenly lit field "
    "under it, and the more beautiful the set the more willing it is to grow into that field and "
    "take the words with it."
)


SOURCES: list[str] = [
    # Bright-field / dark-field, flagging, gradient through glass, specular control
    "https://www.usepixora.com/resource/beauty-product-photography-guide",
    "https://www.diyphotography.net/crossing-over-to-the-dark-field-has-never-been-easier/",
    "https://advancedillumination.com/lighting-education/bright-field-dark-field-lighting/",
    "https://westcottu.com/dark-field-imaging-tips-techniques",
    "https://www.prophotostudio.net/blog/learning-center/why-photographing-glass-is-so-hard/",
    "https://www.photographyfirm.co.uk/photographing-glassware-how-to-shoot-bottles/",
    "https://www.outshinery.com/articles/how-to-photograph-glass-bottle-without-reflections",
    "https://www.digitalphotomentor.com/tips-for-photographing-glassware-on-both-black-and-white-backgrounds/",
    "https://www.instructables.com/Photographing-Glassware/",
    # Droplets, glycerin beading, focus stacking, macro working distances
    "https://www.domestika.org/en/blog/4383-photography-tutorial-how-to-create-droplets-with-glycerin",
    "https://www.apogeephoto.com/creating-glycerin-drop-reflection-photos-with-focus-stacking/",
    "https://digital-photography-school.com/macro-dewdrop-photography/",
    "https://www.canon-europe.com/get-inspired/tips-and-techniques/water-droplet-macro/",
    # Liquid caught mid-motion: splash typology and freeze-flash practice
    "https://www.howlettphoto.com/blog/drinks-liquids-photographer",
    "https://phoode.com/blog/culinary-splash-effect-energizes-food-photography/",
    "https://www.paulreiffer.com/2019/01/splash-water-drop-photography-with-high-speed-freeze-flash/",
    # Gobo vs cucoloris, shadow-edge hardness, negative fill / subtractive lighting
    "https://www.videomaker.com/article/8250-casting-shadows-with-cookies-a-recipe-for-success/",
    "https://petapixel.com/2016/08/29/making-gobos-unusual-things-creative-portrait-lighting/",
    "https://www.goboplus.com/dappled-shade-gobo.html",
    "https://en.wikipedia.org/wiki/Fill_light",
    "https://www.conceptsnc.com/en/service/still-life-product/",
    # Art-direction registers: glass skin as literal reflectivity; the clinical claim
    "https://montecristomagazine.com/beauty/glass-skin-the-k-beauty-skin-care-trend-making-waves-worldwide",
    "https://www.janeyoomd.com/glass-skin-the-rise-and-reality-behind-the-k-beauty-trend/",
    "https://sbeautyplus.com/blogs/beauty-news/what-clinical-really-means-in-modern-skincare-marketing",
    "https://zeely.ai/blog/22-skincare-ads-that-actually-work-with-proof-you-can-copy",
    # Vendor prompt formula and camera / aesthetic vocabulary tables
    "https://docs.byteplus.com/en/docs/ModelArk/2222480",
    "https://docs.byteplus.com/en/docs/ModelArk/1520757",
]


PACK = CategoryPack(
    key="skincare",
    label="Skincare & beauty",
    # What an upstream crawler actually emits, in both languages. Keywords are
    # long on purpose: bare "kem" would take an ice cream and bare "da" would
    # take half the Vietnamese dictionary.
    matches=[
        # English
        "skincare", "skin care", "cosmetic", "beauty", "serum", "essence",
        "ampoule", "toner", "moisturiser", "moisturizer", "cleanser",
        "sunscreen", "body scrub", "face mask", "sheet mask", "snail mucin",
        "hyaluronic", "niacinamide", "retinol", "glass skin",
        # Vietnamese
        "chăm sóc da", "dưỡng da", "mỹ phẩm", "tinh chất", "kem dưỡng",
        "dưỡng ẩm", "sữa rửa mặt", "rửa mặt", "tẩy trang", "tẩy da chết",
        "chống nắng", "mặt nạ", "ốc sên", "làm sạch da", "trắng da",
    ],
    looks=LOOKS,
    # Efficacy versus ritual - the argument the category is actually having, and
    # three axes apart, which is as far as this library goes.
    default_pair=("derm_lab", "spa_noir"),
    scene_grammar=SCENE_GRAMMAR,
    motion=MOTION,
    motion_locked=MOTION_LOCKED,
    craft_notes=CRAFT_NOTES,
    sources=SOURCES,
)
