import json
from pathlib import Path
import pytest
from app.services.research import CAMPAIGN_PLAN_SCHEMA, EXA_MCP_URL, ExaResearchAgent, RawModelClient, ResearchOutputError, extract_output_text, validate_campaign_plan
from app.services.research import agents as research_agents
from app.services.research.prompts import CREATIVE_SYSTEM, EDITOR_SYSTEM, EVIDENCE_AUDITOR_SYSTEM, FOLLOWUP_SEARCH_SYSTEM, POSITIONING_SYSTEM, RESEARCH_DISCOVERY_SYSTEM, RESEARCH_SYSTEM
from app.services.research_service import ResearchService
from app.services.research.input import load_research_input


def sample_plan():
    evidence = [{"basis": "product_brief", "detail": "brief fact", "source_url": None}]
    decision = {"decision": "decision", "rationale": "why", "evidence": evidence}
    route = {"route_name": "Route", "hook_idea": "Hook", "visual_direction": "Visual",
             "message_angle": "Message", "suggested_platform_usage": ["TikTok"],
             "rationale": "Why", "evidence": evidence}
    return {"schema_version": "1.0", "product_positioning": {
        "main_campaign_angle": decision, "target_audience": decision,
        "key_selling_message": decision,
        "benefit_hierarchy": [{"rank": 1, "benefit": "Benefit", "rationale": "Why", "evidence": evidence}]},
        "creative_routes": [route, {**route, "route_name": "Route B"}],
        "source_summary": {"external_sources_supplied": False, "sources": [], "assumptions": []}}


class FakeResponse:
    status_code = 200
    text = ""
    def __init__(self, text): self._text = text
    def raise_for_status(self): return None
    def json(self):
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": self._text}]}]}
    def iter_lines(self, decode_unicode=False):
        tool_name = "web_fetch_exa" if self._text.casefold().startswith("nghiên cứu") else "web_search_exa"
        events = [
            {"type": "response.output_item.added", "item": {"type": "mcp_call", "name": tool_name}},
            {"type": "response.output_text.delta", "delta": self._text},
        ]
        for event in events:
            yield "data: " + json.dumps(event)


def test_raw_client_sends_no_tools():
    calls = []
    def fake_post(url, **kwargs):
        calls.append(kwargs["json"]); return FakeResponse("draft")
    client = RawModelClient("test-key", post=fake_post)
    assert client.ask(system=POSITIONING_SYSTEM, user="brief") == "draft"
    assert "tools" not in calls[0]
    assert calls[0]["thinking"] == {"type": "disabled"}


def test_research_service_runs_exa_then_four_specialists_and_structured_editor():
    calls = []
    outputs = iter([
        "MARKET SOCIAL https://example.com/market",
        "SCIENCE https://example.com/science",
        "NGHIÊN CỨU https://example.com",
        "POSITIONING https://example.com/positioning",
        "CREATIVE https://example.com/creative",
        "AUDIT RESEARCH https://example.com/audit-research",
        "AUDIT https://example.com/audit",
        json.dumps(sample_plan()),
    ])
    def fake_post(url, **kwargs):
        calls.append(kwargs["json"]); return FakeResponse(next(outputs))
    result = ResearchService(RawModelClient("test-key", post=fake_post)).run(
        "A premium tea", evidence="Source: customer survey",
    )
    assert result["engine"] == "exa_specialists"
    assert result["plan"]["schema_version"] == "1.0"
    assert calls[0]["tools"][0]["server_url"] == EXA_MCP_URL
    tool_indices = [0, 1, 2, 5]
    assert all(calls[index]["tools"][0]["server_url"] == EXA_MCP_URL for index in tool_indices)
    assert all("tools" not in calls[index] for index in [3, 4, 6, 7])
    assert result["research_tool_calls"] == [
        "web_search_exa", "web_search_exa", "web_fetch_exa", "web_search_exa",
    ]
    assert [call["input"][0]["content"] for call in calls] == [
        RESEARCH_DISCOVERY_SYSTEM, RESEARCH_DISCOVERY_SYSTEM, RESEARCH_SYSTEM,
        POSITIONING_SYSTEM, CREATIVE_SYSTEM, FOLLOWUP_SEARCH_SYSTEM,
        EVIDENCE_AUDITOR_SYSTEM, EDITOR_SYSTEM]
    assert "MARKET SOCIAL" in calls[2]["input"][1]["content"]
    assert "SCIENCE" in calls[2]["input"][1]["content"]
    assert "NGHIÊN CỨU" in calls[3]["input"][1]["content"]
    assert "POSITIONING" in calls[4]["input"][1]["content"]
    assert "CREATIVE" in calls[5]["input"][1]["content"]
    assert "AUDIT RESEARCH" in calls[6]["input"][1]["content"]
    assert "AUDIT" in calls[7]["input"][1]["content"]
    assert calls[7]["text"]["format"]["schema"] == CAMPAIGN_PLAN_SCHEMA
    assert calls[7]["text"]["format"]["strict"] is True
    assert calls[7]["max_output_tokens"] == 9000


