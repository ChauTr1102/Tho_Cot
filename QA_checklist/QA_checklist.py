"""
QA_checklist.py — BP-01 Commerce Campaign Launch Copilot: single-file QA compliance module.

Everything needed to run and understand the QA step lives in this one file:
  1. Data contracts        (CampaignInput, CampaignPlan, AssetBundle, QAResult, ...)
  2. Prompts                (LLM prompts for positioning + commerce copy, image/video
                              prompt templates for Seedream 5.0 Pro / Seedance 2.5)
  3. Agent flow              gen_plan_agent -> gen_assets_agent -> qa_review_agent
  4. QA rules engine         (3 buckets: internal / market research / user brief)
  5. CLI entry point         run this file directly to execute the full pipeline
                              against testcases/<name>/user_input.json

IMPORTANT: each testcase's user_input.json is SAMPLE INPUT ONLY. The plan
and assets are always produced by running the actual agents (GenPlanAgent /
GenAssetsAgent) against that input — never read back from a pre-baked
"output" fixture. Any brand_kit logo/photo referenced by user_input.json
must be a real local file path (see testcases/<name>/brand_assets/),
generated via generate_testcase_assets.py + byteplus_ark.py — never a fake
remote URL.

  --live (this is the DEFAULT): agents call the real BytePlus ModelArk API
      (byteplus_ark.py) — Seed 2.1 for positioning/copy reasoning, Seedream
      5.0 Pro for images, Seedance 2.5 for video. Requires ARK_API_KEY.
  --mock: agents run a built-in rule-based generator instead (still driven
      by the actual CampaignInput fields — product name, claims, audience,
      market signal — not by loading a canned plan/asset JSON) and
      synthesize local placeholder image/video files instead of calling the
      paid API. Use this when you don't have/want to spend an API key.

This module is fully self-contained in the QA_checklist/ folder — it does
not import from, or depend on, backend/ or frontend/. Run it from anywhere;
paths below are always resolved relative to this file's own location.

Usage:
    python QA_checklist.py                          # DEFAULT: real API calls via byteplus_ark.py
                                                     # (--live), default testcase (bp01_fnb_sparkling_tea)
    python QA_checklist.py --testcase <name>        # run a specific testcase folder (still --live)
    python QA_checklist.py --mock                   # use built-in generator instead (no API key needed)
    python QA_checklist.py --mock --testcase <name> # combine: built-in generator, specific testcase
    python QA_checklist.py --inject-drift           # inject a deliberate compliance drift for testing
    python QA_checklist.py --input path/to/user_input.json   # bypass testcases/ entirely

Folder layout (all inside QA_checklist/, next to this file):
    testcases/
        <testcase_name>/
            user_input.json           - CampaignInput sample (BP-01 "Input" section).
                                         This is the ONLY file the agents read as input.
                                         Any brand_kit image field here must be a real
                                         local file path (e.g. "./brand_assets/brand_logo.jpg"),
                                         not a remote URL.
            planning_output.json      - reference example of what a CampaignPlan looks
                                         like (documentation only, not loaded by the agent).
            assets_model_output.json  - reference example of what an AssetBundle looks
                                         like, happy_case/unhappy_case (documentation only,
                                         not loaded by the agent).
            brand_assets/              - real brand logo / product photos, generated once
                                         via generate_testcase_assets.py + byteplus_ark.py.
                                         Committed to the repo (unlike ark_out/ below).
            ark_out/                   - disposable per-run output: campaign images/video
                                         produced by GenAssetsAgent each time you run
                                         QA_checklist.py. Gitignored, regenerated every run.
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

class ProductBrief(BaseModel):
    product_name: str
    category: str
    key_selling_points: list[str] = Field(default_factory=list)
    price_or_promotion: Optional[str] = None
    target_market: str
    required_claims: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)


class BrandKit(BaseModel):
    logo_url: Optional[str] = None
    brand_colors: list[str] = Field(default_factory=list)
    tone_of_voice: Optional[str] = None
    product_photo_urls: list[str] = Field(default_factory=list)


class AudienceBrief(BaseModel):
    target_customer: str
    language: str
    platform: list[str] = Field(default_factory=list)
    market: str


class MarketSignal(BaseModel):
    trend: Optional[str] = None
    seasonal_moment: Optional[str] = None
    consumer_pain_point: Optional[str] = None
    search_keyword: Optional[str] = None
    competitor_angle: Optional[str] = None
    campaign_objective: Optional[str] = None
    sources: list[str] = Field(default_factory=list)  # citations backing the signal


class PastCampaignData(BaseModel):
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    roas: Optional[float] = None
    watch_time_sec: Optional[float] = None
    add_to_cart_rate: Optional[float] = None
    comments: list[str] = Field(default_factory=list)
    sales_results: Optional[str] = None


class CampaignInput(BaseModel):
    campaign_id: str
    product_brief: ProductBrief
    brand_kit: BrandKit
    audience_brief: AudienceBrief
    market_signal: MarketSignal
    past_campaign_data: Optional[PastCampaignData] = None


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
# 2. PROMPTS
# ===========================================================================
# Text prompts used for the LLM-reasoned parts (positioning + commerce copy),
# and image/video prompt templates handed to byteplus_ark.py for Seedream 5.0
# Pro / Seedance 2.5. Kept as plain string templates so they are easy to
# tweak without touching the agent logic below.

PLANNING_SYSTEM_PROMPT = (
    "Ban la mot AI content strategist cho thuong mai dien tu. Luon tra ve JSON hop le."
)

PLANNING_PROMPT_TEMPLATE = """Ban la chuyen gia chien luoc marketing thuong mai dien tu.
Hay xay dung dinh vi san pham (product positioning) cho campaign sau, va tra ve
DUY NHAT mot JSON object hop le voi cac key chinh xac sau (khong markdown, khong giai thich them):

