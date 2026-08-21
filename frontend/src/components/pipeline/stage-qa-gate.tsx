"use client";

import * as React from "react";
import { AlertTriangle, CheckCircle2, RefreshCw, ShieldAlert } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import type { QAIssue, VerifyChecklistResponseData } from "@/types/qa_checklist";

interface Props {
  /** CampaignInputDTO JSON (snake_case), matching backend/app/schemas/campaign_dto.py. */
  campaignInput?: Record<string, unknown>;
  /** CampaignOutputDTO JSON (snake_case), matching backend/app/schemas/campaign_dto.py. */
  campaignOutput?: Record<string, unknown>;
  iteration?: number;
  /** Called with the verify-checklist response data right after a successful call resolves. */
  onResult?: (result: VerifyChecklistResponseData) => void;
}

// Fallback sample data so this stage is runnable end-to-end before the
// earlier pipeline stages (positioning / content generation) are wired up
// to real generation state. Pass real campaignInput/campaignOutput props
// once those stages produce actual data.
const SAMPLE_CAMPAIGN_INPUT: Record<string, unknown> = {
  product_brief: {
    product_name: "Fizzy Roots Sparkling Tea",
    category: "F&B",
    key_selling_points: ["Zero added sugar", "Made in Vietnam"],
    price_or_promotion: { price: 25000, currency: "VND", promotion: "Buy 4 Get 1 Free" },
    target_market: "Vietnam",
    required_claims: ["zero added sugar", "made in Vietnam"],
    restricted_or_forbidden_claims: ["cures bloating"],
  },
  brand_kit: {
    logo: { path: "./brand_assets/brand_logo.jpg" },
    brand_colors: { primary: "#0E7C61", secondary: "#F4D35E", accent: ["#FFFFFF"], palette: ["#0E7C61"] },
    tone_of_voice: { description: "playful", attributes: ["playful"], do: [], dont: [] },
    product_photos: ["./brand_assets/product_photo_studio.jpg"],
    existing_product_visuals: [],
  },
  audience_brief: { target_customer: "Gen Z", language: "vi", platform: "TikTok Shop", market: "VN" },
  market_signal: {
    trend: "functional beverages", seasonal_moment: null, consumer_pain_point: "sugar guilt",
    search_keyword: ["tra hoa qua khong duong"], competitor_angle: null, campaign_objective: "Drive trial purchases",
  },
  past_campaign_data: {
    enabled: false, ctr: null, cvr: null, roas: null,
    watch_time: { value: null, unit: "seconds" }, add_to_cart_rate: null, comments: [],
    sales_results: { units_sold: null, revenue: null, currency: "VND" },
  },
};

const SAMPLE_CAMPAIGN_OUTPUT: Record<string, unknown> = {
  product_positioning: {
    main_campaign_angle: "Zero added sugar, without the trade-off.",
    target_audience: "Gen Z",
    key_selling_message: "Fizzy Roots solves sugar guilt with zero added sugar, made in Vietnam.",
    product_benefit_hierarchy: ["Zero added sugar", "Made in Vietnam"],
  },
  creative_routes: [
    { name: "Route A", hook_idea: "Problem-agitate-solve", visual_direction: "Close-up shot", message_angle: "Pain-point led", suggested_platform_usage: ["TikTok Shop"] },
    { name: "Route B", hook_idea: "Testimonial", visual_direction: "Studio shot", message_angle: "Trust led", suggested_platform_usage: ["TikTok Shop"] },
  ],
  short_form_video_asset: { generated_video_urls: ["https://example.com/route_a.mp4"], format: "9:16", duration: "20s", additional_cuts: [] },
  product_collection_image_set: {
    product_hero_image: "https://example.com/hero.jpg",
    sku_detail_image: "https://example.com/sku.jpg",
    campaign_collection_image: "https://example.com/collection.jpg",
    marketplace_thumbnail: "https://example.com/thumb.jpg",
  },
  commerce_copy: {
    product_title: "Fizzy Roots Sparkling Tea",
    product_description: "Made with zero added sugar. Made in Vietnam.",
    listing_bullet_points: ["Zero added sugar", "Made in Vietnam"],
    ad_caption: "Zero added sugar, made in Vietnam.",
    promotion_copy: "Buy 4 Get 1 Free",
    short_hook_lines: ["Meet Fizzy Roots."],
  },
  ab_testing_plan: {
    what_to_test: "Hook style", route_a_description: "Pain-point led opener", route_b_description: "Testimonial led opener",
    suggested_success_metrics: ["CTR", "Add-to-cart rate"], expected_learning: "Which hook drives more engagement.",
  },
  performance_learning: null,
};

const REGENERATE_LABEL: Record<string, string> = { plan: "PLAN", asset: "ASSET (ảnh / video / copy)" };