def test_missing_sources_are_disclosed():
    prompts = []
    outputs = iter([
        "Market social https://example.com/market", "Science https://example.com/science",
        "Nghiên cứu https://example.com/research", "positioning", "creative",
        "Audit research https://example.com/audit-research", "audit", json.dumps(sample_plan()),
    ])
    def fake_post(url, **kwargs):
        prompts.append(kwargs["json"]["input"][1]["content"]); return FakeResponse(next(outputs))
    ResearchService(RawModelClient("test-key", post=fake_post)).run("A product")
    assert "Không có tệp evidence từ người dùng" in prompts[0]


def test_extract_output_text_supports_direct_field():
    assert extract_output_text({"output_text": " answer "}) == "answer"


def test_exa_research_accepts_useful_text_without_literal_url():
    class NoUrlResponse(FakeResponse):
        def iter_lines(self, decode_unicode=False):
            events = [
                {"type": "response.output_item.added", "item": {
                    "type": "mcp_call", "name": "web_search_exa",
                }},
                {"type": "response.output_text.delta", "delta": "Đã tìm thấy tín hiệu thị trường hữu ích."},
            ]
            for event in events:
                yield "data: " + json.dumps(event)

    client = RawModelClient("test-key", post=lambda *_args, **_kwargs: NoUrlResponse("unused"))
    text, calls = client.research_with_exa(
        system="search", user="brief", required_tool="web_search",
    )
    assert text == "Đã tìm thấy tín hiệu thị trường hữu ích."
    assert calls == ["web_search_exa"]


def test_exa_fetch_failure_retries_only_fetch_phase():
    class FlakyClient:
        def __init__(self): self.required_tools = []
        def research_with_exa(self, **kwargs):
            self.required_tools.append(kwargs["required_tool"])
            if kwargs["required_tool"] == "web_search":
                return "Nguồn https://example.com", ["web_search_exa"]
            if self.required_tools.count("web_fetch") == 1:
                raise ResearchOutputError("lỗi MCP tạm thời")
            return "Nghiên cứu https://example.com", ["web_fetch_exa"]

    client = FlakyClient()
    report, calls = ExaResearchAgent(client).run("brief", "không có")
    assert report.startswith("Nghiên cứu")
    assert calls == ["web_search_exa", "web_search_exa", "web_search_exa", "web_fetch_exa"]
    assert client.required_tools == ["web_search", "web_search", "web_search", "web_fetch", "web_fetch"]


def test_exa_exhausted_retries_returns_safe_unverified_research(monkeypatch):
    class UnavailableClient:
        def __init__(self): self.calls = 0
        def research_with_exa(self, **kwargs):
            self.calls += 1
            raise ResearchOutputError("Exa research không trả về nội dung")

    monkeypatch.setattr(research_agents.time, "sleep", lambda _seconds: None)
    client = UnavailableClient()

    report, calls = ExaResearchAgent(client).run("brief", "không có")

    assert report.startswith("CHẾ ĐỘ AN TOÀN")
    assert "không được dùng chúng để khẳng định" in report
    assert calls == []
    assert client.calls == research_agents.EXA_MAX_ATTEMPTS * 4


def test_g7_structured_input_sends_all_three_images_to_every_specialist():
    workspace = Path(__file__).resolve().parents[2]
    structured = load_research_input(
        workspace / "sample_data/05_trung_nguyen_g7/research_input.json"
    )
    calls = []
    outputs = iter([
        "Market social https://example.com/market", "Science https://example.com/science",
        "Nghiên cứu https://example.com/research", "positioning", "creative",
        "Audit research https://example.com/audit-research", "audit", json.dumps(sample_plan()),
    ])
    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return FakeResponse(next(outputs))

    result = ResearchService(RawModelClient("test-key", post=fake_post)).run(
        research_input=structured, workspace_root=workspace,
    )
    assert result["campaign_id"] == "trung-nguyen-g7-cross-border-9-9"
    assert len(result["input_assets"]) == 3
    for call in calls:
        user_content = call["input"][1]["content"]
        assert user_content[0]["type"] == "input_text"
        assert [item["type"] for item in user_content[1:]] == ["input_image"] * 3
        assert all(item["image_url"].startswith("data:image/") for item in user_content[1:])


def test_source_summary_rejects_scheme_without_hostname():
    plan = sample_plan()
    plan["source_summary"]["sources"] = [{
        "title": "Nguồn lỗi", "url": "https://", "usage": "Không hợp lệ",
    }]
    with pytest.raises(ResearchOutputError, match="URL HTTP"):
        validate_campaign_plan(plan)


def test_schema_supports_external_research_evidence():
    assert "external_research" in CAMPAIGN_PLAN_SCHEMA["properties"]["product_positioning"][
        "properties"
    ]["main_campaign_angle"]["properties"]["evidence"]["items"]["properties"]["basis"]["enum"]


def test_search_budget_is_fixed_to_two_discovery_and_one_audit_followup():
    calls = []
    outputs = iter([
        "Market social", "Science official", "Nghiên cứu đã đọc",
        "positioning", "creative", "Audit research", "audit", json.dumps(sample_plan()),
    ])

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return FakeResponse(next(outputs))

    result = ResearchService(RawModelClient("test-key", post=fake_post)).run("A product")

    assert result["plan"]["schema_version"] == "1.0"
    assert len(calls) == 8
    assert ["tools" in call for call in calls] == [True, True, True, False, False, True, False, False]
    assert "MARKET + SOCIAL/CONSUMER" in calls[0]["input"][1]["content"]
