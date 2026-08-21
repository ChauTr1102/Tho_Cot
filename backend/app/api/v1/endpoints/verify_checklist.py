"""Verify-checklist QA endpoints."""
from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.common import StandardResponse
from app.schemas.qa_checklist import VerifyChecklistRequest, VerifyChecklistResponse
from app.services.qa_checklist_service import qa_checklist_service

router = APIRouter()


@router.post(
    "",
    response_model=StandardResponse[VerifyChecklistResponse],
    status_code=status.HTTP_200_OK,
    summary="Run the QA checklist against a generated campaign plan + assets",
)
def verify_checklist(payload: VerifyChecklistRequest):
    """Verify a generated campaign (plan + assets) against the BP-01 QA
    checklist (structural completeness, market-research sourcing, and
    brand-brief compliance).

    Returns `passed` (True only when there are zero BLOCKER issues) plus a
    `regenerate` list telling the frontend exactly which stage(s) to call
    next to fix the detected issues:
      - "plan"   -> re-run positioning / creative-routes / AB-test-plan generation
      - "images" -> re-run product/marketplace image generation
      - "video"  -> re-run short-form video generation
      - "copy"   -> re-run commerce-copy generation

    When `passed` is True, `regenerate` is empty and the campaign is ready.
    """
    result = qa_checklist_service.verify(payload)
    return StandardResponse(
        success=True,
        message="QA checklist passed" if result.passed else "QA checklist found issues",
        data=result,
    )