{{
  "main_campaign_angle": "<1 cau, goc do chinh cua campaign>",
  "key_selling_message": "<1 cau, thong diep ban hang chinh>",
  "product_benefit_hierarchy": ["<loi ich 1>", "<loi ich 2>", "..."]
}}

Thong tin san pham:
- Ten: {product_name}
- Nganh: {category}
- Diem ban hang chinh: {key_selling_points}
- Thi truong: {target_market}
- Khach hang muc tieu: {target_customer}
- Ngon ngu: {language}
- Noi dau cua khach hang (pain point): {pain_point}
- Xu huong lien quan: {trend}
"""

COPY_SYSTEM_PROMPT = (
    "Ban la copywriter e-commerce chuyen nghiep. Luon tra ve JSON hop le va tuyet doi "
    "khong dung cac claims bi cam."
)

COPY_PROMPT_TEMPLATE = """Ban la copywriter thuong mai dien tu. Dua tren dinh vi campaign sau, hay viet
commerce copy va tra ve DUY NHAT mot JSON object hop le voi cac key chinh xac sau
(khong markdown, khong giai thich them):

{{
  "product_title": "<tieu de san pham, <=60 ky tu>",
  "product_description": "<mo ta san pham, 2-3 cau>",
  "listing_bullet_points": ["<gach dau dong 1>", "<gach dau dong 2>", "<gach dau dong 3>"],
  "ad_caption": "<caption quang cao ngan>",
  "promotion_copy": "<cau khuyen mai ngan, hoac null>",
  "short_hook_lines": ["<hook 1>", "<hook 2>"]
}}

