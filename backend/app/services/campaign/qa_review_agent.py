"""
QA review agent — main focus of this project.

Takes the outputs of gen_plan (CampaignPlan) and gen_assets (AssetBundle),
runs them through a rule checklist, and returns a QAResult (pass/fail +
list of issues). Designed to be called in a loop by the orchestrator:
gen -> QA -> (if fail) regenerate -> QA -> ... until pass or max
iterations, per draft_idea.txt.

Checklist is grouped into 3 buckets, mirroring draft_idea.txt:
  1. Internal system criteria   (_check_internal_*)   - schema/spec completeness
  2. Market research criteria   (_check_market_*)     - claims backed by sources
  3. User-provided criteria     (_check_user_*)       - brand kit / brief compliance

Each rule appends QAIssue(s) with a severity. QA passes only when there
are zero BLOCKER issues.
"""
from __future__ import annotations

from app.schemas.campaign import (
    AssetBundle,
    CampaignInput,
    CampaignPlan,
    ImageKind,
    QAIssue,
    QAResult,
    QASeverity,
)

# ---------------------------------------------------------------------------
# Config (tune without touching rule logic)
# ---------------------------------------------------------------------------

MIN_CREATIVE_ROUTES = 2
MIN_PRODUCT_IMAGES = 4
REQUIRED_IMAGE_KINDS = {
    ImageKind.HERO,
    ImageKind.SKU_DETAIL,
    ImageKind.COLLECTION,
    ImageKind.THUMBNAIL,
}
MIN_VIDEOS = 1
VIDEO_MIN_DURATION_SEC = 15
VIDEO_MAX_DURATION_SEC = 30
VIDEO_REQUIRED_ASPECT = "9:16"
MAX_ITERATIONS = 3


# ---------------------------------------------------------------------------
# Rule groups
# ---------------------------------------------------------------------------

def _check_internal_plan(plan: CampaignPlan) -> list[QAIssue]:
    """Internal system criteria: is the plan structurally complete per BP-01 spec."""
    issues: list[QAIssue] = []

    if not plan.positioning.main_campaign_angle.strip():
        issues.append(QAIssue(
            rule_id="PLAN.ANGLE_EMPTY", severity=QASeverity.BLOCKER,
            message="Góc chiến dịch chính đang để trống.", field="positioning.main_campaign_angle",
        ))

    if len(plan.creative_routes) < MIN_CREATIVE_ROUTES:
        issues.append(QAIssue(
            rule_id="PLAN.ROUTE_COUNT", severity=QASeverity.BLOCKER,
            message=f"Cần ít nhất {MIN_CREATIVE_ROUTES} hướng sáng tạo để thử nghiệm A/B, hiện có {len(plan.creative_routes)}.",
            field="creative_routes",
        ))

    route_ids = [r.route_id for r in plan.creative_routes]
    if len(route_ids) != len(set(route_ids)):
        issues.append(QAIssue(
            rule_id="PLAN.ROUTE_ID_DUP", severity=QASeverity.BLOCKER,
            message="Có giá trị route_id trùng lặp trong creative_routes.", field="creative_routes",
        ))

    ab = plan.ab_test_plan
    if ab.route_a not in route_ids or ab.route_b not in route_ids:
        issues.append(QAIssue(
            rule_id="PLAN.AB_ROUTE_MISMATCH", severity=QASeverity.BLOCKER,
            message="Kế hoạch thử nghiệm A/B tham chiếu route_id không tồn tại trong creative_routes.",
            field="ab_test_plan",
        ))
    if not ab.success_metrics:
        issues.append(QAIssue(
            rule_id="PLAN.AB_NO_METRICS", severity=QASeverity.WARNING,
            message="Kế hoạch thử nghiệm A/B chưa xác định chỉ số thành công.", field="ab_test_plan.success_metrics",
        ))

    return issues


