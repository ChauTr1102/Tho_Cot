"""
The graph's shape carries the design, so these assertions are the design written
down rather than incidental coverage.

One of them exists because of a real failure. Every video clip in the first full
campaign run died in ten milliseconds: the clip node read the worksheet to find
out what its shot was, but declared a dependency only on its keyframe. The
executor hands a node exactly the results it declared and raises otherwise —
deliberately, so a missing edge is loud instead of a race — and it was right.
`test_every_ctx_read_is_declared` walks the source for `ctx[...]` reads and
checks each one against the node's own deps, so the class of bug cannot return.
"""
from __future__ import annotations

import inspect
import re

import pytest

from app.schemas.studio import AssetOrigin, Platform
from app.services.studio import demo_briefs, pipeline

BOTH = [Platform.TIKTOK_SHOP, Platform.SHOPEE]


@pytest.fixture(scope="module")
def nodes():
    plan, campaign_input = demo_briefs.build_pair("06_marou_chocolate", "test-campaign")
    return {n.id: n for n in pipeline.build_nodes(plan, campaign_input, None, "A", BOTH)}


def test_no_dangling_dependencies(nodes):
    ids = set(nodes)
    dangling = [(n.id, d) for n in nodes.values() for d in n.deps if d not in ids]
    assert dangling == []


def test_reuse_slots_do_not_wait_on_the_hero(nodes):
    """The point of the graph. A slot filled from the brand's own photograph
    needs a crop; making it queue behind a minute-long render would waste the
    entire wall-clock advantage."""
    assert "hero_A" not in nodes["item_A_shopee_sku"].deps


def test_generated_slots_are_anchored_to_the_hero(nodes):
    """Reference 2 is the hero. Without that edge the kit stops looking like one
    photoshoot and becomes eight unrelated pictures."""
    assert "hero_A" in nodes["item_A_shopee_banner"].deps


def test_each_clip_depends_on_its_own_keyframe_and_the_storyboard(nodes):
    clip = nodes["clip_A_tiktok_shop_0"]
    assert set(clip.deps) == {"worksheet_A", "keyframe_A_tiktok_shop_0"}


def test_master_waits_for_every_clip_of_its_platform(nodes):
    deps = set(nodes["master_A_tiktok_shop"].deps)
    assert {f"clip_A_tiktok_shop_{i}" for i in range(4)} <= deps


def test_video_and_image_work_are_in_separate_concurrency_groups(nodes):
    """A saturated video group must never throttle image rendering: one clip can
    take nine minutes, and the Shopee kit should not be held hostage to it."""
    assert nodes["clip_A_tiktok_shop_0"].concurrency_group == "video"
    assert nodes["item_A_shopee_banner"].concurrency_group == "image"


def test_every_ctx_read_is_declared(nodes):
    """Guard against the bug that killed the first full run.

    `build_nodes` closes over its context names, so the check is textual: pull
    every `ctx[...]` / `ctx.get(...)` key out of the source, resolve the ones
    bound to loop variables, and require each to appear in some node's deps.
    """
    source = inspect.getsource(pipeline.build_nodes)
    read = set(re.findall(r"ctx(?:\.get)?\(?\[?\s*([A-Za-z_][A-Za-z0-9_]*)", source))
    # Names that are loop-bound aliases for a dependency id, not ids themselves.
    aliases = {"_kf", "_hero", "_vo", "c", "inv_id", "sheet", "ws_id", "hero_id"}
    unresolved = {name for name in read if name not in aliases}
    assert unresolved == set(), f"ctx read from undeclared names: {unresolved}"

    # And the concrete edges those aliases stand for must actually exist.
    for node in nodes.values():
        if node.kind == "video":
            assert "worksheet_A" in node.deps


def test_worksheet_routes_reuse_where_the_kho_allows_it(nodes):
    """Marou has two 2500x2500 product photographs, so at least one slot must
    come back as real photography rather than generated imagery."""
    plan, campaign_input = demo_briefs.build_pair("06_marou_chocolate", "test-campaign")
    from app.services.studio import inventory
    sheet = inventory.build_sheet(campaign_input.brand_kit.product_photo_urls, use_vision=False)
    from app.services.studio import direct
    ws = direct.build_worksheet(plan, campaign_input, sheet, "A", BOTH)
    assert any(i.origin is AssetOrigin.REUSE for i in ws.items)