Dinh vi campaign:
- Goc do chinh: {main_campaign_angle}
- Thong diep chinh: {key_selling_message}
- San pham: {product_name} ({category})
- Khuyen mai: {promotion}
- Claims bat buoc phai co: {required_claims}
- Claims cam ky (KHONG duoc dung): {forbidden_claims}
"""

# Image prompt templates keyed by ImageKind — {brand_style} and {product_name}
# are filled in from CampaignInput.brand_kit / product_brief at generation time.
IMAGE_PROMPT_TEMPLATES: dict[ImageKind, str] = {
    ImageKind.HERO: (
        "{product_name}, centered hero product shot on a soft gradient studio "
        "background, {brand_style}"
    ),
    ImageKind.SKU_DETAIL: (
        "macro close-up on the {product_name} packaging/label, showing key "
        "ingredient icons and nutrition facts area, sharp focus, {brand_style}"
    ),
    ImageKind.COLLECTION: (
        "flat-lay of {product_name} surrounded by its key ingredients, overhead "
        "shot, e-commerce campaign collection image, {brand_style}"
    ),
    ImageKind.THUMBNAIL: (
        "square marketplace cover image of {product_name}, bold and eye-catching "
        "for a Shopee/TikTok Shop listing thumbnail, {brand_style}"
    ),
    ImageKind.BANNER: (
        "e-commerce promotion banner for {product_name}, wide banner layout, "
        "{brand_style}"
    ),
}

# Video prompt template per creative route — {hook_idea} / {visual_direction}
# come straight out of the generated CampaignPlan.creative_routes.
VIDEO_PROMPT_TEMPLATE = (
    "{hook_idea}. Visual direction: {visual_direction}. Ends on a clean product hero shot."
)

# --- QA checklist agent prompts -------------------------------------------
# ChecklistAgent: reads the raw CampaignInput and produces a short list of
# concrete, checkable QA criteria (max 7) tailored to that specific brief —
# e.g. "The product image colors must match brand_kit.brand_colors",
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


# ===========================================================================
# 3. AGENT FLOW: gen_plan -> gen_assets -> qa_review
# ===========================================================================

class GenPlanAgent:
    """Produces a CampaignPlan from a CampaignInput. Always reasons over the
    actual CampaignInput fields — never reads a pre-baked plan from disk.

    live mode      : calls Seed 2.1 (via byteplus_ark.chat) using
                      PLANNING_PROMPT_TEMPLATE for the reasoned positioning text.
    built-in mode  : runs a deterministic rule-based generator (_generate_builtin)
                      driven by the same CampaignInput fields the live prompt would
                      use (product name, key selling points, pain point, trend),
                      so it is a genuine (if simpler) agent, not a fixture replay.

    In both modes, creative_routes/ab_test_plan are built by
    _default_creative_routes/_default_ab_test_plan from the input's audience
    platforms — structural scaffolding, not the reasoned part.
    """

    def __init__(self, live: bool = False):
        self.live = live

    def generate(
        self, campaign_input: CampaignInput, extra_context: str = "", inject_drift: bool = False
    ) -> CampaignPlan:
        if self.live:
            plan = self._generate_live(campaign_input, extra_context)
        else:
            plan = self._generate_builtin(campaign_input, extra_context)

        if inject_drift:
            _apply_plan_drift(plan)
        return plan

    def _generate_builtin(self, campaign_input: CampaignInput, extra_context: str) -> CampaignPlan:
        """Rule-based positioning generator — no network call, but genuinely
        derived from campaign_input (not a canned fixture)."""
        product = campaign_input.product_brief
        audience = campaign_input.audience_brief
        signal = campaign_input.market_signal

        top_benefit = product.key_selling_points[0] if product.key_selling_points else "a better everyday choice"
        pain_point = signal.consumer_pain_point or "an unmet need in this category"
        trend_clause = f" riding the '{signal.trend}' trend" if signal.trend else ""

        main_angle = f"{product.product_name}: {top_benefit}, without the trade-off {pain_point} implies{trend_clause}."
        key_message = f"{product.product_name} solves {pain_point}."
        if extra_context:
            key_message += " (Regenerated with QA feedback applied.)"

        positioning = ProductPositioning(
            main_campaign_angle=main_angle,
            target_audience=audience.target_customer,
            key_selling_message=key_message,
            product_benefit_hierarchy=product.key_selling_points or ["Quality", "Value", "Convenience"],
            sources=signal.sources or [],
        )
        return CampaignPlan(
            campaign_id=campaign_input.campaign_id,
            positioning=positioning,
            creative_routes=_default_creative_routes(campaign_input),
            ab_test_plan=_default_ab_test_plan(),
            performance_learning=_build_performance_learning(campaign_input),
        )

    def _generate_live(self, campaign_input: CampaignInput, extra_context: str) -> CampaignPlan:
        ark = _load_ark_client()
        product = campaign_input.product_brief
        audience = campaign_input.audience_brief
        signal = campaign_input.market_signal

        prompt = PLANNING_PROMPT_TEMPLATE.format(
            product_name=product.product_name,
            category=product.category,
            key_selling_points=", ".join(product.key_selling_points),
            target_market=product.target_market,
            target_customer=audience.target_customer,
            language=audience.language,
            pain_point=signal.consumer_pain_point or "khong ro",
            trend=signal.trend or "khong ro",
        )
        if extra_context:
            prompt += f"\nLuu y bo sung (khac phuc loi QA truoc do):\n{extra_context}\n"

        raw = ark.chat(prompt, system=PLANNING_SYSTEM_PROMPT)
        data = _parse_llm_json(raw)

        positioning = ProductPositioning(
            main_campaign_angle=data["main_campaign_angle"],
            target_audience=audience.target_customer,
            key_selling_message=data["key_selling_message"],
            product_benefit_hierarchy=data.get("product_benefit_hierarchy") or product.key_selling_points,
            sources=signal.sources or [],
        )
        return CampaignPlan(
            campaign_id=campaign_input.campaign_id,
            positioning=positioning,
            creative_routes=_default_creative_routes(campaign_input),
            ab_test_plan=_default_ab_test_plan(),
            performance_learning=_build_performance_learning(campaign_input),
        )


class GenAssetsAgent:
    """Produces an AssetBundle (images + video + commerce copy) from a CampaignPlan.
    Always derives copy/images/video from the actual plan + campaign_input —
    never reads a pre-baked AssetBundle from disk.

    live mode      : calls Seed 2.1 for commerce copy, and Seedream 5.0 Pro /
                      Seedance 2.5 (via byteplus_ark.py) for real product images
                      and a real short-form video.
    built-in mode  : builds commerce copy with a deterministic rule-based
                      generator (_generate_copy_builtin) that honours
                      required_claims/forbidden_claims from the input, and
                      synthesizes local placeholder image/video files (via
                      byteplus_ark.py's PIL/ffmpeg-free stand-ins, see
                      _synthesize_placeholder_image/_video) covering every
                      required ImageKind + one video, so the QA rules engine
                      is exercised against genuinely-generated (if simple)
                      assets rather than a canned bundle.
    """

    def __init__(self, live: bool = False):
        self.live = live

    def generate(
        self,
        plan: CampaignPlan,
        campaign_input: CampaignInput,
        extra_context: str = "",
        inject_drift: bool = False,
        out_dir: Optional[Path] = None,
    ) -> AssetBundle:
        """out_dir: where generated image/video files are written. Defaults
        to REPO_ROOT/ark_out/<campaign_id> if not given (e.g. when running
        with a custom --input file outside any testcase folder). When run
        via --testcase <name>, this is testcases/<name>/ark_out/."""
        if out_dir is None:
            out_dir = REPO_ROOT / "ark_out" / plan.campaign_id
        out_dir.mkdir(parents=True, exist_ok=True)

        if self.live:
            bundle = self._generate_live(plan, campaign_input, extra_context, out_dir)
        else:
            bundle = self._generate_builtin(plan, campaign_input, extra_context, out_dir)

        if inject_drift:
            _apply_assets_drift(bundle, campaign_input)
        return bundle

    # -- commerce copy: shared builtin generator (used by both live-image/
    #    built-in-image paths when no LLM is available for copy specifically) --
    def _generate_copy_builtin(
        self, plan: CampaignPlan, campaign_input: CampaignInput, extra_context: str
    ) -> CommerceCopy:
        product = campaign_input.product_brief
        angle = plan.positioning.main_campaign_angle
        benefits = plan.positioning.product_benefit_hierarchy or product.key_selling_points

        title = f"{product.product_name}"
        if product.key_selling_points:
            title += f" - {product.key_selling_points[0]}"
        title = title[:60]

        description_parts = [plan.positioning.key_selling_message]
        # Weave in every required_claim verbatim so USER.MISSING_REQUIRED_CLAIM
        # cannot fire against builtin-generated copy (mirrors what a well
        # -behaved LLM prompt would be instructed to do).
        for claim in product.required_claims:
            if claim.strip() and claim.strip().lower() not in description_parts[0].lower():
                description_parts.append(f"Made with {claim}." if "made" not in claim.lower() else claim.capitalize() + ".")
        description = " ".join(description_parts)

        bullets = list(benefits)[:5]
        ad_caption = f"{angle} #{product.product_name.replace(' ', '')}"
        promo = product.price_or_promotion
        hooks = [f"Meet {product.product_name}.", plan.positioning.key_selling_message]

        return CommerceCopy(
            product_title=title,
            product_description=description,
            listing_bullet_points=bullets,
            ad_caption=ad_caption,
            promotion_copy=promo,
            short_hook_lines=hooks,
        )

    def _generate_builtin(
        self, plan: CampaignPlan, campaign_input: CampaignInput, extra_context: str, out_dir: Path
    ) -> AssetBundle:
        copy = self._generate_copy_builtin(plan, campaign_input, extra_context)
        campaign_id = plan.campaign_id

        images: list[ImageAsset] = []
        for kind in REQUIRED_IMAGE_KINDS:
            w, h = (1080, 1080) if kind == ImageKind.THUMBNAIL else (2048, 2048)
            path = _synthesize_placeholder_image(out_dir / f"{kind.value}.jpg", kind.value, w, h)
            images.append(ImageAsset(kind=kind, url=str(path), width=w, height=h, model="builtin-placeholder"))

        route = plan.creative_routes[0]
        video_path = _synthesize_placeholder_video(out_dir / f"route_{route.route_id}.mp4", duration_sec=20)
        videos = [
            VideoAsset(
                url=str(video_path), duration_sec=20, resolution="720p",
                aspect_ratio="9:16", route_id=route.route_id, model="builtin-placeholder",
            )
        ]

        return AssetBundle(campaign_id=campaign_id, images=images, videos=videos, listing_copy=copy)

    def _generate_live(
        self, plan: CampaignPlan, campaign_input: CampaignInput, extra_context: str, out_dir: Path
    ) -> AssetBundle:
        ark = _load_ark_client()
        product = campaign_input.product_brief
        brand = campaign_input.brand_kit
        campaign_id = plan.campaign_id

        # --- Commerce copy: real LLM call (Seed 2.1) ---
        prompt = COPY_PROMPT_TEMPLATE.format(
            main_campaign_angle=plan.positioning.main_campaign_angle,
            key_selling_message=plan.positioning.key_selling_message,
            product_name=product.product_name,
            category=product.category,
            promotion=product.price_or_promotion or "khong co",
            required_claims=product.required_claims or "khong co",
            forbidden_claims=product.forbidden_claims or "khong co",
        )
        if extra_context:
            prompt += f"\nLuu y bo sung (khac phuc loi QA truoc do):\n{extra_context}\n"

        copy_raw = ark.chat(prompt, system=COPY_SYSTEM_PROMPT)
        copy_data = _parse_llm_json(copy_raw)
        copy = CommerceCopy(
            product_title=copy_data["product_title"],
            product_description=copy_data["product_description"],
            listing_bullet_points=copy_data.get("listing_bullet_points") or [],
            ad_caption=copy_data["ad_caption"],
            promotion_copy=copy_data.get("promotion_copy"),
            short_hook_lines=copy_data.get("short_hook_lines") or [],
        )

        # --- Images: real Seedream 5.0 Pro calls, one per required kind ---
        brand_style = (
            f"brand colors {', '.join(brand.brand_colors)}, tone of voice: "
            f"{brand.tone_of_voice or 'clean e-commerce product photography'}, no added text/watermark"
        )

        images: list[ImageAsset] = []
        for kind, template in IMAGE_PROMPT_TEMPLATES.items():
            prompt = template.format(product_name=product.product_name, brand_style=brand_style)
            size = "1080x1080" if kind == ImageKind.THUMBNAIL else "2048x2048"
            url = ark.text_to_image(prompt, size=size)
            local_path = _download_to(ark, url, out_dir / f"{kind.value}.jpg")
            w, h = (1080, 1080) if kind == ImageKind.THUMBNAIL else (2048, 2048)
            images.append(ImageAsset(kind=kind, url=str(local_path), width=w, height=h))

        # --- Video: real Seedance 2.5 call for the first creative route ---
        route = plan.creative_routes[0]
        video_prompt = VIDEO_PROMPT_TEMPLATE.format(
            hook_idea=route.hook_idea, visual_direction=route.visual_direction
        )
        task_id = ark.create_video(video_prompt, resolution="720p", ratio="9:16", duration=20)
        video_url = ark.wait_video(task_id)
        video_path = _download_to(ark, video_url, out_dir / f"route_{route.route_id}.mp4")
        videos = [
            VideoAsset(
                url=str(video_path), duration_sec=20, resolution="720p",
                aspect_ratio="9:16", route_id=route.route_id,
            )
        ]

        return AssetBundle(campaign_id=campaign_id, images=images, videos=videos, listing_copy=copy)


# ---------------------------------------------------------------------------
# QA review agent — the main deliverable. Checklist grouped into 3 buckets
# mirroring draft_idea.txt:
#   1. Internal system criteria   (_check_internal_*)   - schema/spec completeness
#   2. Market research criteria   (_check_market_*)     - claims backed by sources
#   3. User-provided criteria     (_check_user_*)       - brand kit / brief compliance
# QA passes only when there are zero BLOCKER issues.
# ---------------------------------------------------------------------------

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
    """Reviews ONE checklist criterion against the actual generated
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


