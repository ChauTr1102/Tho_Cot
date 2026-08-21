// ---------------------------------------------------------------------------
// INTENTIONALLY MOCKED — product decision.
//
// content-generation is NOT yet wired to a real generation backend. Until
// that exists, we synthesize a CampaignOutputDTO-shaped JSON object (matching
// backend/app/schemas/campaign_dto.py exactly, snake_case) so that the QA
// gate and final report have something realistic to run against instead of
// stage-qa-gate.tsx's own hardcoded SAMPLE_CAMPAIGN_OUTPUT fallback.
//
// Where real generated data already exists (ResearchCampaignPlan's
// product_positioning / creative_routes, produced by the real /research/run
// backend call), we map it into the DTO. Everything else (video asset, image
// set, commerce copy, A/B testing plan specifics) reuses the same hardcoded
// copy that is displayed in stage-content-generation.tsx's JSX, just also
// exposed here as structured data.
// ---------------------------------------------------------------------------

import type { ResearchCampaignPlan, ResearchInput } from "./research";

// Same hardcoded commerce copy shown in stage-content-generation.tsx's JSX.


/**
 * Builds a CampaignOutputDTO-shaped JSON object (snake_case), matching
 * backend/app/schemas/campaign_dto.py's CampaignOutputDTO exactly:
 * product_positioning, creative_routes, short_form_video_asset,
 * product_collection_image_set, commerce_copy, ab_testing_plan,
 * performance_learning.
 *
 * When `plan` is available (from the real /research/run call), its
 * product_positioning / creative_routes are mapped into the DTO's fields.
 * Everything else falls back to the hardcoded mock copy above.
 */
export function buildMockCampaignOutput(
  plan: ResearchCampaignPlan | null,
  input: ResearchInput,
): Record<string, unknown> {
  const positioning = plan?.product_positioning;
  const productName = input.product_brief.product_name || "Sản phẩm";

  const product_positioning = {
    main_campaign_angle:
      positioning?.main_campaign_angle.decision ??
      // Neutral, and built from this product. "Vị đậm chuẩn Việt" is coffee
      // language: it was written while the only campaign was G7, and it read
      // out over a pair of children's trainers as "Giày Thể Thao Bé Gái Biti's
      // Cool — vị đậm chuẩn Việt". A placeholder must not describe a taste.
      `${productName} — ${input.product_brief.key_selling_points[0] ?? "điểm bán chưa xác định"}`,
    target_audience:
      positioning?.target_audience.decision ?? input.audience_brief.target_customer[0] ?? "Khách hàng mục tiêu",
    key_selling_message:
      positioning?.key_selling_message.decision ??
      input.product_brief.key_selling_points[0] ??
      "Chất lượng đảm bảo, giá trị vượt trội.",
    product_benefit_hierarchy:
      positioning && positioning.benefit_hierarchy.length
        ? positioning.benefit_hierarchy.map((item) => item.benefit)
        : input.product_brief.key_selling_points,
  };

  const creative_routes =
    plan && plan.creative_routes.length
      ? plan.creative_routes.map((route) => ({
          name: route.route_name,
          hook_idea: route.hook_idea,
          visual_direction: route.visual_direction,
          message_angle: route.message_angle,
          suggested_platform_usage: route.suggested_platform_usage,
        }))
      : // No plan yet means no creative routes yet. Showing G7's two here made
        // every campaign look like it had a strategy, and the strategy was
        // somebody else's.
        [];

  // Video and images have no real generation backend result yet at this
  // point in the pipeline (before content-generation's studio run reports
  // real assets via onAssetsReady — see campaigns/page.tsx). Genuinely
  // empty rather than a placeholder https://example.com/mock/*.jpg URL:
  // the QA checklist's own rules (backend/app/services/qa_checklist_service.py
  // and qa_agent/service.py) already check for a blank string/empty list
  // and report a correct "not generated yet" issue for it. A fake URL that
  // *looks* real instead made the QA agent try to load it as an actual
  // image and fail with a confusing "no real image could be loaded" error —
  // technically correct (the URL was never real) but reported as the wrong
  // kind of failure for the wrong reason.
  const short_form_video_asset = {
    generated_video_urls: [] as string[],
    format: "9:16",
    duration: "0s",
    additional_cuts: [],
  };

  const product_collection_image_set = {
    product_hero_image: "",
    sku_detail_image: "",
    campaign_collection_image: "",
    marketplace_thumbnail: "",
  };

  // Derived from this campaign, never borrowed from another one. These fields
  // used to be `{ ...MOCK_COMMERCE_COPY }` unconditionally — the G7 sample —
  // so a campaign for children's shoes showed "Cà phê hòa tan 3in1 Trung Nguyên
  // G7" as its product title and "xé gói G7 pha nước nóng" as its A/B hooks.
  // The mock exists to keep the screen from breaking before the real copy
  // arrives, and a different product's copy breaks it worse than a blank does.
  const commerce_copy = {
    product_title: productName,
    product_description: input.product_brief.key_selling_points.join(". "),
    listing_bullet_points: input.product_brief.key_selling_points,
    ad_caption: "",
    promotion_copy: input.product_brief.promotion ?? "",
    short_hook_lines: creative_routes.map((route) => route.hook_idea).filter(Boolean),
  };

  const ab_testing_plan = {
    what_to_test: "Hiệu quả của hook mở đầu giữa hai hướng sáng tạo",
    route_a_description: creative_routes[0]?.hook_idea ?? "",
    route_b_description: creative_routes[1]?.hook_idea ?? "",
    suggested_success_metrics: ["CTR", "CVR", "Add-to-cart rate", "Watch time"],
    expected_learning: "Xác định động lực mua hàng mạnh nhất theo từng kênh và thị trường.",
  };

  const performance_learning = null;

  return {
    product_positioning,
    creative_routes,
    short_form_video_asset,
    product_collection_image_set,
    commerce_copy,
    ab_testing_plan,
    performance_learning,
  };
}

