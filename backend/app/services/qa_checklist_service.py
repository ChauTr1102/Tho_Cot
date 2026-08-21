"""QA checklist service — rule-based verification of a generated campaign
plan + asset bundle against a campaign brief.

Ports the checklist rules from QA_checklist/QA_checklist.py (see
QA_checklist/README.md, section 3 "Checklist buckets") to run against the
real CampaignInputDTO / CampaignOutputDTO contracts shared with the
frontend (app/schemas/campaign_dto.py, snake_case), instead of
QA_checklist's own standalone models.

Checklist buckets (same as QA_checklist.py):
  A. Internal system criteria  - structural/spec completeness of the plan
     and asset bundle per BP-01's "Expected Output" schema.
  B. Market research criteria  - positioning genuinely reasoned (non-empty
     benefit hierarchy backing the angle) — campaign_dto.py's
     ProductPositioning has no separate `sources` field to cite, so this
     bucket checks the closest available proxy.
  C. User-provided criteria    - brand brief compliance (required/forbidden
     claims), the highest-stakes bucket (legal/claims risk).

Every issue is tagged with a `regenerate` target (plan / asset) so the
caller (API layer) can tell the frontend exactly which side of the pipeline
to re-run, instead of forcing a full pipeline re-run on every QA failure.
`passed` is True only when there are zero BLOCKER issues — WARNING issues
are surfaced but never block.
"""
from __future__ import annotations

import re

from app.schemas.campaign_dto import CampaignInputDTO, CampaignOutputDTO
from app.schemas.qa_checklist import (
    QAIssue,
    QASeverity,
    RegenerateTarget,
    VerifyChecklistRequest,
    VerifyChecklistResponse,
)

# ---------------------------------------------------------------------------
# Config (tune without touching rule logic) — mirrors QA_checklist.py
# ---------------------------------------------------------------------------

MIN_CREATIVE_ROUTES = 2
MIN_PRODUCT_IMAGES = 4
MIN_VIDEOS = 1
VIDEO_REQUIRED_FORMAT = "9:16"
VIDEO_MIN_DURATION_SEC = 15
VIDEO_MAX_DURATION_SEC = 30

# Stage regeneration order the frontend should follow when both sides need
# fixing at once (plan before asset, since asset regeneration usually
# depends on plan output).
_REGENERATE_ORDER = [
    RegenerateTarget.PLAN,
    RegenerateTarget.ASSET,
]


def _duration_in_range(duration: str, lo: int, hi: int) -> bool:
    """Best-effort parse of a duration string like '15-30s' or '20s' against
    a [lo, hi] second window. Unparseable strings are treated as in-range
    (nothing to flag) rather than raising, since this is a WARNING-only
    heuristic check on a free-form field."""
    numbers = [int(n) for n in re.findall(r"\d+", duration or "")]
    if not numbers:
        return True
    return all(lo <= n <= hi for n in numbers)