MAX_CHECKLIST_ITEMS = 7
MAX_ITERATIONS = 3


def review(
    campaign_input: CampaignInput,
    plan: CampaignPlan,
    assets: AssetBundle,
    iteration: int = 1,
    checklist_agent: Optional[ChecklistAgent] = None,
    review_agent: Optional[ChecklistReviewAgent] = None,
) -> QAResult:
    """Runs the full checklist-based QA review for one campaign:
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
        campaign_id=campaign_input.campaign_id,
        passed=passed,
        iteration=iteration,
        issues=issues,
        checklist_results=results,
    )


def run_campaign(
    campaign_input: CampaignInput,
    plan_agent: GenPlanAgent,
    assets_agent: GenAssetsAgent,
    inject_drift: bool = False,
    max_iterations: int = MAX_ITERATIONS,
    out_dir: Optional[Path] = None,
) -> tuple[CampaignPlan, AssetBundle, QAResult, list[QAResult]]:
    """Orchestrates gen_plan -> gen_assets -> qa_review, looping with QA feedback
    as additional context on failure, up to max_iterations. Per draft_idea.txt:
    'Lam cho den khi dat cac tieu chi, va khong co van de phat hien.'

    inject_drift only applies on iteration 1 (to exercise/demonstrate the
    unhappy path deterministically); the retry loop then genuinely tries to
    self-correct using the QA remediation feedback as extra_context.

    out_dir: where generated image/video files are written (passed through
    to GenAssetsAgent.generate). Defaults to REPO_ROOT/ark_out/<campaign_id>
    if not given.

    Returns (final_plan, final_assets, final_result, all_iteration_results)
    so callers/CLI can show the full retry history, not just the final pass.
    """
    extra_context = ""
    plan: Optional[CampaignPlan] = None
    assets: Optional[AssetBundle] = None
    result: Optional[QAResult] = None
    history: list[QAResult] = []

    for iteration in range(1, max_iterations + 1):
        drift_this_round = inject_drift and iteration == 1
        plan = plan_agent.generate(campaign_input, extra_context=extra_context, inject_drift=drift_this_round)
        assets = assets_agent.generate(
            plan, campaign_input, extra_context=extra_context, inject_drift=drift_this_round, out_dir=out_dir
        )
        result = review(campaign_input, plan, assets, iteration=iteration)
        history.append(result)

        if result.passed:
            break

        blockers = result.issues  # every failed checklist item blocks QA now
        extra_context = "\n".join(f"- {issue}" for issue in blockers)

    assert plan is not None and assets is not None and result is not None
    return plan, assets, result, history


# ===========================================================================
# Helpers: I/O, byteplus_ark.py bridge, LLM JSON parsing
# ===========================================================================

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _download_to(ark, url: str, dest: Path) -> Path:
    """Downloads a signed asset URL (from byteplus_ark.text_to_image/wait_video)
    directly to `dest`, bypassing byteplus_ark's own shared ark_out/ dir, so
    each testcase's generated assets land in its own testcases/<name>/ark_out/."""
    import requests

    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest


