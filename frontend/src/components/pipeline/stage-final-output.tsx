"use client";

import * as React from "react";
import { BarChart3, Check, Copy, Eye, ExternalLink, FlaskConical, ShieldAlert, ShieldCheck,
  Image as ImageIcon, MessageSquareText, PackageCheck, Play, Route,
  Rocket, Sparkles, Target, Video,
} from "lucide-react";
import { toast } from "sonner";
import type { ResearchCampaignPlan, ResearchInput } from "@/types/research";
import type { VerifyChecklistResponseData } from "@/types/qa_checklist";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { StagePackage } from "./stage-package";
import { StageDeploy } from "./stage-deploy";
import { ProductPdpPreview } from "./product-pdp-preview";

interface Props {
  plan?: ResearchCampaignPlan | null;
  input?: ResearchInput;
  /** CampaignOutputDTO JSON (snake_case) produced by the content-generation stage. */
  campaignOutput?: Record<string, unknown> | null;
  /** Real QA result from POST /verify-checklist, surfaced from the QA gate stage. */
  qaResult?: VerifyChecklistResponseData | null;
}

const fallbackPlan = {
  angle: "Cà phê đậm vị Robusta Buôn Ma Thuột chuẩn Việt — pha nhanh tiện lợi cho ngày bận rộn.",
  audience: "Dân văn phòng, sinh viên 18–34 tuổi và người yêu thích cà phê Việt vị đậm.",
  message: "Vị đậm chuẩn Việt, tiện lợi mỗi ngày — ưu đãi mua 3 tặng 1 trong mùa 9.9.",
  benefits: ["Pha nhanh, tiện mang theo", "Vị đậm Robusta Buôn Ma Thuột", "Hộp 50 gói tiết kiệm", "Ưu đãi mua 3 tặng 1"],
};

const commerceCopy = {
  title: "Cà phê hòa tan Trung Nguyên G7 3in1 – Hộp 50 gói, đậm vị Robusta Việt Nam",
  description: "Khởi đầu ngày mới nhanh gọn với G7 3in1. Công thức tiện lợi kết hợp vị cà phê Robusta đậm đà, phù hợp tại nhà, văn phòng hoặc mang theo khi di chuyển.",
  bullets: ["Cà phê hòa tan 3in1 pha nhanh", "Vị đậm Robusta Buôn Ma Thuột", "Hộp 50 gói tiện dùng dài ngày", "Phù hợp dùng hằng ngày hoặc làm quà"],
  caption: "Buổi sáng bận rộn vẫn có cà phê đậm vị chuẩn Việt. Pha nhanh G7 3in1 và săn ưu đãi mua 3 tặng 1 dịp 9.9!",
  promotion: "SALE 9.9 · MUA 3 TẶNG 1",
  hooks: ["Pha nhanh, bật mood ngày mới", "Đậm vị Việt trong từng ngụm", "50 gói – tiện lợi dài lâu"],
};

const deliverables = [
  ["package", "Tải xuống", "1 file ZIP"],
  ["positioning", "Định vị sản phẩm", "1 góc chiến dịch"],
  ["routes", "Phương án quảng cáo", "2 hướng A/B"],
  ["testing", "Kế hoạch A/B", "Mục tiêu · biến test · chỉ số"],
  ["learning", "Bài học hiệu suất", "Cách đọc kết quả & hành động"],
  ["video", "Video ngắn", "1 prototype · 9:16"],
  ["images", "Hình ảnh sản phẩm", "4 tài sản sàn TMĐT"],
  ["copy", "Nội dung bán hàng", "6 nhóm nội dung"],
] as const;

function SectionTitle({ icon: Icon, index, title, subtitle }: { icon: React.ElementType; index: string; title: string; subtitle: string }) {
  return <div className="flex items-start gap-3 border-b border-foreground/10 pb-3"><div className="h-8 w-8 border border-[#35ea52]/30 bg-[#35ea52]/10 flex items-center justify-center shrink-0"><Icon className="h-4 w-4 text-[#35ea52]" /></div><div><div className="flex items-center gap-2"><span className="text-[10px] font-mono text-[#35ea52]">{index}</span><h2 className="text-sm font-display font-bold tracking-wider text-foreground">{title}</h2></div><p className="text-xs text-foreground/35 mt-1">{subtitle}</p></div></div>;
}

