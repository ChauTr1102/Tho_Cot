"""Verify-checklist QA endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, status

from app.schemas.common import StandardResponse
from app.schemas.qa_checklist import VerifyChecklistRequest, VerifyChecklistResponse
from app.services.qa_agent import agent_qa_checklist_service
from app.services.qa_checklist_service import qa_checklist_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=StandardResponse[VerifyChecklistResponse],
    status_code=status.HTTP_200_OK,
    summary="Run the QA checklist against a generated campaign plan + assets",
)
def verify_checklist(payload: VerifyChecklistRequest):
    """Verify a generated campaign (plan + assets) against a checklist an
    LLM agent derives from this specific campaign brief, then judges in
    parallel (one verifier call per checklist item — including multimodal
    checks against the actual generated images, loaded from their local
    file paths). Falls back to the fixed rule-based checklist
    (app/services/qa_checklist_service.py) if the agent pipeline itself
    fails (e.g. missing ARK_API_KEY or a ModelArk outage), so this endpoint
    never hard-fails just because the LLM is unavailable.

    Returns `passed` (True only when there are zero BLOCKER issues) plus a
    `regenerate` list telling the frontend exactly which stage(s) to call
    next to fix the detected issues:
      - "plan"   -> re-run positioning / creative-routes / AB-test-plan generation
      - "images" -> re-run product/marketplace image generation
      - "video"  -> re-run short-form video generation
      - "copy"   -> re-run commerce-copy generation

    When `passed` is True, `regenerate` is empty and the campaign is ready.
    """
    try:
        result = agent_qa_checklist_service.verify(payload)
    except Exception:
        logger.exception(
            "verify_checklist.agent_pipeline_failed iteration=%d falling_back_to_rule_based",
            payload.iteration,
        )
        result = qa_checklist_service.verify(payload)
    return StandardResponse(
        success=True,
        message="QA checklist passed" if result.passed else "QA checklist found issues",
        data=result,
    )
