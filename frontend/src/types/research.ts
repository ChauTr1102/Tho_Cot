export type CampaignObjective = "awareness" | "consideration" | "conversion" | "retention" | "engagement" | "lead_generation";
export type VerificationStatus = "verified" | "estimated" | "unknown";

export interface ResearchInput {
  schema_version: "1.0";
  campaign_id: string;
  product_brief: {
    product_name: string;
    category: string;
    key_selling_points: string[];
    price: { amount: number; currency: string; unit: string; note: string | null } | null;
    promotion: string | null;
    target_market: string[];
    required_claims: string[];
    restricted_claims: string[];
  };
  brand_kit: {
    logo: string;
    brand_colors: Array<{ name: string; hex: string | null; verification_status: VerificationStatus }>;
    tone_of_voice: string[];
    product_photos: string[];
    existing_product_visuals: string[];
  };
  audience_brief: { target_customer: string[]; languages: string[]; platforms: string[]; markets: string[] };
  market_signal: {
    trends: string[];
    seasonal_moments: string[];
    consumer_pain_points: string[];
    search_keywords: string[];
    competitor_angles: string[];
    campaign_objectives: CampaignObjective[];
  };
}

export interface ResearchSubmission {
  input: ResearchInput;
  files: { logo: File | null; product_photos: File[]; existing_product_visuals: File[] };
  evidence: string;
}

export type EvidenceBasis = "product_brief" | "supplied_source" | "external_research" | "general_marketing_knowledge" | "assumption";
export interface ResearchEvidence { basis: EvidenceBasis; detail: string; source_url: string | null }
export interface ResearchDecision { decision: string; rationale: string; evidence: ResearchEvidence[] }

export interface ResearchCampaignPlan {
  schema_version: "1.0";
  product_positioning: {
    main_campaign_angle: ResearchDecision;
    target_audience: ResearchDecision;
    key_selling_message: ResearchDecision;
    benefit_hierarchy: Array<{ rank: number; benefit: string; rationale: string; evidence: ResearchEvidence[] }>;
  };
  creative_routes: Array<{
    route_name: string;
    hook_idea: string;
    visual_direction: string;
    message_angle: string;
    suggested_platform_usage: string[];
    rationale: string;
    evidence: ResearchEvidence[];
  }>;
  source_summary: {
    external_sources_supplied: boolean;
    sources: Array<{ title: string; url: string; usage: string }>;
    assumptions: string[];
  };
}

export const CAMPAIGN_OBJECTIVES: CampaignObjective[] = ["awareness", "consideration", "conversion", "retention", "engagement", "lead_generation"];

const ALLOWED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/tiff"]);