/**
 * Maps ResearchInput (frontend/src/types/research.ts) to the exact
 * snake_case CampaignInputDTO shape backend/app/schemas/campaign_dto.py
 * expects.
 *
 * The two schemas don't line up 1:1:
 * - product_brief.price / product_brief.promotion (two separate optional
 *   fields in ResearchInput) collapse into a single
 *   price_or_promotion { price, currency, promotion } object in the DTO.
 * - audience_brief in ResearchInput uses plural lists (target_customer,
 *   languages, platforms, markets); the DTO expects singular strings
 *   (target_customer, language, platform, market). We pick the first
 *   element of each list as the primary value — reasonable since the DTO
 *   was designed for a single-audience/single-platform generation run,
 *   while the research stage collects a broader brief upfront.
 * - market_signal in ResearchInput uses plural lists (trends,
 *   seasonal_moments, consumer_pain_points, competitor_angles); the DTO
 *   expects singular optional strings. We again take the first element
 *   (or null if the list is empty).
 * - past_campaign_data has no equivalent in ResearchInput at all (this
 *   pipeline doesn't collect historical performance data), so we default
 *   it to `enabled: false` with all metrics null/empty, matching the
 *   backend's optional defaults.
 *
 * This maps from real user input, so it should always succeed defensively
 * with `?? ""` / `?? []` fallbacks for optional/missing fields.
 */
export function buildCampaignInputDTO(input: ResearchInput): Record<string, unknown> {
  const productBrief = input.product_brief;
  const brandKit = input.brand_kit;
  const audienceBrief = input.audience_brief;
  const marketSignal = input.market_signal;

  const product_brief = {
    product_name: productBrief.product_name ?? "",
    category: productBrief.category ?? "",
    key_selling_points: productBrief.key_selling_points ?? [],
    price_or_promotion: {
      price: productBrief.price?.amount ?? null,
      currency: productBrief.price?.currency ?? "VND",
      promotion: productBrief.promotion ?? null,
    },
    target_market: productBrief.target_market?.[0] ?? "",
    required_claims: productBrief.required_claims ?? [],
    restricted_or_forbidden_claims: productBrief.restricted_claims ?? [],
  };

  const primaryColor = brandKit.brand_colors?.[0];
  const secondaryColor = brandKit.brand_colors?.[1];

  const brand_kit = {
    logo: { path: brandKit.logo ?? null },
    brand_colors: {
      primary: primaryColor?.hex ?? null,
      secondary: secondaryColor?.hex ?? null,
      accent: brandKit.brand_colors?.slice(2).map((color) => color.hex).filter((hex): hex is string => Boolean(hex)) ?? [],
      palette: brandKit.brand_colors?.map((color) => color.hex).filter((hex): hex is string => Boolean(hex)) ?? [],
    },
    tone_of_voice: {
      description: brandKit.tone_of_voice?.join(", ") ?? "",
      attributes: brandKit.tone_of_voice ?? [],
      do: [],
      dont: [],
    },
    product_photos: brandKit.product_photos ?? [],
    existing_product_visuals: brandKit.existing_product_visuals ?? [],
  };

  const audience_brief = {
    target_customer: audienceBrief.target_customer?.[0] ?? "",
    language: audienceBrief.languages?.[0] ?? "",
    platform: audienceBrief.platforms?.[0] ?? "",
    market: audienceBrief.markets?.[0] ?? "",
  };

  const market_signal = {
    trend: marketSignal.trends?.[0] ?? null,
    seasonal_moment: marketSignal.seasonal_moments?.[0] ?? null,
    consumer_pain_point: marketSignal.consumer_pain_points?.[0] ?? null,
    search_keyword: marketSignal.search_keywords ?? [],
    competitor_angle: marketSignal.competitor_angles?.[0] ?? null,
    campaign_objective: marketSignal.campaign_objectives?.[0] ?? "",
  };

  // ResearchInput has no historical performance data collection today.
  const past_campaign_data = {
    enabled: false,
    ctr: null,
    cvr: null,
    roas: null,
    watch_time: { value: null, unit: "seconds" },
    add_to_cart_rate: null,
    comments: [],
    sales_results: { units_sold: null, revenue: null, currency: "VND" },
  };

  return {
    product_brief,
    brand_kit,
    audience_brief,
    market_signal,
    past_campaign_data,
  };
}
