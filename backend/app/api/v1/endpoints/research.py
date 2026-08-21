"""Multipart frontend API for market/user research and campaign planning."""
from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import BadRequestException
from app.schemas.research import ResearchInput
from app.services.research import ResearchOutputError
from app.services.research.input import encode_uploaded_visual_assets
from app.services.research_service import research_service

router = APIRouter()


def _json_object(value: str, field_name: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise BadRequestException(f"Trường {field_name} phải là JSON object hợp lệ") from exc
    if not isinstance(parsed, dict):
        raise BadRequestException(f"Trường {field_name} phải là JSON object")
    return parsed


async def _read_assets(
    logo: UploadFile,
    product_photos: list[UploadFile],
    existing_product_visuals: list[UploadFile],
) -> tuple[list[tuple[str, str, str | None, bytes]], dict[str, Any]]:
    uploads = [("logo", logo)]
    uploads.extend((f"product_photos[{index}]", item) for index, item in enumerate(product_photos))
    uploads.extend((f"existing_product_visuals[{index}]", item) for index, item in enumerate(existing_product_visuals))
    assets = []
    for label, upload in uploads:
        assets.append((label, upload.filename or label, upload.content_type, await upload.read()))
    paths = {
        "logo": logo.filename or "logo",
        "product_photos": [item.filename or f"product_{index}" for index, item in enumerate(product_photos)],
        "existing_product_visuals": [item.filename or f"visual_{index}" for index, item in enumerate(existing_product_visuals)],
    }
    return assets, paths


@router.post(
    "/run",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Nghiên cứu thị trường và lập campaign plan từ form + ảnh",
)
async def run_research(
    campaign_id: str = Form(...),
    product_brief: str = Form(..., description="JSON object product_brief"),
    brand_kit: str = Form(..., description="JSON object brand_kit; đường dẫn ảnh được thay bằng file upload"),
    audience_brief: str = Form(..., description="JSON object audience_brief"),
    market_signal: str = Form(..., description="JSON object market_signal"),
    logo: UploadFile = File(...),
    product_photos: list[UploadFile] = File(...),
    existing_product_visuals: list[UploadFile] | None = File(default=None),
    schema_version: Literal["1.0"] = Form("1.0"),
    evidence: str | None = Form(default=None),
):
    """Accept real images and return the raw campaign-plan JSON object."""
    uploaded, asset_paths = await _read_assets(logo, product_photos, existing_product_visuals or [])
    brand = _json_object(brand_kit, "brand_kit")
    brand.update(asset_paths)
    try:
        payload = ResearchInput.model_validate({
            "schema_version": schema_version,
            "campaign_id": campaign_id,
            "product_brief": _json_object(product_brief, "product_brief"),
            "brand_kit": brand,
            "audience_brief": _json_object(audience_brief, "audience_brief"),
            "market_signal": _json_object(market_signal, "market_signal"),
        })
        visual_assets = encode_uploaded_visual_assets(uploaded)
        result = await run_in_threadpool(
            research_service.run,
            research_input=payload.model_dump(mode="json"),
            visual_assets=visual_assets,
            evidence=evidence,
        )
    except ValidationError as exc:
        raise BadRequestException("Research input không đúng contract", error=exc.errors()) from exc
    except (ResearchOutputError, ValueError) as exc:
        raise BadRequestException(message=str(exc)) from exc
    return result["plan"]