export const StageQAGate: React.FC<Props> = ({ campaignInput, campaignOutput, iteration = 1, onResult }) => {
  const [state, setState] = React.useState<"checking" | "done" | "error">("checking");
  const [result, setResult] = React.useState<VerifyChecklistResponseData | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const runVerify = React.useCallback(() => {
    setState("checking");
    setError(null);
    api
      // Falls back to the local SAMPLE_CAMPAIGN_INPUT/OUTPUT only when no
      // props are supplied at all (e.g. standalone/dev preview usage). The
      // real call site (campaigns/page.tsx) always passes real campaign data.
      .verifyChecklist({
        campaign_input: campaignInput ?? SAMPLE_CAMPAIGN_INPUT,
        campaign_output: campaignOutput ?? SAMPLE_CAMPAIGN_OUTPUT,
        iteration,
      })
      .then((res) => {
        setResult(res.data);
        setState("done");
        if (res.data) onResult?.(res.data);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Không thể kết nối QA checklist backend.");
        setState("error");
      });
  }, [campaignInput, campaignOutput, iteration, onResult]);

  React.useEffect(() => {
    runVerify();
  }, [runVerify]);

  // Group issues by regenerate target for display, purely for readability —
  // does not affect severity (all issues are surfaced as WARNING for now;
  // see backend/app/services/qa_agent/service.py and qa_checklist_service.py).
  const groups = React.useMemo(() => {
    const byTarget = new Map<string, QAIssue[]>();
    for (const issue of result?.issues ?? []) {
      const bucket = byTarget.get(issue.regenerate) ?? [];
      bucket.push(issue);
      byTarget.set(issue.regenerate, bucket);
    }
    return byTarget;
  }, [result]);

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground flex items-center gap-2">
          QA & POLICY GATE
        </h2>
        <p className="text-sm font-mono text-foreground/40">
          AI tự động rà soát các tài sản đã tạo so với brief chiến dịch và gửi vài lưu ý nhỏ để bạn tham khảo trước khi tiếp tục.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6">
        {state === "checking" && (
          // Mocked loading skeleton: the real verify-checklist call can take a
          // few seconds (LLM-backed), and a bare spinner reads as "stuck" /
          // buggy to QA. Render a fake placeholder shaped like the eventual
          // result instead so the stage always looks alive while loading.
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="border-l-2 border-foreground/10 bg-foreground/[0.02] p-4 flex items-start gap-4">
              <RefreshCw className="h-6 w-6 text-[#35ea52] animate-spin shrink-0" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-56" />
                <Skeleton className="h-3 w-full max-w-md" />
                <p className="text-[10px] font-mono text-foreground/30 tracking-widest uppercase pt-1">
                  Đang chạy xác thực QA...
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[0, 1].map((i) => (
                <div key={i} className="border border-foreground/10 bg-background p-4 space-y-3">
                  <Skeleton className="h-3 w-32" />
                  <div className="space-y-3">
                    {[0, 1].map((j) => (
                      <div key={j} className="space-y-1.5">
                        <Skeleton className="h-3 w-40" />
                        <Skeleton className="h-8 w-full" />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="border-l-2 border-amber-500 bg-amber-500/[0.05] p-4 flex items-start gap-4">
            <AlertTriangle className="h-6 w-6 text-amber-400 shrink-0" />
            <div className="space-y-2 flex-1">
              <h3 className="text-[15px] font-mono font-bold text-amber-400">KHÔNG THỂ CHẠY QA CHECKLIST</h3>
              <p className="text-sm font-mono text-foreground/70">{error}</p>
              <button
                onClick={runVerify}
                className="mt-2 px-4 py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-mono transition-colors flex items-center gap-2"
              >
                <RefreshCw className="h-3 w-3" /> THỬ LẠI
              </button>
            </div>
          </div>
        )}

        {state === "done" && result && (
          <>
            {result.issues.length === 0 ? (
              <div className="border-l-2 border-[#35ea52] bg-[#35ea52]/[0.05] p-4 flex items-start gap-4">
                <CheckCircle2 className="h-6 w-6 text-[#35ea52] shrink-0" />
                <div>
                  <h3 className="text-[15px] font-mono font-bold text-[#35ea52]">MỌI THỨ ĐỀU ỔN</h3>
                  <p className="text-sm font-mono text-foreground/70">
                    AI không thấy điểm nào cần lưu ý thêm trên campaign này (lần kiểm tra {result.iteration}). Bạn có thể yên tâm tiếp tục.
                  </p>
                </div>
              </div>
            ) : (
              <div className="border-l-2 border-amber-500 bg-amber-500/[0.05] p-4 flex items-start gap-4">
                <ShieldAlert className="h-6 w-6 text-amber-400 shrink-0" />
                <div className="space-y-2 flex-1">
                  <h3 className="text-[15px] font-mono font-bold text-amber-400">
                    {result.issues.length} LƯU Ý NHỎ ĐỂ BẠN THAM KHẢO
                  </h3>
                  <p className="text-sm font-mono text-foreground/70">
                    AI gợi ý vài điểm có thể cải thiện thêm — đây chỉ là gợi ý, không chặn tiến trình của bạn. Bạn có
                    thể tiếp tục ngay hoặc regenerate lại phần được gợi ý dưới đây nếu muốn.
                  </p>
                  <button
                    onClick={runVerify}
                    className="mt-2 px-4 py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-mono transition-colors flex items-center gap-2"
                  >
                    <RefreshCw className="h-3 w-3" /> KIỂM TRA LẠI
                  </button>
                </div>
              </div>
            )}

            {result.issues.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Array.from(groups.entries()).map(([target, issues]) => (
                  <div key={target} className="border border-foreground/10 bg-background p-4 space-y-3">
                    <span className="text-xs font-mono text-foreground/50 tracking-widest uppercase block border-b border-foreground/5 pb-2">
                      REGENERATE: {REGENERATE_LABEL[target] ?? target.toUpperCase()}
                    </span>
                    <ul className="space-y-3">
                      {issues.map((issue) => (
                        <li key={issue.rule_id} className="space-y-1">
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
                            <span className="text-sm font-mono text-foreground/80 font-bold">{issue.rule_id}</span>
                          </div>
                          <p className="text-xs font-mono text-amber-400/90 pl-5 leading-relaxed bg-amber-500/5 p-2 border border-amber-500/10">
                            {issue.message}
                          </p>
                          <p className="text-[10px] font-mono text-foreground/30 pl-5">field: {issue.field}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
