"""JSON Schema for the agent-generated QA checklist and its per-item
verification results. Mirrors app/services/research/schema.py's pattern:
a strict JSON schema enforced via ModelArk's json_schema response format,
plus a light local validator as a defense-in-depth check.
"""
from typing import Any

from app.services.research.schema import ResearchOutputError

# -- Checklist item categories, mapped 1:1 to the existing RegenerateTarget
# values (app/schemas/qa_checklist.py) so results can drive the same
# frontend "which side to regenerate" contract.
CHECKLIST_CATEGORIES = ["plan", "asset"]

CHECKLIST_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "description": "Short unique slug for this checklist item, e.g. 'FORBIDDEN_CLAIM_CURES_BLOATING'.",
        },
        "category": {
            "type": "string", "enum": CHECKLIST_CATEGORIES,
            "description": (
                "'plan' if fixing this issue means re-running positioning/creative-routes/"
                "AB-test-plan generation; 'asset' if it means re-running image, video, or "
                "commerce-copy generation."
            ),
        },
        "severity": {"type": "string", "enum": ["BLOCKER", "WARNING"]},
        "description": {
            "type": "string",
            "description": "What this item checks, written so a verifier agent can judge pass/fail from it alone.",
        },
        "target_fields": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "description": (
                "Dot-path field(s) on CampaignOutputDTO this item inspects, e.g. "
                "'commerce_copy.product_description' or 'product_collection_image_set.product_hero_image'."
            ),
        },
        "needs_image": {
            "type": "boolean",
            "description": "True if verifying this item requires looking at an actual image file.",
        },
    },
    "required": ["id", "category", "severity", "description", "target_fields", "needs_image"],
    "additionalProperties": False,
}

CHECKLIST_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": CHECKLIST_ITEM_SCHEMA,
            "minItems": 1,
        },
    },
    "required": ["items"],
    "additionalProperties": False,
}

VERIFICATION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "pass": {"type": "boolean"},
        "reason": {
            "type": "string",
            "description": "One or two sentences explaining the pass/fail judgment, citing the actual content inspected.",
        },
    },
    "required": ["pass", "reason"],
    "additionalProperties": False,
}


def validate_checklist(payload: Any) -> list[dict]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list) or not payload["items"]:
        raise ResearchOutputError("Checklist phải là object có 'items' là danh sách không rỗng")
    seen_ids: set[str] = set()
    for item in payload["items"]:
        if not isinstance(item, dict):
            raise ResearchOutputError("Mỗi checklist item phải là object")
        missing = {"id", "category", "severity", "description", "target_fields", "needs_image"} - item.keys()
        if missing:
            raise ResearchOutputError(f"Checklist item thiếu field: {missing}")
        if item["category"] not in CHECKLIST_CATEGORIES:
            raise ResearchOutputError(f"category không hợp lệ: {item['category']}")
        if item["severity"] not in {"BLOCKER", "WARNING"}:
            raise ResearchOutputError(f"severity không hợp lệ: {item['severity']}")
        if not isinstance(item["target_fields"], list) or not item["target_fields"]:
            raise ResearchOutputError(f"target_fields phải là danh sách không rỗng cho item {item['id']}")
        if item["id"] in seen_ids:
            raise ResearchOutputError(f"Trùng checklist item id: {item['id']}")
        seen_ids.add(item["id"])
    return payload["items"]


def validate_verification_result(payload: Any) -> dict:
    if not isinstance(payload, dict) or "pass" not in payload or "reason" not in payload:
        raise ResearchOutputError("Kết quả kiểm tra phải có 'pass' (bool) và 'reason' (string)")
    if not isinstance(payload["pass"], bool):
        raise ResearchOutputError("'pass' phải là boolean")
    return payload