function ReadyBadge({ optional = false }: { optional?: boolean }) {
  void optional;
  return null;
}

// Compact QA notification: instead of dumping every issue inline in the
// final report (which reads as overwhelming), this fires one toast bubble
// when the result comes in and renders a small pill that expands to the
// full issue list only when the user asks for it.
function QaNotificationBubble({ qaResult }: { qaResult: VerifyChecklistResponseData }) {
  const [expanded, setExpanded] = React.useState(false);
  const notifiedIteration = React.useRef<number | null>(null);
  const hasIssues = qaResult.issues.length > 0;

  React.useEffect(() => {
    if (notifiedIteration.current === qaResult.iteration) return;
    notifiedIteration.current = qaResult.iteration;
    if (hasIssues) {
      toast.warning(`QA: ${qaResult.issues.length} lưu ý nhỏ trên gói chiến dịch`, {
        description: "Chỉ là gợi ý — không chặn tiến trình. Xem chi tiết trong phần QA & POLICY GATE.",
      });
    } else {
      toast.success("QA & Policy Gate: đã vượt qua", {
        description: `Không có lưu ý nào từ AI (lần kiểm tra ${qaResult.iteration}).`,
      });
    }
  }, [qaResult.iteration, hasIssues, qaResult.issues.length]);

  return (
    <section id="final-qa" className="scroll-mt-4">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className={`w-full flex items-center gap-3 border p-3 text-left transition-colors ${
          hasIssues
            ? "border-amber-500/30 bg-amber-500/[0.04] hover:bg-amber-500/[0.07]"
            : "border-[#35ea52]/30 bg-[#35ea52]/[0.04] hover:bg-[#35ea52]/[0.07]"
        }`}
      >
        {hasIssues ? (
          <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0" />
        ) : (
          <ShieldCheck className="h-5 w-5 text-[#35ea52] shrink-0" />
        )}
        <span className="flex-1 text-xs font-mono">
          {hasIssues ? (
            <span className="text-amber-400 font-bold">
              QA & POLICY GATE — {qaResult.issues.length} lưu ý (lần kiểm tra {qaResult.iteration})
            </span>
          ) : (
            <span className="text-[#35ea52] font-bold">QA & POLICY GATE — Đã vượt qua</span>
          )}
        </span>
        <span className="text-[10px] font-mono text-foreground/35">{expanded ? "ẨN" : "XEM"}</span>
      </button>

      {expanded && (
        <div className="border border-t-0 border-foreground/10 bg-background p-4 animate-in fade-in duration-200">
          {hasIssues ? (
            <ul className="space-y-1.5">
              {qaResult.issues.map((issue) => (
                <li key={issue.rule_id} className="text-xs font-mono text-amber-400/90">
                  <span className="font-bold">{issue.rule_id}</span> — {issue.message}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs font-mono text-foreground/50">
              Không có lưu ý nào từ AI trên gói chiến dịch này (lần kiểm tra {qaResult.iteration}).
            </p>
          )}
        </div>
      )}
    </section>
  );
}

export const StageFinalOutput: React.FC<Props> = ({ plan, input, campaignOutput, qaResult }) => {
  const positioning = plan?.product_positioning;
  const angle = positioning?.main_campaign_angle.decision ?? fallbackPlan.angle;
  const audience = positioning?.target_audience.decision ?? fallbackPlan.audience;
  const message = positioning?.key_selling_message.decision ?? fallbackPlan.message;
  const benefits = positioning?.benefit_hierarchy.map(item => item.benefit) ?? fallbackPlan.benefits;
  const routes = plan?.creative_routes ?? [];
  const citationUrls = [...new Set([
    ...(plan?.source_summary.sources.map((source) => source.url) ?? []),
    ...routes.flatMap((route) => route.evidence.map((item) => item.source_url).filter((url): url is string => Boolean(url))),
  ])];
  const citationNumbers = new Map(citationUrls.map((url, index) => [url, index + 1]));
  const sourceTitles = new Map(plan?.source_summary.sources.map((source) => [source.url, source.title]) ?? []);

  // Prefer real generated commerce copy from the content-generation stage
  // (CampaignOutputDTO shape) when available; fall back to the static mock.
  const dtoCommerceCopy = campaignOutput?.commerce_copy as
    | { product_title?: string; product_description?: string; listing_bullet_points?: string[]; ad_caption?: string; promotion_copy?: string; short_hook_lines?: string[] }
    | undefined;
  const resolvedCommerceCopy = {
    title: dtoCommerceCopy?.product_title ?? commerceCopy.title,
    description: dtoCommerceCopy?.product_description ?? commerceCopy.description,
    bullets: dtoCommerceCopy?.listing_bullet_points ?? commerceCopy.bullets,
    caption: dtoCommerceCopy?.ad_caption ?? commerceCopy.caption,
    promotion: dtoCommerceCopy?.promotion_copy ?? commerceCopy.promotion,
    hooks: dtoCommerceCopy?.short_hook_lines ?? commerceCopy.hooks,
  };

  const copyAll = async () => {
    await navigator.clipboard.writeText([angle, audience, message, resolvedCommerceCopy.title, resolvedCommerceCopy.description, resolvedCommerceCopy.caption].join("\n\n"));
    toast.success("Đã sao chép nội dung chính của chiến dịch.");
  };

  const productName = input?.product_brief.product_name || "G7 3IN1";
  const platforms = input?.audience_brief.platforms.slice(0, 3) ?? ["TikTok Shop", "Shopee", "Tmall"];
  const pdpImages = [...(input?.brand_kit.product_photos ?? []), ...(input?.brand_kit.existing_product_visuals ?? [])]
    .map((image) => image.includes("/") || image.startsWith("data:") || image.startsWith("blob:")
      ? image
      : `/sample-data/05-trung-nguyen-g7/${image}`);
  const pdpPrice = input?.product_brief.price ?? null;
  const pdpPromotion = input?.product_brief.promotion ?? resolvedCommerceCopy.promotion;

  return <div className="space-y-6 h-full overflow-y-auto pr-1 pb-8 scroll-smooth">
    <header className="relative overflow-hidden border border-[#35ea52]/30 bg-[#35ea52]/[0.035] p-5 lg:p-7">
      <div className="absolute inset-0 dot-grid opacity-20 pointer-events-none" />
      <div className="relative">
        <div className="space-y-3"><div className="inline-flex items-center gap-2 text-[10px] font-mono text-[#35ea52] tracking-[0.18em]"><PackageCheck className="h-4 w-4" /> GÓI CHIẾN DỊCH HOÀN CHỈNH</div><h1 className="text-2xl lg:text-3xl font-display font-bold text-foreground tracking-wide">{productName}</h1><p className="text-sm text-foreground/50 max-w-3xl leading-relaxed">Một trang duy nhất để kiểm tra chiến lược, tài sản sáng tạo, nội dung bán hàng và kế hoạch đo lường trước khi triển khai.</p><div className="flex flex-wrap gap-2 pt-1">{platforms.map(platform => <span key={platform} className="px-2.5 py-1 border border-foreground/15 text-[10px] font-mono text-foreground/55">{platform.toUpperCase()}</span>)}</div></div>
      </div>
    </header>

    <section id="final-package" className="scroll-mt-4 flex items-center gap-4 border border-foreground/10 p-4">
      <div className="flex items-center gap-3 shrink-0">
        <div className="h-8 w-8 border border-[#35ea52]/30 bg-[#35ea52]/10 flex items-center justify-center">
          <PackageCheck className="h-4 w-4 text-[#35ea52]" />
        </div>
        <h2 className="text-sm font-display font-bold tracking-wider text-foreground">TẢI XUỐNG</h2>
      </div>
      <StagePackage />
    </section>

    <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-foreground/10 border border-foreground/10" aria-label="Tóm tắt campaign brief"><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">SẢN PHẨM / NGÀNH HÀNG</p><p className="text-xs text-foreground/65 mt-1.5">{input?.product_brief.category || "F&B · Cà phê hòa tan"}</p></div><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">THỊ TRƯỜNG</p><p className="text-xs text-foreground/65 mt-1.5">{input?.product_brief.target_market.slice(0, 3).join(" · ") || "Trung Quốc · Đông Nam Á"}</p></div><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">ƯU ĐÃI</p><p className="text-xs text-foreground/65 mt-1.5">{input?.product_brief.promotion || "Không có ưu đãi"}</p></div><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">MỤC TIÊU</p><p className="text-xs text-foreground/65 mt-1.5">{input?.market_signal.campaign_objectives.join(" · ") || "Nhận biết · Chuyển đổi"}</p></div></section>

    {qaResult && (
      <QaNotificationBubble qaResult={qaResult} />
    )}

    <div className="grid grid-cols-1 xl:grid-cols-[230px_minmax(0,1fr)] gap-6 items-start">
      <aside className="xl:sticky xl:top-0 border border-foreground/10 bg-background p-4 space-y-4"><div><p className="text-xs font-mono font-bold tracking-wider text-foreground">KIỂM TRA NHANH</p><p className="text-[10px] text-foreground/30 mt-1">Đối chiếu yêu cầu đầu bài</p></div><nav className="space-y-1">{deliverables.map(([id, label, count], index) => <a key={id} href={`#final-${id}`} className="group flex items-center gap-2.5 p-2 hover:bg-foreground/[0.04]"><span className="h-5 w-5 rounded-full bg-[#35ea52]/10 border border-[#35ea52]/25 flex items-center justify-center"><Check className="h-3 w-3 text-[#35ea52]" /></span><span className="min-w-0 flex-1"><span className="block text-[11px] text-foreground/65 group-hover:text-foreground">{index + 1}. {label}</span><span className="block text-[9px] text-foreground/30 truncate">{count}</span></span></a>)}</nav><button type="button" onClick={() => void copyAll()} className="w-full inline-flex items-center justify-center gap-2 px-3 py-2.5 border border-foreground/20 text-[10px] font-mono text-foreground/60 hover:border-[#35ea52]/40 hover:text-[#35ea52]"><Copy className="h-3.5 w-3.5" /> SAO CHÉP NỘI DUNG CHÍNH</button></aside>

      <main className="space-y-6 min-w-0">
        <section id="final-positioning" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={Target} index="01" title="ĐỊNH VỊ SẢN PHẨM" subtitle="Góc chiến dịch, khách hàng, thông điệp và thứ tự lợi ích" /><ReadyBadge /></div><div className="grid grid-cols-1 lg:grid-cols-3 gap-3"><div className="lg:col-span-2 p-4 border border-[#35ea52]/20 bg-[#35ea52]/[0.025]"><p className="text-[10px] font-mono text-[#35ea52] mb-2">GÓC CHIẾN DỊCH CHÍNH</p><p className="text-base font-semibold leading-relaxed text-foreground">{angle}</p></div><div className="p-4 border border-foreground/10"><p className="text-[10px] font-mono text-foreground/35 mb-2">KHÁCH HÀNG MỤC TIÊU</p><p className="text-sm text-foreground/65 leading-relaxed">{audience}</p></div><div className="lg:col-span-2 p-4 border border-foreground/10"><p className="text-[10px] font-mono text-foreground/35 mb-2">THÔNG ĐIỆP BÁN HÀNG</p><p className="text-sm text-foreground/70 leading-relaxed">{message}</p></div><div className="p-4 border border-foreground/10"><p className="text-[10px] font-mono text-foreground/35 mb-2">THỨ TỰ LỢI ÍCH</p><ol className="space-y-1.5">{benefits.slice(0, 4).map((benefit, index) => <li key={benefit} className="flex gap-2 text-xs text-foreground/60"><span className="text-[#35ea52] font-mono">{index + 1}</span><span>{benefit}</span></li>)}</ol></div></div></section>

        <section id="final-routes" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5">
          <div className="flex justify-between gap-3"><SectionTitle icon={Route} index="02" title="HAI PHƯƠNG ÁN QUẢNG CÁO" subtitle="Hai hướng riêng biệt để chạy thử A/B, kèm nguồn tham khảo" /><ReadyBadge /></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {[0, 1].map(index => {
              const route = routes[index];
              const citedEvidence = route?.evidence.filter((item) => item.source_url) ?? [];
              return <article key={index} className="border border-foreground/10 overflow-hidden">
                <div className={`px-4 py-3 flex items-center justify-between ${index === 0 ? "bg-[#35ea52]/10" : "bg-foreground/[0.04]"}`}><strong className="text-xs font-mono text-foreground">PHƯƠNG ÁN {index === 0 ? "A" : "B"}</strong><span className="text-[9px] font-mono text-foreground/35">{route?.suggested_platform_usage.join(" · ") || (index === 0 ? "TIKTOK SHOP" : "SHOPEE")}</span></div>
                <div className="p-4 space-y-4">
                  <div><p className="text-[9px] font-mono text-foreground/30">HOOK</p><p className="text-sm font-semibold mt-1">{route?.hook_idea || (index === 0 ? "Buổi sáng bận rộn? Pha nhanh vị đậm chuẩn Việt." : "Đặc sản Việt Nam — uống một ngụm là nhớ.")} {citedEvidence.map((item) => { const number = citationNumbers.get(item.source_url!)!; return <a key={`hook-${number}`} href={item.source_url!} target="_blank" rel="noreferrer" className="text-[10px] align-super text-[#35ea52] hover:underline">[{number}]</a>; })}</p></div>
                  <div><p className="text-[9px] font-mono text-foreground/30">HƯỚNG HÌNH ẢNH</p><p className="text-xs text-foreground/55 mt-1 leading-relaxed">{route?.visual_direction || (index === 0 ? "Nhịp nhanh, bối cảnh bàn làm việc buổi sáng, cận cảnh pha cà phê." : "Tông đỏ–đen cao cấp, sản phẩm bên cánh đồng cà phê Buôn Ma Thuột.")}</p></div>
                  <div><p className="text-[9px] font-mono text-foreground/30">GÓC THÔNG ĐIỆP</p><p className="text-xs text-foreground/55 mt-1 leading-relaxed">{route?.message_angle || (index === 0 ? "Tiện lợi cho nhịp sống nhanh." : "Vị đậm và bản sắc cà phê Việt.")}</p></div>
                  <div className="p-3 border border-[#35ea52]/15 bg-[#35ea52]/[0.025] space-y-3"><div><p className="text-[9px] font-mono text-[#35ea52]">MỤC TIÊU THỬ NGHIỆM</p><p className="text-xs text-foreground/60 mt-1">{route?.test_objective || "Đo mức độ phản hồi của khách hàng với góc truyền thông này."}</p></div><div><p className="text-[9px] font-mono text-[#35ea52]">KẾ HOẠCH THỬ NGHIỆM</p><p className="text-xs text-foreground/60 mt-1">{route?.testing_plan || "Chạy song song với phương án còn lại, giữ cùng ngân sách và so sánh CTR, CVR."}</p></div></div>
                  <div className="pt-3 border-t border-foreground/10">
                    <p className="text-[9px] font-mono text-foreground/35 mb-2">NGUỒN THAM KHẢO & CITATION</p>
                    {citedEvidence.length ? <div className="space-y-2">{citedEvidence.map((item, evidenceIndex) => { const number = citationNumbers.get(item.source_url!)!; return <a key={`${item.source_url}-${evidenceIndex}`} href={item.source_url!} target="_blank" rel="noreferrer" className="flex items-start gap-2 p-2.5 border border-foreground/10 bg-foreground/[0.02] hover:border-[#35ea52]/40 group"><span className="text-[10px] font-mono font-bold text-[#35ea52]">[{number}]</span><span className="min-w-0 flex-1"><span className="block text-[11px] font-medium text-foreground/70 group-hover:text-foreground truncate">{sourceTitles.get(item.source_url!) || new URL(item.source_url!).hostname.replace(/^www\./, "")}</span><span className="block text-[10px] text-foreground/40 mt-1 leading-relaxed">{item.detail}</span><span className="block text-[9px] font-mono text-foreground/25 mt-1 truncate">{item.source_url}</span></span><ExternalLink className="h-3.5 w-3.5 text-foreground/30 group-hover:text-[#35ea52] shrink-0" /></a>; })}</div> : <p className="text-[10px] text-foreground/35">Phương án này hiện dựa trên brief sản phẩm; chưa có nguồn bên ngoài để trích dẫn.</p>}
                  </div>
                </div>
              </article>;
            })}
          </div>
        </section>

        <section id="final-testing" className="scroll-mt-4 border border-[#35ea52]/20 bg-[#35ea52]/[0.015] p-5 space-y-5">
          <div className="flex justify-between gap-3"><SectionTitle icon={FlaskConical} index="03" title="KẾ HOẠCH THỬ NGHIỆM A/B" subtitle="So sánh hai giả thuyết trong cùng điều kiện để biết hướng nào nên được ưu tiên" /><ReadyBadge /></div>
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_52px_1fr] gap-3 items-stretch">
            {[0, 1].map((index) => <React.Fragment key={index}>
              {index === 1 && <div className="hidden lg:flex items-center justify-center"><span className="h-10 w-10 rounded-full border border-foreground/20 bg-background flex items-center justify-center text-[10px] font-mono font-bold text-foreground/50">VS</span></div>}
              <article className={`p-4 border space-y-4 ${index === 0 ? "border-[#35ea52]/30 bg-[#35ea52]/[0.035]" : "border-blue-400/20 bg-blue-400/[0.025]"}`}>
                <div className="flex items-center justify-between"><span className={`px-2 py-1 text-[9px] font-mono font-bold ${index === 0 ? "bg-[#35ea52] text-black" : "bg-blue-400 text-black"}`}>PHƯƠNG ÁN {index === 0 ? "A" : "B"}</span><span className="text-[9px] font-mono text-foreground/30">{routes[index]?.route_name || `ROUTE ${index === 0 ? "A" : "B"}`}</span></div>
                <div><p className="text-[9px] font-mono text-foreground/30">MỤC TIÊU CẦN XÁC NHẬN</p><p className="text-sm font-semibold text-foreground/75 leading-relaxed mt-1">{routes[index]?.test_objective || "Đo mức độ phản hồi của khách hàng với góc truyền thông này."}</p></div>
                <div className="p-3 border border-foreground/10 bg-background/60"><p className="text-[9px] font-mono text-[#35ea52]">TEST GÌ · CHẠY NHƯ THẾ NÀO · ĐO GÌ</p><p className="text-xs text-foreground/55 leading-relaxed mt-2">{routes[index]?.testing_plan || "Chỉ thay đổi hook và góc thông điệp; giữ cùng ngân sách, tệp khách hàng và ưu đãi; so sánh CTR và CVR."}</p></div>
              </article>
            </React.Fragment>)}
          </div>
          <div className="border border-foreground/10 bg-background p-4"><p className="text-[10px] font-mono font-bold text-foreground/65 mb-3">CÁCH SỬ DỤNG KẾ HOẠCH</p><ol className="grid grid-cols-1 md:grid-cols-4 gap-3">{[["01", "Giữ điều kiện giống nhau", "Cùng ngân sách, tệp khách hàng, ưu đãi và thời gian chạy."], ["02", "Chỉ đổi biến cần test", "Dùng đúng hook, hình ảnh hoặc thông điệp được nêu trong từng phương án."], ["03", "Đọc cùng bộ chỉ số", "So sánh CTR để đo thu hút và CVR để đo khả năng tạo đơn."], ["04", "Chọn và học", "Giữ hướng thắng; ghi lại động lực mua để tối ưu vòng tiếp theo."]].map(([number, title, text]) => <li key={number} className="flex gap-3"><span className="text-[10px] font-mono text-[#35ea52]">{number}</span><span><strong className="block text-[11px] text-foreground/70">{title}</strong><span className="block text-[10px] text-foreground/35 leading-relaxed mt-1">{text}</span></span></li>)}</ol></div>
        </section>

        <section id="final-learning" className="scroll-mt-4 border border-blue-400/15 bg-blue-400/[0.02] p-5 space-y-5">
          <div className="flex justify-between gap-3"><SectionTitle icon={BarChart3} index="04" title="BÀI HỌC HIỆU SUẤT" subtitle="Biến kết quả A/B thành quyết định rõ ràng cho vòng tối ưu tiếp theo" /><ReadyBadge optional /></div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">{[["GIỮ LẠI", "Thông điệp và hình ảnh của phương án thắng", "Ghi rõ yếu tố tạo CTR/CVR tốt hơn."], ["ĐIỀU CHỈNH", "Hook, CTA hoặc thumbnail chưa đạt", "Chỉ sửa một biến trong mỗi vòng tiếp theo."], ["DỪNG", "Claim rủi ro hoặc hướng không tạo chuyển đổi", "Không tiếp tục tăng ngân sách cho hướng thua."], ["THỬ TIẾP", "Ưu đãi, CTA và hình ảnh bìa", "Dùng bài học vòng này làm giả thuyết mới."]].map(([label, title, text], index) => <article key={label} className="p-4 border border-blue-400/10 bg-background"><div className="flex items-center justify-between"><p className="text-[9px] font-mono text-blue-300">{label}</p><span className="text-[9px] font-mono text-foreground/20">0{index + 1}</span></div><p className="text-xs font-semibold text-foreground/65 mt-3">{title}</p><p className="text-[10px] text-foreground/35 leading-relaxed mt-2">{text}</p></article>)}</div>
          <div className="flex flex-col md:flex-row gap-3 text-[10px] font-mono"><span className="flex-1 p-3 border border-foreground/10 text-foreground/45"><strong className="text-[#35ea52]">CTR cao, CVR thấp:</strong> quảng cáo thu hút nhưng trang bán hàng hoặc ưu đãi chưa thuyết phục.</span><span className="flex-1 p-3 border border-foreground/10 text-foreground/45"><strong className="text-[#35ea52]">CTR và CVR cùng cao:</strong> ưu tiên phương án này để mở rộng ngân sách.</span></div>
        </section>

        <section className="scroll-mt-4 border border-[#35ea52]/20 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={Rocket} index="" title="ĐĂNG LÊN NỀN TẢNG" subtitle="Triển khai phương án quảng cáo lên TikTok Shop, Shopee, Taobao và Tmall" /><ReadyBadge /></div><StageDeploy /></section>

        <section id="final-video" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={Video} index="03" title="VIDEO QUẢNG CÁO NGẮN" subtitle="Tối thiểu 1 video hoặc prototype · 15–30 giây · khung dọc 9:16" /><ReadyBadge /></div><div className="grid grid-cols-[120px_1fr] sm:grid-cols-[150px_1fr] gap-5 items-center"><div className="aspect-[9/16] border border-[#35ea52]/25 bg-gradient-to-b from-red-950/60 to-black relative flex items-center justify-center overflow-hidden"><div className="absolute inset-0 dot-grid opacity-30" /><button type="button" aria-label="Phát video prototype" className="relative h-12 w-12 rounded-full bg-[#35ea52] text-black flex items-center justify-center hover:scale-105 transition-transform"><Play className="h-5 w-5 fill-current ml-0.5" /></button><span className="absolute top-2 right-2 px-1.5 py-0.5 bg-black/70 text-[8px] font-mono text-white">9:16</span></div><div className="space-y-4"><div><h3 className="font-semibold text-foreground">G7_Morning_Ritual_9x16.mp4</h3><p className="text-xs text-foreground/40 mt-1">Prototype quảng cáo ngắn · 22 giây · 1080 × 1920</p></div><div className="grid grid-cols-2 gap-2 text-[10px] font-mono"><span className="p-2 border border-foreground/10 text-foreground/50">MỞ ĐẦU 0–3S</span><span className="p-2 border border-foreground/10 text-foreground/50">DEMO 4–14S</span><span className="p-2 border border-foreground/10 text-foreground/50">LỢI ÍCH 15–18S</span><span className="p-2 border border-foreground/10 text-foreground/50">CTA 19–22S</span></div><div className="flex gap-2"><span className="px-2 py-1 border border-[#35ea52]/20 text-[9px] text-[#35ea52]">SEEDANCE 2.5</span><span className="px-2 py-1 border border-foreground/10 text-[9px] text-foreground/40">BẢN CẮT 1:1 TÙY CHỌN</span></div></div></div></section>

        <section id="final-images" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={ImageIcon} index="04" title="BỘ HÌNH ẢNH SẢN PHẨM" subtitle="4 hình ảnh sẵn sàng cho gian hàng và chiến dịch" /><div className="flex items-center gap-2 shrink-0"><Dialog><DialogTrigger className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-sm bg-[#ee4d2d] text-white text-xs font-bold hover:bg-[#d83f24]"><Eye className="h-3.5 w-3.5" /> PREVIEW TRANG SẢN PHẨM</DialogTrigger><DialogContent className="sm:max-w-5xl max-h-[92vh] overflow-y-auto"><DialogTitle className="text-neutral-900">Xem trước trang sản phẩm</DialogTitle><ProductPdpPreview productName={productName} images={pdpImages} price={pdpPrice} promotion={pdpPromotion} description={resolvedCommerceCopy.description} bullets={resolvedCommerceCopy.bullets} angle={angle} /></DialogContent></Dialog><ReadyBadge /></div></div><div className="grid grid-cols-2 lg:grid-cols-4 gap-3">{[["ẢNH HERO", "Sản phẩm nổi bật"], ["CHI TIẾT SKU", "Thông tin & bao bì"], ["ẢNH CHIẾN DỊCH", "Bộ sưu tập 9.9"], ["ẢNH BÌA SÀN", "Thumbnail chuyển đổi"]].map(([label, note], index) => <article key={label} className="border border-foreground/10 p-2"><div className={`aspect-square relative flex items-center justify-center overflow-hidden ${index % 2 ? "bg-gradient-to-br from-neutral-900 to-red-950" : "bg-gradient-to-br from-red-950 to-amber-950"}`}><div className="absolute inset-0 dot-grid opacity-30" /><div className="relative text-center"><PackageCheck className="h-8 w-8 text-[#35ea52]/70 mx-auto" /><span className="text-[8px] font-mono text-white/40 mt-2 block">G7 · 3IN1</span></div><span className="absolute top-2 left-2 text-[8px] font-mono text-white/50">0{index + 1}</span></div><div className="p-2"><p className="text-[10px] font-mono font-bold text-[#35ea52]">{label}</p><p className="text-[10px] text-foreground/35 mt-1">{note}</p></div></article>)}</div><div className="flex items-center gap-2 text-[10px] text-foreground/35"><Sparkles className="h-3.5 w-3.5 text-[#35ea52]" /> Tạo với Seedream 5.0 Pro · đồng nhất màu sắc, logo và bao bì sản phẩm</div></section>

        <section id="final-copy" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={MessageSquareText} index="05" title="NỘI DUNG BÁN HÀNG" subtitle="Tiêu đề, mô tả, bullet, caption, ưu đãi và hook ngắn" /><ReadyBadge /></div><div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><div className="p-4 border border-foreground/10 space-y-4"><div><p className="text-[9px] font-mono text-foreground/30">TIÊU ĐỀ SẢN PHẨM</p><p className="text-sm font-semibold mt-1">{resolvedCommerceCopy.title}</p></div><div><p className="text-[9px] font-mono text-foreground/30">MÔ TẢ SẢN PHẨM</p><p className="text-xs text-foreground/55 leading-relaxed mt-1">{resolvedCommerceCopy.description}</p></div><ul className="space-y-1">{resolvedCommerceCopy.bullets.map(item => <li key={item} className="flex gap-2 text-xs text-foreground/60"><Check className="h-3.5 w-3.5 text-[#35ea52] shrink-0" />{item}</li>)}</ul></div><div className="p-4 border border-foreground/10 space-y-4"><div className="inline-block px-3 py-2 bg-red-500/10 border border-red-500/20 text-red-300 text-sm font-bold">{resolvedCommerceCopy.promotion}</div><div><p className="text-[9px] font-mono text-foreground/30">CAPTION QUẢNG CÁO</p><p className="text-xs text-foreground/60 leading-relaxed mt-1">{resolvedCommerceCopy.caption}</p></div><div><p className="text-[9px] font-mono text-foreground/30 mb-2">HOOK NGẮN</p><div className="flex flex-wrap gap-2">{resolvedCommerceCopy.hooks.map(hook => <span key={hook} className="px-2 py-1 bg-foreground/[0.05] text-[10px] text-foreground/55">{hook}</span>)}</div></div></div></div></section>

      </main>
    </div>
  </div>;
};
