"""Schemas for POST /verify-checklist.

Mirrors the rule-based QA checklist in QA_checklist.py (the source of truth
for this feature — see QA_checklist/README.md) but runs against the real
CampaignInputDTO / CampaignOutputDTO contracts already shared with the
frontend (app/schemas/campaign_dto.py), instead of QA_checklist's own
standalone CampaignInput/CampaignPlan/AssetBundle models.

`regenerate` tells the frontend exactly which generation stage(s) to call
next to fix the detected issues, so it doesn't have to re-run the whole
pipeline on every QA failure:
  - "plan"   -> re-run positioning/creative-routes/AB-test-plan generation
  - "images" -> re-run the product/marketplace image generation step
  - "video"  -> re-run the short-form video generation step
  - "copy"   -> re-run the commerce-copy generation step
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.campaign_dto import CampaignInputDTO, CampaignOutputDTO


class QASeverity(str, Enum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"


class RegenerateTarget(str, Enum):
    """Which generation stage the frontend should call next to fix an issue."""
    PLAN = "plan"
    IMAGES = "images"
    VIDEO = "video"
    COPY = "copy"


class QAIssue(BaseModel):
    rule_id: str
    severity: QASeverity
    message: str
    field: str
    regenerate: RegenerateTarget = Field(
        description="Which stage produced the offending content and should be regenerated."
    )


class VerifyChecklistRequest(BaseModel):
    campaign_input: CampaignInputDTO = Field(description="Original campaign brief (BP-01 'Input').")
    campaign_output: CampaignOutputDTO = Field(description="Generated plan + assets to verify (BP-01 'Expected Output').")
    iteration: int = Field(default=1, ge=1, description="Which regeneration attempt this is (for logging/telemetry).")


class VerifyChecklistResponse(BaseModel):
    passed: bool = Field(description="True only when there are zero BLOCKER issues.")
    iteration: int
    issues: List[QAIssue] = Field(default_factory=list)
    regenerate: List[RegenerateTarget] = Field(
        default_factory=list,
        description=(
            "Deduplicated, ordered list of stages the frontend should call next "
            "(plan -> images -> video -> copy order). Empty when passed=True."
        ),
    )