export function validateResearchSubmission({ input, files }: ResearchSubmission): string[] {
  const errors: string[] = [];
  if (!input.campaign_id.trim()) errors.push("Campaign ID là bắt buộc.");
  if (!input.product_brief.product_name.trim()) errors.push("Product name là bắt buộc.");
  if (!input.product_brief.category.trim()) errors.push("Category là bắt buộc.");
  if (!input.product_brief.key_selling_points.length) errors.push("Cần ít nhất một key selling point.");
  if (!input.product_brief.target_market.length) errors.push("Cần ít nhất một target market.");
  if (input.product_brief.price && (input.product_brief.price.amount < 0 || input.product_brief.price.currency.length < 3 || !input.product_brief.price.unit.trim())) errors.push("Price chưa đúng contract.");
  if (!input.brand_kit.brand_colors.length || input.brand_kit.brand_colors.some((color) => !color.name.trim() || (color.hex !== null && !/^#[0-9A-Fa-f]{6}$/.test(color.hex)))) errors.push("Brand colors chưa đúng contract.");
  if (!input.brand_kit.tone_of_voice.length) errors.push("Cần ít nhất một tone of voice.");
  if (!input.audience_brief.target_customer.length || !input.audience_brief.languages.length || !input.audience_brief.platforms.length || !input.audience_brief.markets.length) errors.push("Audience brief còn thiếu danh sách bắt buộc.");
  if (!input.market_signal.campaign_objectives.length) errors.push("Cần ít nhất một campaign objective.");
  if (!files.logo) errors.push("Logo là bắt buộc.");
  if (!files.product_photos.length) errors.push("Cần ít nhất một product photo.");
  const images = [...(files.logo ? [files.logo] : []), ...files.product_photos, ...files.existing_product_visuals];
  if (images.some((file) => !ALLOWED_IMAGE_TYPES.has(file.type) || file.size === 0 || file.size > 20 * 1024 * 1024)) errors.push("Ảnh phải đúng định dạng, không rỗng và không vượt quá 20 MB.");
  return errors;
}

export function parseResearchCampaignPlan(value: unknown): ResearchCampaignPlan {
  const plan = value as Partial<ResearchCampaignPlan> | null;
  const positioning = plan?.product_positioning;
  const validDecision = (decision: ResearchDecision | undefined) =>
    Boolean(decision && typeof decision.decision === "string" && typeof decision.rationale === "string" && Array.isArray(decision.evidence));
  if (plan?.schema_version !== "1.0" || !positioning ||
      !validDecision(positioning.main_campaign_angle) || !validDecision(positioning.target_audience) ||
      !validDecision(positioning.key_selling_message) || !Array.isArray(positioning.benefit_hierarchy) ||
      !Array.isArray(plan.creative_routes) || plan.creative_routes.length !== 2 ||
      !plan.source_summary || !Array.isArray(plan.source_summary.sources) || !Array.isArray(plan.source_summary.assumptions)) {
    throw new Error("Research backend trả về campaign plan không đúng schema 1.0.");
  }
  return plan as ResearchCampaignPlan;
}

export const createInitialResearchSubmission = (): ResearchSubmission => ({
  input: {
    schema_version: "1.0",
    campaign_id: `campaign-${Date.now()}`,
    product_brief: {
      product_name: "Cà Phê Hòa Tan G7 3in1 Hộp 50 Gói",
      category: "F&B / Cà phê / Hòa tan",
      key_selling_points: ["Vị đậm Robusta Buôn Ma Thuột", "Công thức 3in1 pha nhanh, tiện mang theo"],
      price: { amount: 135000, currency: "VND", unit: "túi 50 gói", note: null },
      promotion: "Mua 3 tặng 1 trong chiến dịch 9.9",
      target_market: ["Trung Quốc", "Hoa Kỳ", "Hàn Quốc", "Đông Nam Á"],
      required_claims: ["Cà phê hòa tan 3in1", "Cà phê Robusta Việt Nam / Buôn Ma Thuột"],
      restricted_claims: ["Claim chữa bệnh", "So sánh trực tiếp đối thủ", "Tuyên bố tuyệt đối hoặc siêu hạng"],
    },
    brand_kit: {
      logo: "logo.png",
      brand_colors: [{ name: "G7 Red", hex: "#E60000", verification_status: "estimated" }],
      tone_of_voice: ["Năng động", "Trực diện", "Tự hào bản sắc Việt"],
      product_photos: [], existing_product_visuals: [],
    },
    audience_brief: {
      target_customer: ["Dân văn phòng", "Sinh viên 18–34", "Người yêu thích cà phê Việt vị đậm", "Khách mua quà"],
      languages: ["vi", "zh-CN", "en", "ko"],
      platforms: ["Douyin", "Tmall", "Taobao", "Shopee"],
      markets: ["Trung Quốc", "Hoa Kỳ", "Hàn Quốc", "Đông Nam Á"],
    },
    market_signal: {
      trends: ["Lối sống nhanh", "Livestream commerce"],
      seasonal_moments: ["China 9.9 Shopping Festival"],
      consumer_pain_points: ["Cần thức uống pha nhanh cho buổi sáng bận rộn"],
      search_keywords: ["cà phê hòa tan đậm vị", "cà phê Việt Nam"],
      competitor_angles: [], campaign_objectives: ["awareness", "conversion"],
    },
  },
  files: { logo: null, product_photos: [], existing_product_visuals: [] }, evidence: "",
});

export const createEmptyResearchSubmission = (): ResearchSubmission => ({
  input: {
    schema_version: "1.0",
    campaign_id: `campaign-${Date.now()}`,
    product_brief: {
      product_name: "",
      category: "",
      key_selling_points: [],
      price: null,
      promotion: null,
      target_market: [],
      required_claims: [],
      restricted_claims: [],
    },
    brand_kit: {
      logo: "logo.png",
      brand_colors: [{ name: "Primary Color", hex: "#000000", verification_status: "unknown" }],
      tone_of_voice: [],
      product_photos: [],
      existing_product_visuals: [],
    },
    audience_brief: {
      target_customer: [],
      languages: ["vi"],
      platforms: ["TikTok Shop"],
      markets: ["Việt Nam"],
    },
    market_signal: {
      trends: [],
      seasonal_moments: [],
      consumer_pain_points: [],
      search_keywords: [],
      competitor_angles: [],
      campaign_objectives: ["conversion"],
    },
  },
  files: { logo: null, product_photos: [], existing_product_visuals: [] },
  evidence: "",
});
