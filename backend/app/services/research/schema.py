"""JSON Schema and local validation for campaign research output."""
from typing import Any


class ResearchOutputError(RuntimeError):
    pass


EVIDENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "basis": {"type": "string", "enum": [
            "product_brief", "supplied_source", "external_research",
            "general_marketing_knowledge", "assumption"
        ]},
        "detail": {"type": "string"},
        "source_url": {
            "anyOf": [
                {"type": "null"},
                {"type": "string", "pattern": "^https?://[^\\s/]+(?:/[^\\s]*)?$"},
            ]
        },
    },
    "required": ["basis", "detail", "source_url"],
    "additionalProperties": False,
}

DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string"},
        "rationale": {"type": "string"},
        "evidence": {"type": "array", "items": EVIDENCE_SCHEMA, "minItems": 1},
    },
    "required": ["decision", "rationale", "evidence"],
    "additionalProperties": False,
}

CAMPAIGN_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "enum": ["1.0"]},
        "product_positioning": {
            "type": "object",
            "properties": {
                "main_campaign_angle": DECISION_SCHEMA,
                "target_audience": DECISION_SCHEMA,
                "key_selling_message": DECISION_SCHEMA,
                "benefit_hierarchy": {
                    "type": "array", "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "rank": {"type": "integer"}, "benefit": {"type": "string"},
                            "rationale": {"type": "string"},
                            "evidence": {"type": "array", "items": EVIDENCE_SCHEMA, "minItems": 1},
                        },
                        "required": ["rank", "benefit", "rationale", "evidence"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["main_campaign_angle", "target_audience", "key_selling_message", "benefit_hierarchy"],
            "additionalProperties": False,
        },
        "creative_routes": {
            "type": "array", "minItems": 2, "maxItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "route_name": {"type": "string"}, "hook_idea": {"type": "string"},
                    "visual_direction": {"type": "string"}, "message_angle": {"type": "string"},
                    "test_objective": {"type": "string"}, "testing_plan": {"type": "string"},
                    "suggested_platform_usage": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "rationale": {"type": "string"},
                    "evidence": {"type": "array", "items": EVIDENCE_SCHEMA, "minItems": 1},
                },
                "required": ["route_name", "hook_idea", "visual_direction", "message_angle", "test_objective", "testing_plan", "suggested_platform_usage", "rationale", "evidence"],
                "additionalProperties": False,
            },
        },
        "source_summary": {
            "type": "object",
            "properties": {
                "external_sources_supplied": {"type": "boolean"},
                "sources": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string", "pattern": "^https?://[^\\s/]+(?:/[^\\s]*)?$"},
                        "usage": {"type": "string"},
                    },
                    "required": ["title", "url", "usage"], "additionalProperties": False,
                }},
                "assumptions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["external_sources_supplied", "sources", "assumptions"],
            "additionalProperties": False,
        },
    },
    "required": ["schema_version", "product_positioning", "creative_routes", "source_summary"],
    "additionalProperties": False,
}


def validate_campaign_plan(plan: Any) -> None:
    from urllib.parse import urlparse

    def valid_url(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    if not isinstance(plan, dict) or plan.get("schema_version") != "1.0":
        raise ResearchOutputError("schema_version không hợp lệ")
    positioning = plan.get("product_positioning")
    if not isinstance(positioning, dict):
        raise ResearchOutputError("Thiếu product_positioning")
    for key in ("main_campaign_angle", "target_audience", "key_selling_message"):
        block = positioning.get(key)
        if not isinstance(block, dict) or not all(k in block for k in ("decision", "rationale", "evidence")):
            raise ResearchOutputError(f"Khối {key} không hợp lệ")
    if not isinstance(positioning.get("benefit_hierarchy"), list) or not positioning["benefit_hierarchy"]:
        raise ResearchOutputError("benefit_hierarchy phải có dữ liệu")
    routes = plan.get("creative_routes")
    if not isinstance(routes, list) or len(routes) != 2:
        raise ResearchOutputError("creative_routes phải có đúng hai hướng")
    required = {"route_name", "hook_idea", "visual_direction", "message_angle", "test_objective", "testing_plan", "suggested_platform_usage", "rationale", "evidence"}
    if any(not isinstance(route, dict) or not required <= route.keys() for route in routes):
        raise ResearchOutputError("creative route không hợp lệ")
    summary = plan.get("source_summary")
    if not isinstance(summary, dict) or not all(k in summary for k in ("external_sources_supplied", "sources", "assumptions")):
        raise ResearchOutputError("source_summary không hợp lệ")
    for source in summary["sources"]:
        if not isinstance(source, dict) or not valid_url(source.get("url")):
            raise ResearchOutputError("Mọi nguồn trong source_summary phải có URL HTTP(S) hợp lệ")
    evidence_blocks = [positioning[key] for key in ("main_campaign_angle", "target_audience", "key_selling_message")]
    evidence_blocks.extend(positioning["benefit_hierarchy"])
    evidence_blocks.extend(routes)
    for block in evidence_blocks:
        for evidence in block.get("evidence", []):
            source_url = evidence.get("source_url")
            if source_url is not None and not valid_url(source_url):
                raise ResearchOutputError("source_url trong evidence phải là null hoặc URL HTTP(S) đầy đủ")
