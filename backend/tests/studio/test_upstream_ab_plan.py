"""
The A/B plan, once the research contract started stating it.

`test_objective` and `testing_plan` were added to each creative route after this
adapter was written. Before that the plan carried no A/B block at all, so the
adapter synthesised one — correct then, and wrong now: a synthesised sentence
laid over a real experiment reads as though the team never designed one.

The two shapes must both work. Campaigns researched before the contract changed
are still in the database and still have to open.
"""
from __future__ import annotations

import pytest

from app.services.studio import upstream

CID = "c-test"


def _route(route_id: str, **extra):
    route = {
        "route_name": f"Route {route_id}",
        "hook_idea": f'"Câu hook của {route_id}"',
        "visual_direction": "Ảnh sản phẩm trên nền tối",
        "message_angle": "Góc thông điệp",
        "suggested_platform_usage": ["TikTok Shop", "Shopee"],
        "rationale": "Vì thế",
        "evidence": [],
    }
    route.update(extra)
    return route


def _plan(routes):
    return {
        "product_positioning": {
            "main_campaign_angle": "Góc chính",
            "target_audience": "Người mua",
            "key_selling_message": "Thông điệp",
        },
        "creative_routes": routes,
    }


class TestRoutesStateTheTest:
    @pytest.fixture
    def parsed(self):
        return upstream.parse_plan(
            _plan([
                _route("A",
                       test_objective="Hook tiện lợi có tăng CTR không",
                       testing_plan="Đổi 3 giây đầu, đo CTR và tỉ lệ thêm vào giỏ."),
                _route("B",
                       test_objective="Hook đặc sản có tăng CVR không",
                       testing_plan="Giữ nguyên khung hình, đo CVR."),
            ]),
            CID,
        )

    def test_the_stated_objectives_are_used_verbatim(self, parsed):
        what = parsed.plan.ab_test_plan.what_to_test
        assert "Hook tiện lợi có tăng CTR không" in what
        assert "Hook đặc sản có tăng CVR không" in what

    def test_the_stated_plan_becomes_the_expected_learning(self, parsed):
        assert "đo CTR" in parsed.plan.ab_test_plan.expected_learning

    def test_metrics_named_in_prose_are_recognised(self, parsed):
        metrics = parsed.plan.ab_test_plan.success_metrics
        assert "CTR" in metrics
        assert "CVR" in metrics
        assert "Add-to-cart rate" in metrics

    def test_no_warning_claims_the_plan_was_missing(self, parsed):
        """The warning existed to say "upstream gave us nothing". Now it has."""
        assert not any("synthesised" in w for w in parsed.warnings)

    def test_the_routes_are_named_by_their_real_ids(self, parsed):
        ids = [r.route_id for r in parsed.plan.creative_routes]
        assert parsed.plan.ab_test_plan.route_a in ids
        assert parsed.plan.ab_test_plan.route_b in ids


class TestOlderCampaignsWithoutTheFields:
    """Rows researched before the contract changed are still in the database."""

    @pytest.fixture
    def parsed(self):
        return upstream.parse_plan(_plan([_route("A"), _route("B")]), CID)

    def test_it_still_parses(self, parsed):
        assert len(parsed.plan.creative_routes) == 2

    def test_a_plan_is_still_synthesised(self, parsed):
        assert parsed.plan.ab_test_plan.what_to_test
        assert parsed.plan.ab_test_plan.success_metrics

    def test_and_says_so(self, parsed):
        assert any("synthesised" in w for w in parsed.warnings)


class TestMetricScanning:
    @pytest.mark.parametrize("prose,expected", [
        ("đo CTR và CVR", ["CTR", "CVR"]),
        ("theo dõi tỉ lệ chuyển đổi", ["CVR"]),
        ("watch time trung bình", ["Watch time"]),
        ("ROAS theo tuần", ["ROAS"]),
    ])
    def test_reads_the_metrics_it_knows(self, prose, expected):
        assert upstream._metrics_named_in(prose) == expected

    def test_names_nothing_when_the_prose_names_nothing(self):
        """Returning [] lets the caller fall back to the defaults. Guessing at
        every noun would file "engagement is important" as a target."""
        assert upstream._metrics_named_in("làm cho thật hay") == []
        assert upstream._metrics_named_in("") == []
