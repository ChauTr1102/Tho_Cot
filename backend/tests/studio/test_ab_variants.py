"""
The A/B pair: two creative routes, two posters.

Research designs a test — each route carries its own hypothesis, its own way of
measuring it — and until the studio rendered a poster per route there was
nothing to run it with. The final report showed two objectives above one set of
artwork, which is a plan rather than an experiment.

What must stay true: the pair varies the argument and nothing else. Same
product, same offer, same call to action — if the badge differed too, a result
would not say which change caused it.
"""
from __future__ import annotations

import pytest

from app.schemas.studio import CampaignInput, CampaignPlan
from app.services.studio import director, from_research, saved
from pathlib import Path

DB = Path("sql_app.db")
pytestmark = pytest.mark.skipif(
    not DB.is_file(), reason="sql_app.db thuộc bước research, chưa có ở checkout này"
)


@pytest.fixture(scope="module")
def pair():
    rows = [r for r in from_research.list_campaigns() if r.get("status") == "researched"]
    if not rows:
        pytest.skip("chưa có campaign nào research xong")
    plan, campaign_input, _ = from_research.load_pair(rows[0]["id"])
    if len(plan.creative_routes) < 2:
        pytest.skip("plan chỉ có một route, không có gì để so")
    return plan, campaign_input


def _draft(platforms=("shopee",)):
    return director.Draft(
        summary="",
        register=director.Register(
            name="n", lens="l", light="li", surface="s", grade="g",
            palette=[], why="w", source="preset",
        ),
        platforms=list(platforms),
        deliverables=[],
        video_shots=0,
        video_seconds=0,
        notes=[],
    )


def _ab_nodes(plan: CampaignPlan, campaign_input: CampaignInput):
    spec = director.plan_graph(_draft(), plan, campaign_input, with_video=False)
    return [n for n in spec.nodes if n.route]


def test_one_poster_per_route(pair):
    nodes = _ab_nodes(*pair)
    assert len(nodes) == 2
    assert {n.route for n in nodes} == {r.route_id for r in pair[0].creative_routes[:2]}


def test_the_headline_is_what_differs(pair):
    """The variable under test. Two routes that print the same line are not an
    A/B test, they are the same poster twice — which is what the studio produced
    when `_campaign_texts` always read `creative_routes[0]`."""
    nodes = _ab_nodes(*pair)
    headlines = [dict(n.texts).get("headline") for n in nodes]
    assert all(headlines), "route nào cũng phải có headline"
    assert headlines[0] != headlines[1]


def test_the_offer_does_not_differ(pair):
    """Everything except the argument is held constant. A badge that changed
    with the headline would make a win unattributable."""
    nodes = _ab_nodes(*pair)
    badges = [dict(n.texts).get("badge") for n in nodes]
    ctas = [dict(n.texts).get("cta") for n in nodes]
    assert badges[0] == badges[1]
    assert ctas[0] == ctas[1]


def test_each_route_stages_its_own_scene(pair):
    """Upstream writes `visual_direction` per route and the two stage the
    product differently on purpose. One scene for both would test typography."""
    nodes = _ab_nodes(*pair)
    assert nodes[0].prompt != nodes[1].prompt


def test_both_posters_anchor_to_the_same_hero(pair):
    """The pair has to look like one photoshoot or the comparison measures
    lighting rather than message."""
    for node in _ab_nodes(*pair):
        assert node.deps == ["hero"]


def test_a_kit_without_the_pair_reports_nothing_rather_than_half(pair):
    """Campaigns rendered before this existed have no posters, and `{}` is the
    signal the report needs to fall back rather than show one variant twice."""
    assert saved.ab_pair("c-campaign-khong-ton-tai") == {}
