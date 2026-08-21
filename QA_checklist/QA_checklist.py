"""
QA_checklist.py — BP-01 Commerce Campaign Launch Copilot: standalone QA compliance module.

This module owns ONLY the QA/review step. It does not generate a campaign
plan or asset bundle itself — gen_plan and gen_assets are separate agents
(see backend/app/services/campaign/ for the real implementations). Given a
CampaignInput + an already-produced CampaignPlan + AssetBundle, this module:

  1. Data contracts   (CampaignInput, CampaignPlan, AssetBundle, QAResult, ...)
  2. Prompts           (LLM prompts for the QA checklist + per-item review)
  3. QA agents         ChecklistAgent (derives criteria) + ChecklistReviewAgent
                       (judges plan+assets against each criterion) + review()
  4. CLI entry point   run this file directly for a standalone QA-only smoke
                       test against sample data in testcases/<name>/

For now, "sample data in" means: testcases/<name>/user_input.json (the
CampaignInput) plus testcases/<name>/planning_output.json (the CampaignPlan)
and testcases/<name>/assets_model_output.json (the AssetBundle) — the same
reference fixtures already committed per testcase. assets_model_output.json
has a top-level {"happy_case": {...}, "unhappy_case": {...}} shape; pick
which one to load with --case happy|unhappy (default: happy).

This module is fully self-contained in the QA_checklist/ folder — it does
not import from, or depend on, backend/ or frontend/. Run it from anywhere;
paths below are always resolved relative to this file's own location.

Usage:
    python QA_checklist.py                          # default testcase, happy_case assets
    python QA_checklist.py --testcase <name>        # run a specific testcase folder
    python QA_checklist.py --case unhappy           # load the unhappy_case assets fixture instead
    python QA_checklist.py --plan p.json --assets a.json --input i.json
                                                     # bypass testcases/ entirely with explicit paths

Folder layout (all inside QA_checklist/, next to this file):
    testcases/
        <testcase_name>/
            user_input.json           - CampaignInput sample (BP-01 "Input" section).
            planning_output.json      - CampaignPlan sample fed into the QA step.
            assets_model_output.json  - AssetBundle sample(s) fed into the QA step,
                                         shaped as {"happy_case": {...}, "unhappy_case": {...}}.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent
TESTCASES_DIR = REPO_ROOT / "testcases"
DEFAULT_TESTCASE = "bp01_fnb_sparkling_tea"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ===========================================================================
# 1. DATA CONTRACTS
# ===========================================================================
# Mirror the "Expected Output" section of BP01-prob.txt:
#   1. Product Positioning        4. Product Collection Image Set
#   2. Creative Routes (A/B)      5. Commerce Copy
#   3. Short-form Video Asset     6. A/B Testing Plan   7. (Optional) Performance Learning

class _CamelModel(BaseModel):
    """Base for input models: accepts/emits the camelCase field names used by
    frontend/src/types/campaign_dto.ts's CampaignInputDTO, while still letting
    Python code read/write the same attributes as ordinary snake_case-free
    Python identifiers (Pydantic v2 populates by field name OR alias)."""

    model_config = {"populate_by_name": True}


class PriceOrPromotion(_CamelModel):
    price: Optional[float] = None
    currency: str = "VND"
    promotion: Optional[str] = None


class ProductBrief(_CamelModel):
    productName: str
    category: str
    keySellingPoints: list[str] = Field(default_factory=list)
    priceOrPromotion: PriceOrPromotion = Field(default_factory=PriceOrPromotion)
    targetMarket: str
    requiredClaims: list[str] = Field(default_factory=list)
    restrictedOrForbiddenClaims: list[str] = Field(default_factory=list)


class Logo(_CamelModel):
    path: Optional[str] = None


class BrandColors(_CamelModel):
    primary: Optional[str] = None
    secondary: Optional[str] = None
    accent: list[str] = Field(default_factory=list)
    palette: list[str] = Field(default_factory=list)


class ToneOfVoice(_CamelModel):
    description: str = ""
    attributes: list[str] = Field(default_factory=list)
    do: list[str] = Field(default_factory=list)
    dont: list[str] = Field(default_factory=list)


class BrandKit(_CamelModel):
    logo: Logo = Field(default_factory=Logo)
    brandColors: BrandColors = Field(default_factory=BrandColors)
    toneOfVoice: ToneOfVoice = Field(default_factory=ToneOfVoice)
    productPhotos: list[str] = Field(default_factory=list)
    existingProductVisuals: list[str] = Field(default_factory=list)


class AudienceBrief(_CamelModel):
    targetCustomer: str
    language: str
    platform: str
    market: str


class MarketSignal(_CamelModel):
    trend: Optional[str] = None
    seasonalMoment: Optional[str] = None
    consumerPainPoint: Optional[str] = None
    searchKeyword: list[str] = Field(default_factory=list)
    competitorAngle: Optional[str] = None
    campaignObjective: str = ""


class WatchTime(_CamelModel):
    value: Optional[float] = None
    unit: str = "sec"


class SalesResults(_CamelModel):
    unitsSold: Optional[int] = None
    revenue: Optional[float] = None
    currency: str = "VND"


class PastCampaignData(_CamelModel):
    enabled: bool = False
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    roas: Optional[float] = None
    watchTime: WatchTime = Field(default_factory=WatchTime)
    addToCartRate: Optional[float] = None
    comments: list[str] = Field(default_factory=list)
    salesResults: SalesResults = Field(default_factory=SalesResults)


class CampaignInput(_CamelModel):
    # campaign_id is NOT part of frontend's CampaignInputDTO (it has no
    # concept of a campaign id at input time) — QA_checklist assigns one
    # internally (see main()) purely for output file naming / traceability,
    # defaulted here so existing callers that don't set it explicitly still
    # work.
    campaignId: str = "campaign"
    productBrief: ProductBrief
    brandKit: BrandKit
    audienceBrief: AudienceBrief
    marketSignal: MarketSignal
    pastCampaignData: PastCampaignData = Field(default_factory=PastCampaignData)


class CreativeRoute(BaseModel):
    route_id: str  # "A" / "B" / ...
    hook_idea: str
    visual_direction: str
    message_angle: str
    suggested_platform_usage: list[str] = Field(default_factory=list)


class ProductPositioning(BaseModel):
    main_campaign_angle: str
    target_audience: str
    key_selling_message: str
    product_benefit_hierarchy: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)  # market research citations


class ABTestPlan(BaseModel):
    what_to_test: str
    route_a: str
    route_b: str
    success_metrics: list[str] = Field(default_factory=list)
    expected_learning: str


class PerformanceLearning(BaseModel):
    keep: list[str] = Field(default_factory=list)
    change: list[str] = Field(default_factory=list)
    stop: list[str] = Field(default_factory=list)
    test_next: list[str] = Field(default_factory=list)


class CampaignPlan(BaseModel):
    campaign_id: str
    positioning: ProductPositioning
    creative_routes: list[CreativeRoute]
    ab_test_plan: ABTestPlan
    performance_learning: Optional[PerformanceLearning] = None
    generated_at: datetime = Field(default_factory=_utcnow)


class ImageKind(str, Enum):
    HERO = "product_hero_image"
    SKU_DETAIL = "sku_detail_image"
    COLLECTION = "campaign_collection_image"
    THUMBNAIL = "marketplace_thumbnail"
    BANNER = "promotion_banner"
    BUNDLE = "bundle_image"
    SEASONAL = "seasonal_sale_image"


# The 4 image kinds BP-01's "Expected Output" requires on every campaign
# (ASSETS.IMAGE_COUNT / ASSETS.MISSING_IMAGE_KIND checklist criteria would
# reference these).
REQUIRED_IMAGE_KINDS: list["ImageKind"] = [
    ImageKind.HERO, ImageKind.SKU_DETAIL, ImageKind.COLLECTION, ImageKind.THUMBNAIL,
]


class ImageAsset(BaseModel):
    kind: ImageKind
    url: str
    width: int
    height: int
    model: str = "dola-seedream-5-0-pro-260628"


class VideoAsset(BaseModel):
    url: str
    duration_sec: float
    resolution: str  # e.g. "720p"
    aspect_ratio: str  # e.g. "9:16"
    model: str = "dreamina-seedance-2-5-260628"
    route_id: Optional[str] = None


class CommerceCopy(BaseModel):
    product_title: str
    product_description: str
    listing_bullet_points: list[str] = Field(default_factory=list)
    ad_caption: str
    promotion_copy: Optional[str] = None
    short_hook_lines: list[str] = Field(default_factory=list)


class AssetBundle(BaseModel):
    campaign_id: str
    images: list[ImageAsset]
    videos: list[VideoAsset]
    listing_copy: CommerceCopy
    generated_at: datetime = Field(default_factory=_utcnow)


class ChecklistItemResult(BaseModel):
    """One checklist criterion + the review agent's verdict on it.

    `verdict` is the raw string returned by ChecklistReviewAgent: literally
    "Pass" on success, or a human-readable failure reason (e.g. "The color
    is not match with user description") on failure. No severity/blocker
    distinction — every failed item blocks QA, mirroring "lam cho den khi
    dat cac tieu chi, va khong co van de phat hien."
    """
    criterion: str
    verdict: str

    @property
    def passed(self) -> bool:
        return self.verdict.strip().lower() == "pass"


class QAResult(BaseModel):
    campaign_id: str
    passed: bool
    iteration: int
    issues: list[str] = Field(default_factory=list)  # failure-reason strings only (Pass items excluded)
    checklist_results: list[ChecklistItemResult] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=_utcnow)


# ===========================================================================
# 2. PROMPTS (QA-only)
# ===========================================================================
# This module only reasons about QA: deriving a checklist from a
# CampaignInput, and judging a checklist item against an already-produced
# CampaignPlan + AssetBundle. It does not generate plans/assets/copy/images/
# video itself — those are produced by separate gen_plan / gen_assets agents
# elsewhere and handed to this module (or, for standalone runs, loaded from
# each testcase's planning_output.json / assets_model_output.json).

# --- QA checklist agent prompts -------------------------------------------
# ChecklistAgent: reads the raw CampaignInput and produces a short list of
# concrete, checkable QA criteria (max 7) tailored to that specific brief —
# e.g. "The product image colors must match brand_kit.brandColors",
# "The copy must not contain the forbidden claim 'cures bloating'".
CHECKLIST_SYSTEM_PROMPT = (
    "Ban la mot QA lead cho e-commerce marketing. Luon tra ve JSON hop le."
)

CHECKLIST_PROMPT_TEMPLATE = """Dua vao thong tin dau vao (input) cua mot campaign thuong mai dien tu duoi day,
hay lap mot checklist QA gom TOI DA 7 va TOI THIEU 3 tieu chi cu the, co the kiem tra duoc,
de danh gia xem ban ke hoach campaign (plan) va bo tai san (assets: hinh anh, video, copy)
duoc sinh ra co dap ung dung brief nay khong.

Moi tieu chi phai:
- La mot cau khang dinh ro rang, co the kiem tra Pass/Fail (vi du: "Anh san pham phai dung
  bang mau brand_colors trong brand_kit", "Copy phai chua claim bat buoc 'made in Vietnam'",
  "Copy khong duoc chua claim cam 'cures bloating'", "Video phai co ti le khung hinh 9:16").
- Bam sat cac field cu the trong input (product_brief, brand_kit, audience_brief, market_signal).
- Khong trung lap y nghia voi tieu chi khac trong danh sach.

Tra ve DUY NHAT mot JSON object hop le voi key chinh xac sau (khong markdown, khong giai thich them):

{{
  "checklist": ["<tieu chi 1>", "<tieu chi 2>", "..."]
}}

Campaign input:
{campaign_input_json}
"""

# ChecklistReviewAgent: reviews ONE checklist criterion against the actual
# generated CampaignPlan + AssetBundle (+ original CampaignInput for
# grounding) and returns a plain string verdict: "Pass" or a short failure
# reason.
REVIEW_SYSTEM_PROMPT = (
    "Ban la QA reviewer nghiem khac cho e-commerce marketing. Luon tra ve dung mot dong text, "
    "khong markdown, khong giai thich dai dong."
)

REVIEW_PROMPT_TEMPLATE = """Tieu chi QA can kiem tra:
"{criterion}"

Du lieu campaign input (brief goc cua khach hang):
{campaign_input_json}

Ke hoach campaign da duoc sinh ra (plan):
{plan_json}

Bo tai san da duoc sinh ra (assets: hinh anh, video, copy):
{assets_json}

Hay danh gia xem ke hoach + tai san co dap ung tieu chi tren khong.
- Neu DAP UNG, tra ve DUY NHAT chu "Pass" (khong dau cau, khong giai thich them).
- Neu KHONG DAP UNG, tra ve DUY NHAT mot cau ngan gon giai thich ly do fail
  (vi du: "The color is not match with user description"). Khong tra ve JSON,
  khong markdown, chi mot dong text duy nhat.
"""


MAX_CHECKLIST_ITEMS = 7


# ===========================================================================
# 3. QA AGENTS — the main deliverable. Given campaign_input + an already-
# produced plan + assets (from gen_plan / gen_assets, wherever those run),
# derive a checklist and judge the plan+assets against it.
# ===========================================================================

class ChecklistAgent:
    """Reads the raw CampaignInput and produces a short, concrete QA
    checklist (3-7 plain-string criteria) tailored to that specific brief.
    Always calls Seed 2.1 via byteplus_ark.chat — no rule-based fallback,
    since the checklist must be reasoned from the actual brief content
    (colors, claims, audience, platform, etc.), not hardcoded structural
    rules."""

    def generate(self, campaign_input: CampaignInput) -> list[str]:
        ark = _load_ark_client()
        prompt = CHECKLIST_PROMPT_TEMPLATE.format(
            campaign_input_json=campaign_input.model_dump_json(indent=2)
        )
        raw = ark.chat(prompt, system=CHECKLIST_SYSTEM_PROMPT)
        data = _parse_llm_json(raw)
        checklist = [str(item).strip() for item in data.get("checklist", []) if str(item).strip()]
        if not checklist:
            raise RuntimeError(f"ChecklistAgent returned an empty checklist. Raw output:\n{raw}")
        return checklist[:MAX_CHECKLIST_ITEMS]


class ChecklistReviewAgent:
    """Reviews ONE checklist criterion against an already-produced
    CampaignPlan + AssetBundle (grounded by the original CampaignInput) and
    returns a plain string verdict: "Pass" or a short failure reason."""

    def review_item(
        self,
        criterion: str,
        campaign_input: CampaignInput,
        plan: CampaignPlan,
        assets: AssetBundle,
    ) -> str:
        ark = _load_ark_client()
        prompt = REVIEW_PROMPT_TEMPLATE.format(
            criterion=criterion,
            campaign_input_json=campaign_input.model_dump_json(indent=2),
            plan_json=plan.model_dump_json(indent=2),
            assets_json=assets.model_dump_json(indent=2),
        )
        raw = ark.chat(prompt, system=REVIEW_SYSTEM_PROMPT)
        return raw.strip().strip('"')


def review(
    campaign_input: CampaignInput,
    plan: CampaignPlan,
    assets: AssetBundle,
    iteration: int = 1,
    checklist_agent: Optional[ChecklistAgent] = None,
    review_agent: Optional[ChecklistReviewAgent] = None,
) -> QAResult:
    """Runs the full checklist-based QA review for one campaign, against an
    already-produced plan + asset bundle (this module never generates them):
      1. ChecklistAgent derives 3-7 concrete criteria from campaign_input.
      2. ChecklistReviewAgent judges each criterion against plan + assets,
         in parallel, each returning "Pass" or a plain failure-reason string.
    passed=True only when every criterion verdict is exactly "Pass".
    """
    checklist_agent = checklist_agent or ChecklistAgent()
    review_agent = review_agent or ChecklistReviewAgent()

    checklist = checklist_agent.generate(campaign_input)

    results: list[ChecklistItemResult] = [None] * len(checklist)  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=len(checklist)) as executor:
        future_to_idx = {
            executor.submit(review_agent.review_item, criterion, campaign_input, plan, assets): idx
            for idx, criterion in enumerate(checklist)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            criterion = checklist[idx]
            verdict = future.result()
            results[idx] = ChecklistItemResult(criterion=criterion, verdict=verdict)

    issues = [f"{r.criterion} -> {r.verdict}" for r in results if not r.passed]
    passed = len(issues) == 0

    return QAResult(
        campaign_id=campaign_input.campaignId,
        passed=passed,
        iteration=iteration,
        issues=issues,
        checklist_results=results,
    )


# ===========================================================================
# Helpers: I/O, byteplus_ark.py bridge, LLM JSON parsing
# ===========================================================================

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_ark_client():
    """Import byteplus_ark.py (repo root) lazily, only when review() is
    actually called, so simply importing this module never requires
    ARK_API_KEY or the `requests` package."""
    sys.path.insert(0, str(REPO_ROOT))
    import byteplus_ark  # type: ignore
    return byteplus_ark


def _parse_llm_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM did not return valid JSON. Raw output:\n{raw}") from exc


# ===========================================================================
# 4. CLI entry point
# ===========================================================================

def _print_section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--testcase", default=DEFAULT_TESTCASE,
        help=f"Name of a folder under testcases/ to run (default: {DEFAULT_TESTCASE}). "
             "Reads testcases/<name>/user_input.json, planning_output.json, and "
             "assets_model_output.json as sample input for the standalone QA step.",
    )
    parser.add_argument(
        "--case", choices=["happy", "unhappy"], default="happy",
        help="Which fixture to load from assets_model_output.json's "
             "{happy_case, unhappy_case} shape (default: happy).",
    )
    parser.add_argument(
        "--input", type=Path, default=None,
        help="Override: path to a CampaignInput JSON file, instead of "
             "testcases/<testcase>/user_input.json.",
    )
    parser.add_argument(
        "--plan", type=Path, default=None,
        help="Override: path to a CampaignPlan JSON file, instead of "
             "testcases/<testcase>/planning_output.json.",
    )
    parser.add_argument(
        "--assets", type=Path, default=None,
        help="Override: path to an AssetBundle JSON file, instead of "
             "testcases/<testcase>/assets_model_output.json. If the loaded JSON "
             "has a top-level {happy_case, unhappy_case} shape, --case selects "
             "which one to use; otherwise the JSON is used as-is.",
    )
    args = parser.parse_args()

    testcase_dir = TESTCASES_DIR / args.testcase
    input_path = args.input or (testcase_dir / "user_input.json")
    plan_path = args.plan or (testcase_dir / "planning_output.json")
    assets_path = args.assets or (testcase_dir / "assets_model_output.json")

    for label, path in (("input", input_path), ("plan", plan_path), ("assets", assets_path)):
        if not path.exists():
            raise SystemExit(f"Sample {label} file not found: {path}")

    input_data = _load_json(input_path)
    # campaign_id is not part of frontend's CampaignInputDTO (it has no notion
    # of a campaign id at input time) — QA_checklist assigns one here, purely
    # for traceability, unless the input JSON explicitly sets "campaignId".
    input_data.setdefault("campaignId", args.testcase)
    campaign_input = CampaignInput.model_validate(input_data)

    plan_data = _load_json(plan_path)
    plan_data.pop("$note", None)
    plan = CampaignPlan.model_validate(plan_data)

    assets_data = _load_json(assets_path)
    assets_data.pop("$note", None)
    if "happy_case" in assets_data or "unhappy_case" in assets_data:
        case_key = f"{args.case}_case"
        if case_key not in assets_data:
            raise SystemExit(f"'{case_key}' not found in {assets_path}")
        assets_data = assets_data[case_key]
    assets_data.pop("$drift_notes", None)
    assets = AssetBundle.model_validate(assets_data)

    _print_section("1. CAMPAIGN INPUT (sample)")
    print(campaign_input.model_dump_json(indent=2))

    _print_section("2. CAMPAIGN PLAN (sample)")
    print(plan.model_dump_json(indent=2))

    _print_section(f"3. ASSET BUNDLE (sample, case={args.case})")
    print(assets.model_dump_json(indent=2))

    result = review(campaign_input, plan, assets)

    _print_section("4. QA RESULT")
    print(f"campaign_id : {result.campaign_id}")
    print(f"passed      : {result.passed}")
    print(f"iteration   : {result.iteration}")
    print(f"checked_at  : {result.checked_at}")

    print(f"\nChecklist ({len(result.checklist_results)} item(s)):")
    for item in result.checklist_results:
        mark = "PASS" if item.passed else "FAIL"
        print(f"  [{mark}] {item.criterion}")
        if not item.passed:
            print(f"         -> {item.verdict}")

    _print_section("SUMMARY")
    failed = [r for r in result.checklist_results if not r.passed]
    print(f"Result  : {'PASS' if result.passed else 'FAIL'}")
    print(f"Checked : {len(result.checklist_results)}")
    print(f"Failed  : {len(failed)}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
