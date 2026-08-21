/* ═══════════════════════════════════════════════════════════
   CAIBS — Multi-Agent AI Campaign Platform
   Type System
   ═══════════════════════════════════════════════════════════ */

// ── Platform & Input ──────────────────────────────────────

export type ProductPlatform = "tiktok" | "shopee" | "amazon" | "lazada" | "tiki" | "custom";
export type InputMode = "link" | "form";

// ── Campaign Pipeline Stages ──────────────────────────────

export type CampaignStage =
  | "product_input"
  | "research"
  | "content_generation"
  | "qa_gate"
  | "final_output"
  | "user_review"
  | "package"
  | "deploy";

export const CAMPAIGN_STAGES: { id: CampaignStage; label: string; shortLabel: string; index: number }[] = [
  { id: "product_input", label: "NHẬP.SẢN_PHẨM", shortLabel: "NHẬP", index: 0 },
  { id: "research", label: "PHÂN_TÍCH.NGHIÊN_CỨU", shortLabel: "NGHIÊN CỨU", index: 1 },
  { id: "content_generation", label: "TẠO.NỘI_DUNG", shortLabel: "NỘI DUNG", index: 2 },
  { id: "qa_gate", label: "KIỂM_DUYỆT.CHẤT_LƯỢNG", shortLabel: "KIỂM DUYỆT", index: 3 },
  { id: "final_output", label: "KẾT_QUẢ.CUỐI_CÙNG", shortLabel: "KẾT QUẢ", index: 4 },
  { id: "user_review", label: "ĐÁNH_GIÁ.TỪ_NGƯỜI_DÙNG", shortLabel: "ĐÁNH GIÁ", index: 5 },
  { id: "package", label: "ĐÓNG_GÓI", shortLabel: "ĐÓNG GÓI", index: 6 },
  { id: "deploy", label: "TRIỂN_KHAI", shortLabel: "TRIỂN_KHAI", index: 7 },
];

export type StageStatus = "locked" | "active" | "processing" | "completed" | "failed";

// ── Product Data ──────────────────────────────────────────

export interface ProductImageItem {
  id: string;
  url: string;
  isCover: boolean;
  name?: string;
  size?: string;
}

export interface TargetAudience {
  gender: "all" | "female" | "male";
  ageGroup: string[];
  painPoints: string[];
  interests: string[];
}

export interface ProductData {
  id?: string;
  name: string;
  brand?: string;
  category: string;
  price: string;
  originalPrice?: string;
  currency: string;
  images: ProductImageItem[];
  description: string;
  usps: string[];
  targetAudience: TargetAudience;
  toneOfVoice: string;
  campaignGoal: string;
  sourceUrl?: string;
  platform?: ProductPlatform;
  rating?: number;
  reviewsCount?: number;
  salesVolume?: string;
}

export interface CrawlSimulationResult {
  title: string;
  brand: string;
  category: string;
  price: string;
  originalPrice?: string;
  currency: string;
  images: string[];
  description: string;
  usps: string[];
  platform: ProductPlatform;
  rating: number;
  reviewsCount: number;
  salesVolume: string;
  suggestedTone: string;
  suggestedGoal: string;
  suggestedTargetAudience: TargetAudience;
}

// ── Product Understanding (Stage 2) ──────────────────────

export interface ProductAnalysis {
  extractedFeatures: string[];
  uspAnalysis: { usp: string; strength: "high" | "medium" | "low" }[];
  currentPositioning: string;
  contentStyleAnalysis: string;
  competitiveAdvantage: string;
  pricePositioning: "budget" | "mid-range" | "premium" | "luxury";
}

// ── Research & Evidence (Stages 3-5) ─────────────────────

export interface ResearchFinding {
  id: string;
  category: "user_history" | "market_trend" | "competitor" | "platform_behavior" | "policy" | "content_pattern";
  title: string;
  description: string;
  sourceUrl: string;
  sourceTitle: string;
  evidence: string;
  confidence: "high" | "medium" | "low";
  timestamp: string;
  platform?: ProductPlatform;
}

export interface UserResearchResult {
  previousProducts: { name: string; platform: string; performance: string }[];
  contentStyle: string;
  visualPreferences: string[];
  campaignPatterns: string[];
}

export interface MarketResearchResult {
  trends: { trend: string; relevance: "high" | "medium" | "low"; source: string }[];
  competitors: { name: string; positioning: string; strength: string; weakness: string }[];
  platformBehavior: { platform: string; insight: string; source: string }[];
  policyWarnings: { platform: string; warning: string; severity: "critical" | "warning" | "info"; source: string }[];
}