def _load_ark_client():
    """Import byteplus_ark.py (repo root) lazily, only when live mode is used,
    so mock mode never requires ARK_API_KEY or the `requests` package."""
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


def _default_creative_routes(campaign_input: CampaignInput) -> list[CreativeRoute]:
    platforms = campaign_input.audience_brief.platform or ["TikTok Shop"]
    return [
        CreativeRoute(
            route_id="A",
            hook_idea="Problem-agitate-solve opener in first 2 seconds",
            visual_direction="Close-up product shot, natural lighting, UGC style",
            message_angle="Pain-point led",
            suggested_platform_usage=platforms,
        ),
        CreativeRoute(
            route_id="B",
            hook_idea="Testimonial / social-proof opener",
            visual_direction="Studio product photography, clean background",
            message_angle="Trust / social-proof led",
            suggested_platform_usage=platforms,
        ),
    ]


def _default_ab_test_plan() -> ABTestPlan:
    return ABTestPlan(
        what_to_test="Hook style: pain-point vs. testimonial",
        route_a="A",
        route_b="B",
        success_metrics=["CTR", "3s view rate", "Add-to-cart rate"],
        expected_learning="Which emotional entry point drives higher early engagement for this audience.",
    )


def _build_performance_learning(campaign_input: CampaignInput) -> Optional[PerformanceLearning]:
    """Derives an optional performance-learning block from past_campaign_data,
    if the user supplied it. Genuinely reads the input's numbers/comments —
    not a canned fixture."""
    past = campaign_input.past_campaign_data
    if past is None:
        return None

    keep, change, stop, test_next = [], [], [], []

    if past.add_to_cart_rate is not None and past.add_to_cart_rate >= 3.0:
        keep.append(f"Add-to-cart rate ({past.add_to_cart_rate}%) was healthy — keep the same funnel structure.")
    if past.ctr is not None and past.ctr < 2.0:
        change.append(f"CTR ({past.ctr}%) underperformed — test a faster, punchier hook in the first 2 seconds.")
    if past.roas is not None and past.roas < 1.5:
        stop.append(f"ROAS ({past.roas}) was weak — stop scaling spend on the previous creative direction.")
    if past.sales_results:
        test_next.append(f"Build on prior result context: {past.sales_results[:160]}")

    if not (keep or change or stop or test_next):
        return None
    return PerformanceLearning(keep=keep, change=change, stop=stop, test_next=test_next)


