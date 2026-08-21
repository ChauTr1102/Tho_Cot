"""Resolve dot-path field references (e.g. "commerce_copy.product_description")
against CampaignInputDTO/CampaignOutputDTO instances, for feeding the actual
relevant content to the per-item verifier agent."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def resolve_field(root: BaseModel, dot_path: str) -> Any:
    """Walk a dot-path (e.g. 'product_collection_image_set.product_hero_image')
    against a Pydantic model instance. Returns None if any segment is missing
    or the path traverses into a list without an index (in which case the
    whole list is returned instead, since checklist items reference list
    fields directly, e.g. 'creative_routes')."""
    current: Any = root
    for segment in dot_path.split("."):
        if isinstance(current, BaseModel):
            if segment not in current.__class__.model_fields:
                return None
            current = getattr(current, segment)
        elif isinstance(current, dict):
            current = current.get(segment)
        elif isinstance(current, list):
            # Path continued past a list without an index; nothing further
            # to resolve — return the list itself as the closest match.
            return current
        else:
            return None
    return current


def stringify_field(value: Any) -> str:
    """Render a resolved field value as readable text for the verifier
    agent's prompt (lists of Pydantic models, plain strings, etc.)."""
    if value is None:
        return "(không có giá trị)"
    if isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    if isinstance(value, list):
        rendered = []
        for item in value:
            if isinstance(item, BaseModel):
                rendered.append(item.model_dump_json(indent=2))
            else:
                rendered.append(str(item))
        return "\n".join(rendered) if rendered else "(danh sách rỗng)"
    return str(value)