def _check_internal_assets(assets: AssetBundle) -> list[QAIssue]:
    """Internal system criteria: asset bundle completeness per BP-01 spec."""
    issues: list[QAIssue] = []

    if len(assets.images) < MIN_PRODUCT_IMAGES:
        issues.append(QAIssue(
            rule_id="ASSETS.IMAGE_COUNT", severity=QASeverity.BLOCKER,
            message=f"Cần ít nhất {MIN_PRODUCT_IMAGES} ảnh sản phẩm, hiện có {len(assets.images)}.",
            field="images",
        ))

    present_kinds = {img.kind for img in assets.images}
    missing_kinds = REQUIRED_IMAGE_KINDS - present_kinds
    if missing_kinds:
        issues.append(QAIssue(
            rule_id="ASSETS.MISSING_IMAGE_KIND", severity=QASeverity.BLOCKER,
            message=f"Thiếu các loại ảnh bắt buộc: {sorted(k.value for k in missing_kinds)}.",
            field="images",
        ))

    if len(assets.videos) < MIN_VIDEOS:
        issues.append(QAIssue(
            rule_id="ASSETS.VIDEO_COUNT", severity=QASeverity.BLOCKER,
            message=f"Cần ít nhất {MIN_VIDEOS} video ngắn, hiện có {len(assets.videos)}.",
            field="videos",
        ))

    for v in assets.videos:
        if not (VIDEO_MIN_DURATION_SEC <= v.duration_sec <= VIDEO_MAX_DURATION_SEC):
            issues.append(QAIssue(
                rule_id="ASSETS.VIDEO_DURATION", severity=QASeverity.WARNING,
                message=f"Thời lượng video {v.duration_sec} giây nằm ngoài khoảng đề xuất {VIDEO_MIN_DURATION_SEC}-{VIDEO_MAX_DURATION_SEC} giây.",
                field="videos",
            ))
        if v.aspect_ratio != VIDEO_REQUIRED_ASPECT:
            issues.append(QAIssue(
                rule_id="ASSETS.VIDEO_ASPECT", severity=QASeverity.WARNING,
                message=f"Tỷ lệ khung hình {v.aspect_ratio} khác tỷ lệ đề xuất {VIDEO_REQUIRED_ASPECT}.",
                field="videos",
            ))

    copy = assets.listing_copy
    if not copy.product_title.strip() or not copy.product_description.strip():
        issues.append(QAIssue(
            rule_id="ASSETS.COPY_INCOMPLETE", severity=QASeverity.BLOCKER,
            message="Nội dung thương mại thiếu product_title hoặc product_description.", field="copy",
        ))
    if len(copy.listing_bullet_points) == 0:
        issues.append(QAIssue(
            rule_id="ASSETS.COPY_NO_BULLETS", severity=QASeverity.WARNING,
            message="Nội dung thương mại chưa có danh sách lợi ích nổi bật.", field="copy.listing_bullet_points",
        ))

    return issues


def _check_market_research(plan: CampaignPlan) -> list[QAIssue]:
    """Market research criteria: positioning claims must be backed by cited sources."""
    issues: list[QAIssue] = []

    if not plan.positioning.sources:
        issues.append(QAIssue(
            rule_id="MARKET.NO_SOURCES", severity=QASeverity.WARNING,
            message="Định vị chưa có nguồn nghiên cứu thị trường để chứng minh cho góc chiến dịch.",
            field="positioning.sources",
        ))

    return issues


def _check_user_brief_compliance(
    campaign_input: CampaignInput, plan: CampaignPlan, assets: AssetBundle
) -> list[QAIssue]:
    """User-provided criteria: required claims present, forbidden claims absent."""
    issues: list[QAIssue] = []
    product = campaign_input.product_brief

    text_blob = " ".join(
        [
            plan.positioning.main_campaign_angle,
            plan.positioning.key_selling_message,
            assets.listing_copy.product_title,
            assets.listing_copy.product_description,
            assets.listing_copy.ad_caption,
            *assets.listing_copy.listing_bullet_points,
            *assets.listing_copy.short_hook_lines,
        ]
    ).lower()

    for forbidden in product.forbidden_claims:
        if forbidden.strip() and forbidden.strip().lower() in text_blob:
            issues.append(QAIssue(
                rule_id="USER.FORBIDDEN_CLAIM", severity=QASeverity.BLOCKER,
                message=f"Phát hiện tuyên bố bị cấm trong nội dung tạo ra: '{forbidden}'.",
                field="copy",
            ))

    for required in product.required_claims:
        if required.strip() and required.strip().lower() not in text_blob:
            issues.append(QAIssue(
                rule_id="USER.MISSING_REQUIRED_CLAIM", severity=QASeverity.BLOCKER,
                message=f"Không tìm thấy tuyên bố bắt buộc trong nội dung tạo ra: '{required}'.",
                field="copy",
            ))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def review(
    campaign_input: CampaignInput,
    plan: CampaignPlan,
    assets: AssetBundle,
    iteration: int = 1,
) -> QAResult:
    """Run the full checklist against a plan + asset bundle for one campaign.

    Returns a QAResult with passed=True only if there are no BLOCKER issues.
    Caller (orchestrator) is responsible for looping: on failure, feed
    `issues` back to gen_plan/gen_assets for regeneration and re-review,
    up to MAX_ITERATIONS.
    """
    issues: list[QAIssue] = []
    issues += _check_internal_plan(plan)
    issues += _check_internal_assets(assets)
    issues += _check_market_research(plan)
    issues += _check_user_brief_compliance(campaign_input, plan, assets)

    passed = not any(i.severity == QASeverity.BLOCKER for i in issues)

    return QAResult(
        campaign_id=campaign_input.campaign_id,
        passed=passed,
        iteration=iteration,
        issues=issues,
    )
