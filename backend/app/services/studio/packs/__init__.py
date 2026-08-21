"""
Category art-direction packs.

Commercial photography is not one craft. A skincare campaign is lit to make a
liquid look clinical and a surface look repaired; a chocolate campaign is lit to
make a fracture edge read as texture; a power bank is lit to make anodised metal
read as precise. The lighting setups, the props, the motion, even the aspect
conventions differ per category, and a single library of generic presets
flattens all of that into supermarket-flyer neutrality.

So each category gets its own pack: its own looks, its own scene grammar, its own
motion vocabulary, and its own note on what actually makes that category read as
paid work. Packs are data. An art director opens one file, reads sentences, and
tunes them — no code, no framework.

Adding a category is adding a file: define `PACK` and import it in `_MODULES`.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field

from app.services.studio.looks import Look

# Category packs, in match priority order. A brand's category string is matched
# against each pack's `matches` list; the first hit wins, so put specific
# categories before broad ones.
_MODULES = (
    "skincare",
    "beverage",
    "coffee",
    "confectionery",
    "electronics",
)


@dataclass(frozen=True)
class CategoryPack:
    """One category's art direction, as data.

    `looks` are the pack's own presets and take priority over the generic
    library. `scene_grammar` overrides a slot's scene template when this pack is
    active — a skincare SKU close-up wants a different frame from a chocolate
    one. `motion` maps a storyboard role to a camera move, because a hook beat
    and a CTA beat do not want the same gesture.
    """

    key: str
    label: str
    matches: list[str]
    looks: dict[str, Look]
    default_pair: tuple[str, str]
    scene_grammar: dict[str, str] = field(default_factory=dict)
    motion: dict[str, str] = field(default_factory=dict)
    motion_locked: dict[str, str] = field(default_factory=dict)
    craft_notes: str = ""
    sources: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for key in self.default_pair:
            if key not in self.looks:
                raise ValueError(f"{self.key}: default_pair names unknown look {key!r}")


def _load() -> list[CategoryPack]:
    packs: list[CategoryPack] = []
    for name in _MODULES:
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except ModuleNotFoundError:
            continue          # a pack still being written must not break a run
        pack = getattr(module, "PACK", None)
        if isinstance(pack, CategoryPack):
            packs.append(pack)
    return packs


PACKS: list[CategoryPack] = _load()
BY_KEY: dict[str, CategoryPack] = {p.key: p for p in PACKS}


def resolve(category: str, tone: str = "", trend: str = "") -> CategoryPack | None:
    """Pick the pack for a brand, or None to fall back to the generic library.

    Matching is plain case-folded substring against the category first, then the
    tone and trend, so an upstream crawler that returns "Tẩy da chết cơ thể"
    rather than a tidy taxonomy label still lands somewhere sensible.
    """
    haystacks = [category or "", tone or "", trend or ""]
    for haystack in haystacks:
        folded = haystack.casefold()
        for pack in PACKS:
            if any(m.casefold() in folded for m in pack.matches):
                return pack
    return None


def looks_for(category: str, tone: str = "", trend: str = "") -> dict[str, Look]:
    """Every look available to a brand: its pack's presets, else the generic set."""
    from app.services.studio.looks import LOOKS

    pack = resolve(category, tone, trend)
    return {**LOOKS, **pack.looks} if pack else dict(LOOKS)
