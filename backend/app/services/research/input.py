"""Load and validate structured research input plus its visual assets."""
from __future__ import annotations

import base64
import json
import mimetypes
import pathlib
from typing import Any

from jsonschema import Draft202012Validator

from app.services.research.schema import ResearchOutputError

_SCHEMA_PATH = pathlib.Path(__file__).with_name("input_schema.json")
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/tiff"}
_MAX_IMAGE_BYTES = 20 * 1024 * 1024


def validate_research_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ResearchOutputError("Research input phải là một JSON object")
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "$"
        raise ResearchOutputError(f"Research input không đúng schema tại {location}: {error.message}")
    return payload


def load_research_input(path: pathlib.Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchOutputError(f"Không thể đọc research input {path}: {exc}") from exc
    return validate_research_input(payload)


def _asset_entries(payload: dict[str, Any]) -> list[tuple[str, str]]:
    brand_kit = payload["brand_kit"]
    entries = [("logo", brand_kit["logo"])]
    entries.extend((f"product_photos[{index}]", value) for index, value in enumerate(brand_kit["product_photos"]))
    entries.extend((f"existing_product_visuals[{index}]", value) for index, value in enumerate(brand_kit["existing_product_visuals"]))
    return entries


def load_visual_assets(payload: dict[str, Any], workspace_root: pathlib.Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Return model-ready image URLs and a safe manifest included in the prompt."""
    root = workspace_root.resolve()
    image_urls: list[str] = []
    manifest: list[dict[str, Any]] = []
    for label, value in _asset_entries(payload):
        if value.startswith(("http://", "https://")):
            image_urls.append(value)
            manifest.append({"label": label, "source": value, "transport": "remote_url"})
            continue
        path = (root / value).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ResearchOutputError(f"Asset nằm ngoài workspace: {value}") from exc
        if not path.is_file():
            raise ResearchOutputError(f"Không tìm thấy asset: {value}")
        mime_type = mimetypes.guess_type(path.name)[0]
        if mime_type not in _ALLOWED_IMAGE_TYPES:
            raise ResearchOutputError(f"Định dạng ảnh không hỗ trợ: {value} ({mime_type})")
        size = path.stat().st_size
        if size > _MAX_IMAGE_BYTES:
            raise ResearchOutputError(f"Ảnh vượt quá 20 MB: {value}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        image_urls.append(f"data:{mime_type};base64,{encoded}")
        manifest.append({"label": label, "source": value, "mime_type": mime_type, "bytes": size, "transport": "base64_data_url"})
    return image_urls, manifest