def _apply_plan_drift(plan: CampaignPlan) -> None:
    """Deliberately mutates a plan to violate a QA rule, for exercising the
    unhappy-path in tests/CLI (--inject-drift). Drops to 1 creative route,
    which triggers PLAN.ROUTE_COUNT."""
    plan.creative_routes = plan.creative_routes[:1]


def _apply_assets_drift(assets: AssetBundle, campaign_input: Optional[CampaignInput] = None) -> None:
    """Deliberately mutates an asset bundle to violate QA rules, for
    exercising the unhappy-path (--inject-drift):
      - drops the sku_detail_image kind      -> ASSETS.MISSING_IMAGE_KIND
      - stretches video to 34s, 1:1 aspect    -> ASSETS.VIDEO_DURATION/ASPECT (warnings)
      - injects a forbidden_claims phrase and strips wording matching a
        required_claims phrase from the description, so USER.FORBIDDEN_CLAIM
        and USER.MISSING_REQUIRED_CLAIM fire against genuinely generated
        (not canned) copy, using the campaign's own declared claims."""
    assets.images = [img for img in assets.images if img.kind != ImageKind.SKU_DETAIL]
    for v in assets.videos:
        v.duration_sec = 34
        v.aspect_ratio = "1:1"

    if campaign_input is not None:
        product = campaign_input.product_brief
        if product.forbidden_claims:
            assets.listing_copy.product_description += f" This product {product.forbidden_claims[0]}."
        if product.required_claims:
            drop = product.required_claims[0].strip().lower()
            desc = assets.listing_copy.product_description
            idx = desc.lower().find(drop)
            if idx != -1:
                assets.listing_copy.product_description = (desc[:idx] + desc[idx + len(drop):]).strip()


