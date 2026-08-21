"""Schemas for POST /verify-checklist.

Mirrors the rule-based QA checklist in QA_checklist.py (the source of truth
for this feature — see QA_checklist/README.md) but runs against the real
CampaignInputDTO / CampaignOutputDTO contracts already shared with the
frontend (app/schemas/campaign_dto.py), instead of QA_checklist's own
standalone CampaignInput/CampaignPlan/AssetBundle models.

`regenerate` tells the frontend which side of the pipeline to re-run to fix
the detected issues, so it doesn't have to re-run the whole pipeline on
every QA failure:
  - "plan"  -> re-run positioning/creative-routes/AB-test-plan generation
  - "asset" -> re-run image, video, or commerce-copy generation
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
    """Which side of the pipeline the frontend should re-run to fix an issue."""
    PLAN = "plan"
    ASSET = "asset"


class QAIssue(BaseModel):
    rule_id: str
    severity: QASeverity
    message: str
    field: str
    regenerate: RegenerateTarget = Field(
        description="Which side produced the offending content and should be regenerated."
    )


class QACheckedItem(BaseModel):
    """One generated checklist item and its pass/fail outcome, so the
    frontend can render a full tick-list (not just the failures)."""
    rule_id: str
    description: str
    passed: bool
    category: RegenerateTarget


class VerifyChecklistRequest(BaseModel):
    campaign_input: CampaignInputDTO = Field(description="Original campaign brief (BP-01 'Input').")
    campaign_output: CampaignOutputDTO = Field(description="Generated plan + assets to verify (BP-01 'Expected Output').")
    iteration: int = Field(default=1, ge=1, description="Which regeneration attempt this is (for logging/telemetry).")


class VerifyChecklistResponse(BaseModel):
    passed: bool = Field(description="True only when there are zero BLOCKER issues.")
    iteration: int
    issues: List[QAIssue] = Field(default_factory=list)
    checked_items: List[QACheckedItem] = Field(
        default_factory=list,
        description="Every generated checklist item with its pass/fail outcome, for rendering a full tick-list.",
    )
    regenerate: List[RegenerateTarget] = Field(
        default_factory=list,
        description=(
            "Deduplicated, ordered list of sides the frontend should call next "
            "(plan -> asset order). Empty when passed=True."
        ),
    )
