"""Multipart frontend API for market/user research and campaign planning."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import BadRequestException
from app.api.deps import get_db
from app.schemas.research import ResearchInput
from app.services.research import ResearchOutputError
from app.services.research.input import encode_uploaded_visual_assets
from app.services.research_service import research_service
from app.services.campaign_service import campaign_service

router = APIRouter()
logger = logging.getLogger(__name__)


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
    db: Session = Depends(get_db),
):
    """Accept real images and return the raw campaign-plan JSON object."""
    started_at = time.monotonic()
    logger.info(
        "research_api.request_started campaign_id=%s schema_version=%s product_photos=%d "
        "existing_product_visuals=%d evidence_supplied=%s",
        campaign_id,
        schema_version,
        len(product_photos),
        len(existing_product_visuals or []),
        bool(evidence and evidence.strip()),
    )
    try:
        uploaded, asset_paths = await _read_assets(
            logo, product_photos, existing_product_visuals or []
        )
        logger.info(
            "research_api.assets_read campaign_id=%s asset_count=%d total_bytes=%d",
            campaign_id,
            len(uploaded),
            sum(len(content) for _, _, _, content in uploaded),
        )
        brand = _json_object(brand_kit, "brand_kit")
        brand.update(asset_paths)
        payload = ResearchInput.model_validate({
            "schema_version": schema_version,
            "campaign_id": campaign_id,
            "product_brief": _json_object(product_brief, "product_brief"),
            "brand_kit": brand,
            "audience_brief": _json_object(audience_brief, "audience_brief"),
            "market_signal": _json_object(market_signal, "market_signal"),
        })
        campaign_service.start_research(
            db,
            campaign_id=campaign_id,
            research_input=payload.model_dump(mode="json"),
        )
        visual_assets = encode_uploaded_visual_assets(uploaded)
        logger.info(
            "research_api.input_validated campaign_id=%s encoded_assets=%d",
            campaign_id,
            len(visual_assets[1]),
        )
        result = await run_in_threadpool(
            research_service.run,
            research_input=payload.model_dump(mode="json"),
            visual_assets=visual_assets,
            evidence=evidence,
            on_progress=lambda message: logger.info(
                "research_api.agent_progress campaign_id=%s message=%s",
                campaign_id,
                message,
            ),
        )
    except BadRequestException as exc:
        campaign_service.mark_research_failed(db, campaign_id=campaign_id)
        logger.warning(
            "research_api.input_rejected campaign_id=%s error=%s",
            campaign_id,
            exc.message,
        )
        raise
    except ValidationError as exc:
        logger.warning(
            "research_api.input_rejected campaign_id=%s validation_errors=%d",
            campaign_id,
            len(exc.errors()),
        )
        raise BadRequestException("Research input không đúng contract", error=exc.errors()) from exc
    except (ResearchOutputError, ValueError) as exc:
        campaign_service.mark_research_failed(db, campaign_id=campaign_id)
        logger.warning(
            "research_api.run_failed campaign_id=%s error_type=%s error=%s",
            campaign_id,
            type(exc).__name__,
            exc,
        )
        raise BadRequestException(message=str(exc)) from exc
    except Exception:
        campaign_service.mark_research_failed(db, campaign_id=campaign_id)
        logger.exception("research_api.unexpected_error campaign_id=%s", campaign_id)
        raise
    campaign_service.save_research_result(db, campaign_id=campaign_id, result=result)
    logger.info(
        "research_api.request_completed campaign_id=%s duration_ms=%d sources=%d tool_calls=%d",
        campaign_id,
        round((time.monotonic() - started_at) * 1000),
        len(result.get("sources", [])),
        len(result.get("research_tool_calls", [])),
    )
    return result["plan"]