def _synthesize_placeholder_image(path: Path, label: str, width: int, height: int) -> Path:
    """Creates a minimal valid JPEG placeholder file locally (no network call).
    Uses Pillow if available; otherwise writes a tiny valid JPEG byte stream
    so downstream code always has a real file to point at."""
    try:
        from PIL import Image, ImageDraw  # type: ignore

        img = Image.new("RGB", (width, height), color=(230, 230, 230))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), label, fill=(20, 20, 20))
        img.save(path, "JPEG")
    except ImportError:
        # Minimal 1x1 black JPEG (valid file bytes) as a last-resort stand-in.
        _MINIMAL_JPEG_BYTES = bytes.fromhex(
            "ffd8ffe000104a46494600010100000100010000ffdb004300030202020203020"
            "2020303030304060404040405050506070706070707070a090a0a0908090909ff"
            "c00011080001000103012200021101031101ffc4001f0000010501010101010100"
            "000000000000000102030405060708090a0bffc400b5100002010303020403050"
            "5040400000001027d01020300041105122131410613516107227114328191a1082"
            "342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a4"
            "34445464748494a535455565758595a636465666768696a737475767778797a838"
            "48586878889898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9"
            "bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f"
            "5f6f7f8f9faffda0008010100003f00fb"
            "fdffd9"
        )
        path.write_bytes(_MINIMAL_JPEG_BYTES)
    return path