// ── Strategy (Stage 6) ───────────────────────────────────

export interface ABTestVariant {
  id: string;
  name: string;
  hypothesis: string;
  approach: string;
  expectedOutcome: string;
}

export interface StrategyOutput {
  targetAudience: TargetAudience;
  customerPainPoints: string[];
  productPositioning: string;
  uniqueSellingProp: string;
  marketAngle: string;
  contentAngle: string;
  campaignConcept: string;
  highLevelPlan: string;
  abTestPlan: ABTestVariant[];
  evidenceBackedReasons: { recommendation: string; evidence: string; sourceId: string }[];
}

// ── Content Generation (Stage 7) ─────────────────────────

export type AssetType = "video_15s" | "video_30s" | "image" | "banner" | "social_creative" | "caption" | "title" | "commerce_copy" | "cta" | "platform_copy";

export interface GeneratedAsset {
  id: string;
  type: AssetType;
  name: string;
  url?: string;
  content?: string;
  platform?: ProductPlatform;
  variant?: string;
  status: "generating" | "ready" | "failed";
}

// ── QA Gate (Stage 8) ────────────────────────────────────

export type QACategory = "internal" | "market" | "user" | "platform_policy" | "source_validation";

export interface QACheck {
  id: string;
  category: QACategory;
  name: string;
  description: string;
  status: "pass" | "fail" | "warning" | "pending";
  details?: string;
  severity: "critical" | "major" | "minor";
}

export interface QAReport {
  checks: QACheck[];
  overallStatus: "passed" | "failed" | "warning";
  passCount: number;
  failCount: number;
  warningCount: number;
  totalCount: number;
  iterationCount: number;
  failedCategories: QACategory[];
}

// ── User Review (Stage 10) ───────────────────────────────

export interface ReviewComment {
  id: string;
  section: string;
  comment: string;
  timestamp: string;
  resolved: boolean;
}

// ── Package (Stage 11) ───────────────────────────────────

export interface PackageFile {
  name: string;
  type: "video" | "image" | "text" | "metadata";
  size: string;
  path: string;
}

export interface CampaignPackage {
  files: PackageFile[];
  totalSize: string;
  createdAt: string;
  campaignName: string;
}

// ── Deployment (Stage 12) ────────────────────────────────

export type DeployPlatform = "tiktok" | "shopee" | "amazon";
export type DeployStatus = "ready" | "deploying" | "deployed" | "failed";

export interface DeploymentAction {
  platform: DeployPlatform;
  status: DeployStatus;
  deployedAt?: string;
  campaignUrl?: string;
}

// ── Performance / Analytics ──────────────────────────────

export interface PerformanceMetrics {
  campaignId: string;
  platform: DeployPlatform;
  ctr: number;
  conversionRate: number;
  engagement: number;
  watchTime?: number;
  sales?: number;
  impressions: number;
  abTestResults?: { variantId: string; performance: number }[];
  collectedAt: string;
}

// ── Campaign Entity ──────────────────────────────────────

export interface Campaign {
  id: string;
  name: string;
  product: ProductData;
  currentStage: CampaignStage;
  stageStatuses: Record<CampaignStage, StageStatus>;
  productAnalysis?: ProductAnalysis;
  userResearch?: UserResearchResult;
  marketResearch?: MarketResearchResult;
  researchFindings: ResearchFinding[];
  strategy?: StrategyOutput;
  generatedAssets: GeneratedAsset[];
  qaReport?: QAReport;
  reviewComments: ReviewComment[];
  campaignPackage?: CampaignPackage;
  deployments: DeploymentAction[];
  performance?: PerformanceMetrics[];
  createdAt: string;
  updatedAt: string;
}

// ── Persisted Campaign API ───────────────────────────────

export type PersistedCampaignStatus = "draft" | "researching" | "researched" | "failed";

export interface PersistedCampaign {
  id: string;
  name: string;
  description: string | null;
  status: PersistedCampaignStatus;
  research_input: Record<string, unknown> | null;
  research_result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignListItem {
  id: string;
  name: string;
  description: string | null;
  status: PersistedCampaignStatus;
  has_research_result: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCampaignInput {
  id?: string;
  name: string;
  description?: string | null;
}

export interface UpdateCampaignInput {
  name?: string;
  description?: string | null;
  status?: PersistedCampaignStatus;
}
