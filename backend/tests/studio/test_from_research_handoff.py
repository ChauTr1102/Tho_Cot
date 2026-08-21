"""
The handoff from research into the studio, asserted against the real campaign
row rather than a fixture.

The studio is downstream of a teammate's agent, so the interesting failures are
not crashes — they are things that arrive and are quietly dropped. `load_pair`
used to call `upstream.load_plan`, the thin adapter, which returns the contract
and discards everything the parse worked out on the way: which marketplaces each
route asked for, whether upstream forbade redrawing the packaging, which kho
photos it named, and what it had to repair. All of it was computed and thrown
away, and the run looked completely healthy without it.

These tests skip when `sql_app.db` is absent, because the database belongs to
the research stage and a checkout without one is a legitimate state.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.studio import from_research

DB = Path("sql_app.db")
pytestmark = pytest.mark.skipif(
    not DB.is_file(), reason="sql_app.db thuộc bước research, chưa có ở checkout này"
)


@pytest.fixture(scope="module")
def researched_id() -> str:
    rows = [r for r in from_research.list_campaigns() if r.get("status") == "researched"]
    if not rows:
        pytest.skip("chưa có campaign nào research xong")
    return rows[0]["id"]


@pytest.fixture(scope="module")
def handoff(researched_id):
    return from_research.load_pair(researched_id)


def test_the_brief_survives_the_crossing(handoff):
    _, campaign_input, _ = handoff
    brief = campaign_input.product_brief
    assert brief.product_name, "sản phẩm không có tên thì không chụp được gì"
    assert brief.category
    # `{amount, currency, unit}` plus a separate promotion, as one line. A brief
    # with neither is legitimate — not every product ships with a price on the
    # artwork — so the assertion is about the formatting, not the presence: an
    # unformatted amount reaches a badge as "135000.0".
    if brief.price_or_promotion:
        assert "135000.0" not in brief.price_or_promotion
        assert ".0" not in brief.price_or_promotion.split(" ")[0]


def test_photos_resolve_to_the_right_brand(handoff, researched_id):
    """Six demo brands store their photos under the same filenames, so an
    alphabetical sweep once resolved a G7 coffee campaign onto COSRX's serum
    bottle and rendered the whole kit as a serum wearing a coffee label.

    Two resolutions are legitimate and only one of them can be checked by name.
    A campaign whose uploads were kept has them under its own
    `data/<campaign_id>/source/`, which is correct by construction — nobody
    else's photographs can be in there. Only the `sample_data/` fallback has to
    prove itself, because that is the sweep that once picked the wrong brand.
    """
    _, campaign_input, notes = handoff
    product = campaign_input.product_brief.product_name.casefold()
    words = {w for w in product.replace("_", " ").split() if len(w) > 1}

    for raw in campaign_input.brand_kit.product_photo_urls:
        path = Path(raw)
        if researched_id in path.parts:
            continue  # the campaign's own upload directory
        folder = path.parent.parent.name.casefold()
        shared = {w for w in folder.replace("_", " ").split() if len(w) > 1} & words
        assert shared, f"{raw} không khớp tên sản phẩm {product!r}"
    assert notes["photos_missing"] == []


def test_the_plan_keeps_both_creative_routes(handoff):
    plan, _, _ = handoff
    assert len(plan.creative_routes) >= 2, "A/B cần ít nhất hai route"
    ids = [r.route_id for r in plan.creative_routes]
    assert len(set(ids)) == len(ids), "route_id trùng nhau làm A/B mơ hồ"


def test_the_routes_still_say_different_things(handoff):
    """Shortening a wordy hook by falling back to the shared positioning line
    made two deliberately different routes come back identical."""
    from app.services.studio import director

    plan, _, _ = handoff
    headlines = [director._headline(r, plan) for r in plan.creative_routes]
    assert all(h.strip() for h in headlines)
    assert len(set(headlines)) == len(headlines)


def test_nothing_the_adapter_learned_is_dropped(handoff):
    """The regression that motivated this file: `load_plan` returned the
    contract and binned the rest."""
    _, _, notes = handoff
    for key in (
        "route_platforms",
        "routes_without_kit",
        "preserve_packaging",
        "art_direction_notes",
        "warnings",
        "stripped_placeholders",
    ):
        assert key in notes, f"notes thiếu {key!r}"


def test_a_route_with_no_kit_is_named_not_swallowed(handoff):
    """The real plan points route B at Tmall and Taobao. The studio has kits for
    neither, so that route produces nothing — which the user must be told,
    because a silently empty route looks like a bug in the renderer."""
    _, _, notes = handoff
    orphaned = notes["routes_without_kit"]
    unsupported = notes["platforms_unsupported"]
    if orphaned:
        assert unsupported, "route không có kit thì phải nêu được sàn nào thiếu"
    for route_id, platforms in notes["route_platforms"].items():
        if not platforms:
            assert route_id in orphaned


def test_no_editorial_placeholder_reaches_a_prompt(handoff):
    """Seedream renders whatever string it is handed. The real plan carries
    "[Placeholder khuyến mãi 9.9: chưa xác nhận điều kiện áp dụng]" inside
    message_angle, and an unstripped note becomes a marketplace banner."""
    plan, campaign_input, _ = handoff
    surfaces = [
        plan.positioning.main_campaign_angle,
        plan.positioning.key_selling_message,
        campaign_input.product_brief.price_or_promotion or "",
        *(r.message_angle for r in plan.creative_routes),
        *(r.hook_idea for r in plan.creative_routes),
    ]
    for text in surfaces:
        lowered = (text or "").casefold()
        assert "placeholder" not in lowered
        assert "chưa xác nhận" not in lowered