def _synthesize_placeholder_video(path: Path, duration_sec: float) -> Path:
    """Creates a minimal placeholder video file locally (no network call).
    Writes a tiny valid empty MP4 container so downstream code always has a
    real file to point at. Duration is tracked in the VideoAsset metadata
    (the QA rules check that field), not by encoding actual frames."""
    _MINIMAL_MP4_BYTES = bytes.fromhex(
        "0000001c667479706d70343200000000697"
        "36f6d6d70343200000008667265650000000870"
        "64617400000008" .replace(" ", "")
    )
    try:
        path.write_bytes(_MINIMAL_MP4_BYTES)
    except Exception:
        path.touch()
    return path


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
             "Reads testcases/<name>/user_input.json as input, and writes generated "
             "image/video files to testcases/<name>/ark_out/.",
    )
    parser.add_argument(
        "--input", type=Path, default=None,
        help="Override: path to a CampaignInput JSON file to use instead of "
             "testcases/<testcase>/user_input.json. When set, generated assets are "
             "written to REPO_ROOT/ark_out/<campaign_id>/ instead of a testcase folder.",
    )
    parser.add_argument(
        "--inject-drift", action="store_true",
        help="Deliberately drop the sku_detail_image, distort the video duration/aspect, "
             "and inject a forbidden claim / drop a required claim on the first iteration, "
             "to demonstrate the QA unhappy-path and the regenerate-and-recheck loop.",
    )
    parser.add_argument(
        "--live", dest="live", action="store_true", default=True,
        help="Use real BytePlus ModelArk API calls (Seed 2.1 / Seedream 5.0 Pro / Seedance 2.5) "
             "via byteplus_ark.py. This is the DEFAULT — requires ARK_API_KEY (see .env.example). "
             "Pass --mock to use the built-in rule-based generator instead (no API key needed).",
    )
    parser.add_argument(
        "--mock", dest="live", action="store_false",
        help="Use the built-in rule-based generator + local placeholder image/video files "
             "instead of real BytePlus API calls. No ARK_API_KEY needed.",
    )
    args = parser.parse_args()

    if args.input is not None:
        input_path = args.input
        out_dir = None  # falls back to REPO_ROOT/ark_out/<campaign_id> in GenAssetsAgent.generate
    else:
        testcase_dir = TESTCASES_DIR / args.testcase
        input_path = testcase_dir / "user_input.json"
        out_dir = testcase_dir / "ark_out"
        if not input_path.exists():
            available = sorted(p.name for p in TESTCASES_DIR.iterdir() if p.is_dir()) if TESTCASES_DIR.exists() else []
            raise SystemExit(
                f"Testcase '{args.testcase}' not found (expected {input_path}).\n"
                f"Available testcases: {available or '(none found)'}"
            )

    campaign_input = CampaignInput.model_validate(_load_json(input_path))

    _print_section("1. CAMPAIGN INPUT")
    print(campaign_input.model_dump_json(indent=2))

    plan_agent = GenPlanAgent(live=args.live)
    assets_agent = GenAssetsAgent(live=args.live)

    plan, assets, result, history = run_campaign(
        campaign_input, plan_agent, assets_agent, inject_drift=args.inject_drift, out_dir=out_dir
    )

    _print_section("2. GENERATED PLAN (final)")
    print(plan.model_dump_json(indent=2))

    _print_section("3. GENERATED ASSETS (final)")
    print(assets.model_dump_json(indent=2))

    if len(history) > 1:
        _print_section("4. QA RETRY HISTORY")
        for past_result in history:
            status = "PASS" if past_result.passed else "FAIL"
            print(f"  Iteration {past_result.iteration}: {status} ({len(past_result.issues)} issue(s))")
            for item in past_result.checklist_results:
                mark = "PASS" if item.passed else "FAIL"
                print(f"    [{mark}] {item.criterion} -> {item.verdict}")

    _print_section("5. FINAL QA RESULT")
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