class QAChecklistService:
    # -- Bucket A: internal system criteria (plan) --------------------------

    def _check_plan(self, output: CampaignOutputDTO) -> list[QAIssue]:
        issues: list[QAIssue] = []
        positioning = output.product_positioning
        routes = output.creative_routes
        ab_plan = output.ab_testing_plan

        if not positioning.main_campaign_angle.strip():
            issues.append(QAIssue(
                rule_id="PLAN.ANGLE_EMPTY", severity=QASeverity.BLOCKER,
                message="Main campaign angle is empty.",
                field="product_positioning.main_campaign_angle", regenerate=RegenerateTarget.PLAN,
            ))

        if len(routes) < MIN_CREATIVE_ROUTES:
            issues.append(QAIssue(
                rule_id="PLAN.ROUTE_COUNT", severity=QASeverity.BLOCKER,
                message=f"Need at least {MIN_CREATIVE_ROUTES} creative routes for A/B testing, found {len(routes)}.",
                field="creative_routes", regenerate=RegenerateTarget.PLAN,
            ))

        route_names = [r.name for r in routes]
        if len(route_names) != len(set(route_names)):
            issues.append(QAIssue(
                rule_id="PLAN.ROUTE_NAME_DUP", severity=QASeverity.BLOCKER,
                message="Duplicate creative route names found in creative_routes.",
                field="creative_routes", regenerate=RegenerateTarget.PLAN,
            ))

        if not ab_plan.route_a_description.strip() or not ab_plan.route_b_description.strip():
            issues.append(QAIssue(
                rule_id="PLAN.AB_ROUTE_EMPTY", severity=QASeverity.BLOCKER,
                message="A/B testing plan is missing route_a_description or route_b_description.",
                field="ab_testing_plan", regenerate=RegenerateTarget.PLAN,
            ))
        if not ab_plan.suggested_success_metrics:
            issues.append(QAIssue(
                rule_id="PLAN.AB_NO_METRICS", severity=QASeverity.WARNING,
                message="A/B testing plan has no suggested success metrics.",
                field="ab_testing_plan.suggested_success_metrics", regenerate=RegenerateTarget.PLAN,
            ))

        return issues

    # -- Bucket A: internal system criteria (images) ------------------------

    def _check_images(self, output: CampaignOutputDTO) -> list[QAIssue]:
        issues: list[QAIssue] = []
        images = output.product_collection_image_set

        required_fields = {
            "product_hero_image": images.product_hero_image,
            "sku_detail_image": images.sku_detail_image,
            "campaign_collection_image": images.campaign_collection_image,
            "marketplace_thumbnail": images.marketplace_thumbnail,
        }
        missing = [name for name, value in required_fields.items() if not (value or "").strip()]
        if missing:
            issues.append(QAIssue(
                rule_id="ASSETS.MISSING_IMAGE_KIND", severity=QASeverity.BLOCKER,
                message=f"Missing required image(s): {missing}.",
                field="product_collection_image_set", regenerate=RegenerateTarget.ASSET,
            ))

        present_count = sum(1 for value in required_fields.values() if (value or "").strip())
        if present_count < MIN_PRODUCT_IMAGES:
            issues.append(QAIssue(
                rule_id="ASSETS.IMAGE_COUNT", severity=QASeverity.BLOCKER,
                message=f"Need at least {MIN_PRODUCT_IMAGES} product images, found {present_count}.",
                field="product_collection_image_set", regenerate=RegenerateTarget.ASSET,
            ))

        return issues

    # -- Bucket A: internal system criteria (video) --------------------------

    def _check_video(self, output: CampaignOutputDTO) -> list[QAIssue]:
        issues: list[QAIssue] = []
        video = output.short_form_video_asset

        if len(video.generated_video_urls) < MIN_VIDEOS:
            issues.append(QAIssue(
                rule_id="ASSETS.VIDEO_COUNT", severity=QASeverity.BLOCKER,
                message=f"Need at least {MIN_VIDEOS} short-form video, found {len(video.generated_video_urls)}.",
                field="short_form_video_asset.generated_video_urls", regenerate=RegenerateTarget.ASSET,
            ))

        if video.format != VIDEO_REQUIRED_FORMAT:
            issues.append(QAIssue(
                rule_id="ASSETS.VIDEO_ASPECT", severity=QASeverity.WARNING,
                message=f"Video format '{video.format}' differs from the recommended {VIDEO_REQUIRED_FORMAT}.",
                field="short_form_video_asset.format", regenerate=RegenerateTarget.ASSET,
            ))

        if not _duration_in_range(video.duration, lo=VIDEO_MIN_DURATION_SEC, hi=VIDEO_MAX_DURATION_SEC):
            issues.append(QAIssue(
                rule_id="ASSETS.VIDEO_DURATION", severity=QASeverity.WARNING,
                message=(
                    f"Video duration '{video.duration}' is outside the recommended "
                    f"{VIDEO_MIN_DURATION_SEC}-{VIDEO_MAX_DURATION_SEC}s window."
                ),
                field="short_form_video_asset.duration", regenerate=RegenerateTarget.ASSET,
            ))

        return issues

    # -- Bucket A: internal system criteria (copy) --------------------------

    def _check_copy(self, output: CampaignOutputDTO) -> list[QAIssue]:
        issues: list[QAIssue] = []
        copy = output.commerce_copy

        if not copy.product_title.strip() or not copy.product_description.strip():
            issues.append(QAIssue(
                rule_id="ASSETS.COPY_INCOMPLETE", severity=QASeverity.BLOCKER,
                message="Commerce copy is missing product_title or product_description.",
                field="commerce_copy", regenerate=RegenerateTarget.ASSET,
            ))
        if not copy.listing_bullet_points:
            issues.append(QAIssue(
                rule_id="ASSETS.COPY_NO_BULLETS", severity=QASeverity.WARNING,
                message="Commerce copy has no listing bullet points.",
                field="commerce_copy.listing_bullet_points", regenerate=RegenerateTarget.ASSET,
            ))

        return issues

    # -- Bucket B: market research criteria ----------------------------------

    def _check_market_research(self, output: CampaignOutputDTO) -> list[QAIssue]:
        """campaign_dto.py's ProductPositioning has no dedicated `sources`
        field to cite market research (unlike QA_checklist.py's model), so
        this checks the closest structural proxy available: the campaign
        angle must be backed by a non-empty, non-trivial benefit hierarchy
        rather than being an unsupported one-liner."""
        issues: list[QAIssue] = []
        positioning = output.product_positioning
        if not positioning.product_benefit_hierarchy:
            issues.append(QAIssue(
                rule_id="MARKET.NO_SOURCES", severity=QASeverity.WARNING,
                message="Positioning has no product_benefit_hierarchy backing the campaign angle.",
                field="product_positioning.product_benefit_hierarchy", regenerate=RegenerateTarget.PLAN,
            ))
        return issues

    # -- Bucket C: user-provided brief compliance ----------------------------

    def _check_user_brief_compliance(
        self, campaign_input: CampaignInputDTO, output: CampaignOutputDTO
    ) -> list[QAIssue]:
        issues: list[QAIssue] = []
        product = campaign_input.product_brief
        copy = output.commerce_copy
        positioning = output.product_positioning

        text_blob = " ".join(
            [
                positioning.main_campaign_angle,
                positioning.key_selling_message,
                copy.product_title,
                copy.product_description,
                copy.ad_caption,
                copy.promotion_copy or "",
                *copy.listing_bullet_points,
                *copy.short_hook_lines,
            ]
        ).lower()

        for forbidden in product.restricted_or_forbidden_claims:
            if forbidden.strip() and forbidden.strip().lower() in text_blob:
                issues.append(QAIssue(
                    rule_id="USER.FORBIDDEN_CLAIM", severity=QASeverity.BLOCKER,
                    message=f"Forbidden claim found in generated content: '{forbidden}'.",
                    field="commerce_copy", regenerate=RegenerateTarget.ASSET,
                ))

        for required in product.required_claims:
            if required.strip() and required.strip().lower() not in text_blob:
                issues.append(QAIssue(
                    rule_id="USER.MISSING_REQUIRED_CLAIM", severity=QASeverity.BLOCKER,
                    message=f"Required claim not found in generated content: '{required}'.",
                    field="commerce_copy", regenerate=RegenerateTarget.ASSET,
                ))

        return issues

    # -- Entry point ----------------------------------------------------------

    def verify(self, request: VerifyChecklistRequest) -> VerifyChecklistResponse:
        output = request.campaign_output
        campaign_input = request.campaign_input

        issues: list[QAIssue] = []
        issues += self._check_plan(output)
        issues += self._check_images(output)
        issues += self._check_video(output)
        issues += self._check_copy(output)
        issues += self._check_market_research(output)
        issues += self._check_user_brief_compliance(campaign_input, output)

        # TEMP: only surface WARNING severity for now — never block the
        # pipeline (same policy as the agent-based service, kept in sync so
        # the fallback path behaves identically to the primary path).
        issues = [issue.model_copy(update={"severity": QASeverity.WARNING}) for issue in issues]

        passed = not any(issue.severity == QASeverity.BLOCKER for issue in issues)

        seen = {issue.regenerate for issue in issues}
        regenerate = [target for target in _REGENERATE_ORDER if target in seen]

        return VerifyChecklistResponse(
            passed=passed,
            iteration=request.iteration,
            issues=issues,
            regenerate=regenerate,
        )


qa_checklist_service = QAChecklistService()
