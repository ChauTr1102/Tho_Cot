"use client";

import * as React from "react";
import { CheckCircle2, Loader2, MessageSquare, Send, ShieldAlert, ThumbsUp } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { api, ApiError } from "@/lib/api";
import type { QACheckedItem, VerifyChecklistResponseData } from "@/types/qa_checklist";

interface Props {
  /** CampaignInputDTO JSON (snake_case), matching backend/app/schemas/campaign_dto.py. */
  campaignInput?: Record<string, unknown>;
  /** CampaignOutputDTO JSON (snake_case), matching backend/app/schemas/campaign_dto.py. */
  campaignOutput?: Record<string, unknown>;
  iteration?: number;
}

// Fallback sample data so this stage is runnable end-to-end before the
// earlier pipeline stages (positioning / content generation) are wired up
// to real generation state. Pass real campaignInput/campaignOutput props
// once those stages produce actual data. Kept in sync with stage-qa-gate.tsx.
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

// Items are "ticked" one at a time (staggered) purely for the visual effect
// of watching AI check them off, rather than popping in all at once.
const TICK_STAGGER_MS = 350;

export const StageUserReview: React.FC<Props> = ({ campaignInput, campaignOutput, iteration = 1 }) => {
  const [state, setState] = React.useState<"checking" | "done" | "error">("checking");
  const [result, setResult] = React.useState<VerifyChecklistResponseData | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [tickedCount, setTickedCount] = React.useState(0);
  const [feedback, setFeedback] = React.useState("");
  const [isSending, setIsSending] = React.useState(false);
  const [isApproved, setIsApproved] = React.useState(false);

  const runVerify = React.useCallback(() => {
    setState("checking");
    setError(null);
    setTickedCount(0);
    api
      .verifyChecklist({
        campaign_input: campaignInput ?? SAMPLE_CAMPAIGN_INPUT,
        campaign_output: campaignOutput ?? SAMPLE_CAMPAIGN_OUTPUT,
        iteration,
      })
      .then((res) => {
        setResult(res.data);
        setState("done");
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Không thể kết nối AI kiểm tra checklist.");
        setState("error");
      });
  }, [campaignInput, campaignOutput, iteration]);

  React.useEffect(() => {
    runVerify();
  }, [runVerify]);

  // Reveal each checked item one by one so the user watches AI "tick" them
  // off in sequence, instead of the whole list appearing at once.
  const items: QACheckedItem[] = result?.checked_items ?? [];
  React.useEffect(() => {
    if (state !== "done" || items.length === 0) return;
    setTickedCount(0);
    let i = 0;
    const timer = setInterval(() => {
      i += 1;
      setTickedCount(i);
      if (i >= items.length) clearInterval(timer);
    }, TICK_STAGGER_MS);
    return () => clearInterval(timer);
  }, [state, items.length]);

  const allRevealed = tickedCount >= items.length;
  const attentionItems = items.filter((item) => !item.passed);

  const handleSendFeedback = () => {
    if (!feedback.trim()) return;
    setIsSending(true);
    setTimeout(() => {
      setIsSending(false);
      setFeedback("");
      // Logic để back lại stage trước nếu cần
    }, 1500);
  };

  const handleApprove = () => {
    setIsApproved(true);
  };

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">ĐÁNH GIÁ TỪ NGƯỜI DÙNG</h2>
        <p className="text-sm font-mono text-foreground/40">
          AI đang tự động rà soát checklist duyệt sản phẩm cho bạn. Bạn chỉ cần xem lại và gửi phản hồi nếu muốn chỉnh sửa thêm.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 pr-2 pb-8">
        {/* AI Checklist */}
        <div className="border border-foreground/10 bg-background p-5 space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Checklist Duyệt Sản Phẩm (AI tự kiểm tra)
          </h3>

          {state === "checking" && (
            <div className="flex items-center gap-3 p-4 text-sm font-mono text-foreground/50">
              <Loader2 className="h-4 w-4 animate-spin text-[#35ea52]" />
              AI đang rà soát các tiêu chí, bao gồm bản quyền / sở hữu trí tuệ...
            </div>
          )}

          {state === "error" && (
            <div className="border-l-2 border-amber-500 bg-amber-500/[0.05] p-4 flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0" />
              <div className="space-y-2 flex-1">
                <p className="text-sm font-mono text-foreground/70">{error}</p>
                <button
                  onClick={runVerify}
                  className="px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-mono transition-colors"
                >
                  THỬ LẠI
                </button>
              </div>
            </div>
          )}

          {state === "done" && items.length === 0 && (
            <p className="text-sm font-mono text-foreground/50 p-2">Không có tiêu chí nào để hiển thị.</p>
          )}

          {state === "done" && items.length > 0 && (
            <ul className="space-y-2 text-sm font-mono text-foreground/80">
              {items.map((item, idx) => {
                const revealed = idx < tickedCount;
                return (
                  <li
                    key={item.rule_id}
                    className={`flex items-start gap-3 p-2 border transition-colors duration-300 ${
                      !revealed
                        ? "border-foreground/5 bg-foreground/[0.02] opacity-40"
                        : item.passed
                        ? "border-[#35ea52]/20 bg-[#35ea52]/[0.04]"
                        : "border-amber-500/20 bg-amber-500/[0.04]"
                    }`}
                  >
                    {revealed ? (
                      item.passed ? (
                        <CheckCircle2 className="h-4 w-4 mt-0.5 text-[#35ea52] shrink-0" />
                      ) : (
                        <ShieldAlert className="h-4 w-4 mt-0.5 text-amber-400 shrink-0" />
                      )
                    ) : (
                      <Loader2 className="h-4 w-4 mt-0.5 text-foreground/30 shrink-0 animate-spin" />
                    )}
                    <span className={revealed && item.passed ? "line-through text-foreground/50" : ""}>
                      {item.description}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}

          {state === "done" && allRevealed && attentionItems.length > 0 && (
            <div className="border-l-2 border-amber-500 bg-amber-500/[0.05] p-3 space-y-2">
              <p className="text-xs font-mono text-amber-400 font-bold">
                {attentionItems.length} lưu ý nhỏ để bạn tham khảo — không chặn tiến trình
              </p>
              <ul className="space-y-1">
                {result?.issues.map((issue) => (
                  <li key={issue.rule_id} className="text-xs font-mono text-foreground/60 pl-2">
                    • {issue.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {state === "done" && allRevealed && attentionItems.length === 0 && (
            <div className="border-l-2 border-[#35ea52] bg-[#35ea52]/[0.05] p-3">
              <p className="text-xs font-mono text-[#35ea52] font-bold">
                AI đã tự động tích xong toàn bộ checklist, mọi thứ đều ổn.
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Feedback Form */}
          <div className="border border-foreground/10 bg-foreground/[0.02] p-5 space-y-4">
            <h3 className="text-xs font-mono font-bold text-foreground/70 tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Yêu cầu chỉnh sửa
            </h3>
            <p className="text-[11px] font-mono text-foreground/50">
              Agent sẽ nhận feedback này, quay lại bước Sáng tạo nội dung để chỉnh sửa và tự động sinh lại các tài sản.
            </p>
            <Textarea
              placeholder="VD: Cần đổi tone màu banner Route B sang đỏ sậm hơn. Video Route A thêm hiệu ứng khói rõ hơn..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="bg-background border-foreground/20 text-sm font-mono min-h-[120px] focus:border-[#35ea52]/50"
              disabled={isSending || isApproved}
            />
            <button
              onClick={handleSendFeedback}
              disabled={!feedback.trim() || isSending || isApproved}
              className="w-full flex items-center justify-center gap-2 py-2 border border-foreground/30 bg-background hover:bg-foreground/10 text-xs font-mono font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? (
                <span className="animate-pulse">ĐANG GỬI PHẢN HỒI...</span>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" /> GỬI PHẢN HỒI CHO AGENT
                </>
              )}
            </button>
          </div>

          {/* Approve Panel */}
          <div className="border border-[#35ea52]/20 bg-[#35ea52]/[0.02] p-5 space-y-4 flex flex-col justify-between">
            <div>
              <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-[#35ea52]/20 pb-2 flex items-center gap-2">
                <ThumbsUp className="h-4 w-4" />
                Phê duyệt Chiến dịch
              </h3>
              <p className="text-sm font-mono text-foreground/80 mt-4 leading-relaxed">
                Nếu tất cả các nội dung đã đạt yêu cầu, bạn có thể phê duyệt để chuyển sang bước Đóng gói (Package) & Triển khai (Deploy).
              </p>
            </div>

            {isApproved ? (
              <div className="flex items-center justify-center gap-2 py-3 bg-[#35ea52]/20 text-[#35ea52] border border-[#35ea52]/30 text-xs font-mono font-bold">
                <CheckCircle2 className="h-4 w-4" /> ĐÃ PHÊ DUYỆT
              </div>
            ) : (
              <button
                onClick={handleApprove}
                disabled={isSending}
                className="w-full flex items-center justify-center gap-2 py-3 bg-[#35ea52] text-black hover:bg-[#35ea52]/80 text-xs font-mono font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <CheckCircle2 className="h-4 w-4" /> PHÊ DUYỆT & TIẾP TỤC
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
