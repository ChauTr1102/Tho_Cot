"use client";

import * as React from "react";
import {
  BarChart3, Check, Copy, Eye, ExternalLink, FlaskConical,
  Image as ImageIcon, MessageSquareText, PackageCheck, Play, Route,
  Rocket, Sparkles, Target, Video,
} from "lucide-react";
import { toast } from "sonner";
import type { ResearchCampaignPlan, ResearchInput } from "@/types/research";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { StagePackage } from "./stage-package";
import { StageDeploy } from "./stage-deploy";
import { TiktokPdpPreview } from "./tiktok-pdp-preview";

interface Props { plan?: ResearchCampaignPlan | null; input?: ResearchInput }

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
  ["video", "Video ngắn", "1 prototype · 9:16"],
  ["images", "Hình ảnh sản phẩm", "4 tài sản sàn TMĐT"],
  ["copy", "Nội dung bán hàng", "6 nhóm nội dung"],
  ["testing", "Kế hoạch A/B", "Chỉ số & giả thuyết"],
  ["learning", "Bài học hiệu suất", "Bước tối ưu tiếp theo"],
] as const;

function SectionTitle({ icon: Icon, index, title, subtitle }: { icon: React.ElementType; index: string; title: string; subtitle: string }) {
  return <div className="flex items-start gap-3 border-b border-foreground/10 pb-3"><div className="h-8 w-8 border border-[#35ea52]/30 bg-[#35ea52]/10 flex items-center justify-center shrink-0"><Icon className="h-4 w-4 text-[#35ea52]" /></div><div><div className="flex items-center gap-2"><span className="text-[10px] font-mono text-[#35ea52]">{index}</span><h2 className="text-sm font-display font-bold tracking-wider text-foreground">{title}</h2></div><p className="text-xs text-foreground/35 mt-1">{subtitle}</p></div></div>;
}

function ReadyBadge({ optional = false }: { optional?: boolean }) {
  void optional;
  return null;
}

export const StageFinalOutput: React.FC<Props> = ({ plan, input }) => {
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

  const copyAll = async () => {
    await navigator.clipboard.writeText([angle, audience, message, commerceCopy.title, commerceCopy.description, commerceCopy.caption].join("\n\n"));
    toast.success("Đã sao chép nội dung chính của chiến dịch.");
  };

  const productName = input?.product_brief.product_name || "G7 3IN1";
  const platforms = input?.audience_brief.platforms.slice(0, 3) ?? ["TikTok Shop", "Shopee", "Tmall"];
  const pdpImages = [...(input?.brand_kit.product_photos ?? []), ...(input?.brand_kit.existing_product_visuals ?? [])];
  const pdpPrice = input?.product_brief.price ?? null;
  const pdpPromotion = input?.product_brief.promotion ?? commerceCopy.promotion;

  return <div className="space-y-6 h-full overflow-y-auto pr-1 pb-8 scroll-smooth">
    <header className="relative overflow-hidden border border-[#35ea52]/30 bg-[#35ea52]/[0.035] p-5 lg:p-7">
      <div className="absolute inset-0 dot-grid opacity-20 pointer-events-none" />
      <div className="relative">
        <div className="space-y-3"><div className="inline-flex items-center gap-2 text-[10px] font-mono text-[#35ea52] tracking-[0.18em]"><PackageCheck className="h-4 w-4" /> GÓI CHIẾN DỊCH HOÀN CHỈNH</div><h1 className="text-2xl lg:text-3xl font-display font-bold text-foreground tracking-wide">{productName}</h1><p className="text-sm text-foreground/50 max-w-3xl leading-relaxed">Một trang duy nhất để kiểm tra chiến lược, tài sản sáng tạo, nội dung bán hàng và kế hoạch đo lường trước khi triển khai.</p><div className="flex flex-wrap gap-2 pt-1">{platforms.map(platform => <span key={platform} className="px-2.5 py-1 border border-foreground/15 text-[10px] font-mono text-foreground/55">{platform.toUpperCase()}</span>)}</div></div>
      </div>
    </header>

    <section id="final-package" className="scroll-mt-4 border border-foreground/10 p-4 space-y-3"><SectionTitle icon={PackageCheck} index="" title="TẢI XUỐNG" subtitle="Tải toàn bộ chiến dịch trong một file ZIP" /><StagePackage /></section>

    <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-foreground/10 border border-foreground/10" aria-label="Tóm tắt campaign brief"><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">SẢN PHẨM / NGÀNH HÀNG</p><p className="text-xs text-foreground/65 mt-1.5">{input?.product_brief.category || "F&B · Cà phê hòa tan"}</p></div><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">THỊ TRƯỜNG</p><p className="text-xs text-foreground/65 mt-1.5">{input?.product_brief.target_market.slice(0, 3).join(" · ") || "Trung Quốc · Đông Nam Á"}</p></div><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">ƯU ĐÃI</p><p className="text-xs text-foreground/65 mt-1.5">{input?.product_brief.promotion || "Không có ưu đãi"}</p></div><div className="p-3.5 bg-background"><p className="text-[9px] font-mono text-foreground/30">MỤC TIÊU</p><p className="text-xs text-foreground/65 mt-1.5">{input?.market_signal.campaign_objectives.join(" · ") || "Nhận biết · Chuyển đổi"}</p></div></section>

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
                  <div className="pt-3 border-t border-foreground/10">
                    <p className="text-[9px] font-mono text-foreground/35 mb-2">NGUỒN THAM KHẢO & CITATION</p>
                    {citedEvidence.length ? <div className="space-y-2">{citedEvidence.map((item, evidenceIndex) => { const number = citationNumbers.get(item.source_url!)!; return <a key={`${item.source_url}-${evidenceIndex}`} href={item.source_url!} target="_blank" rel="noreferrer" className="flex items-start gap-2 p-2.5 border border-foreground/10 bg-foreground/[0.02] hover:border-[#35ea52]/40 group"><span className="text-[10px] font-mono font-bold text-[#35ea52]">[{number}]</span><span className="min-w-0 flex-1"><span className="block text-[11px] font-medium text-foreground/70 group-hover:text-foreground truncate">{sourceTitles.get(item.source_url!) || new URL(item.source_url!).hostname.replace(/^www\./, "")}</span><span className="block text-[10px] text-foreground/40 mt-1 leading-relaxed">{item.detail}</span><span className="block text-[9px] font-mono text-foreground/25 mt-1 truncate">{item.source_url}</span></span><ExternalLink className="h-3.5 w-3.5 text-foreground/30 group-hover:text-[#35ea52] shrink-0" /></a>; })}</div> : <p className="text-[10px] text-foreground/35">Phương án này hiện dựa trên brief sản phẩm; chưa có nguồn bên ngoài để trích dẫn.</p>}
                  </div>
                </div>
              </article>;
            })}
          </div>
        </section>

        <section className="scroll-mt-4 border border-[#35ea52]/20 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={Rocket} index="" title="ĐĂNG LÊN NỀN TẢNG" subtitle="Triển khai phương án quảng cáo lên TikTok Shop, Shopee, Taobao và Tmall" /><ReadyBadge /></div><StageDeploy /></section>

        <section id="final-video" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={Video} index="03" title="VIDEO QUẢNG CÁO NGẮN" subtitle="Tối thiểu 1 video hoặc prototype · 15–30 giây · khung dọc 9:16" /><ReadyBadge /></div><div className="grid grid-cols-[120px_1fr] sm:grid-cols-[150px_1fr] gap-5 items-center"><div className="aspect-[9/16] border border-[#35ea52]/25 bg-gradient-to-b from-red-950/60 to-black relative flex items-center justify-center overflow-hidden"><div className="absolute inset-0 dot-grid opacity-30" /><button type="button" aria-label="Phát video prototype" className="relative h-12 w-12 rounded-full bg-[#35ea52] text-black flex items-center justify-center hover:scale-105 transition-transform"><Play className="h-5 w-5 fill-current ml-0.5" /></button><span className="absolute top-2 right-2 px-1.5 py-0.5 bg-black/70 text-[8px] font-mono text-white">9:16</span></div><div className="space-y-4"><div><h3 className="font-semibold text-foreground">G7_Morning_Ritual_9x16.mp4</h3><p className="text-xs text-foreground/40 mt-1">Prototype quảng cáo ngắn · 22 giây · 1080 × 1920</p></div><div className="grid grid-cols-2 gap-2 text-[10px] font-mono"><span className="p-2 border border-foreground/10 text-foreground/50">MỞ ĐẦU 0–3S</span><span className="p-2 border border-foreground/10 text-foreground/50">DEMO 4–14S</span><span className="p-2 border border-foreground/10 text-foreground/50">LỢI ÍCH 15–18S</span><span className="p-2 border border-foreground/10 text-foreground/50">CTA 19–22S</span></div><div className="flex gap-2"><span className="px-2 py-1 border border-[#35ea52]/20 text-[9px] text-[#35ea52]">SEEDANCE 2.5</span><span className="px-2 py-1 border border-foreground/10 text-[9px] text-foreground/40">BẢN CẮT 1:1 TÙY CHỌN</span></div></div></div></section>

        <section id="final-images" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={ImageIcon} index="04" title="BỘ HÌNH ẢNH SẢN PHẨM" subtitle="4 hình ảnh sẵn sàng cho gian hàng và chiến dịch" /><div className="flex items-center gap-2 shrink-0"><Dialog><DialogTrigger className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[#35ea52]/30 text-[10px] font-mono text-[#35ea52] hover:bg-[#35ea52]/10"><Eye className="h-3.5 w-3.5" /> XEM TRƯỚC</DialogTrigger><DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto"><DialogTitle>Xem trước trang sản phẩm TikTok Shop</DialogTitle><TiktokPdpPreview productName={productName} images={pdpImages} price={pdpPrice} promotion={pdpPromotion} description={commerceCopy.description} bullets={commerceCopy.bullets} angle={angle} /></DialogContent></Dialog><ReadyBadge /></div></div><div className="grid grid-cols-2 lg:grid-cols-4 gap-3">{[["ẢNH HERO", "Sản phẩm nổi bật"], ["CHI TIẾT SKU", "Thông tin & bao bì"], ["ẢNH CHIẾN DỊCH", "Bộ sưu tập 9.9"], ["ẢNH BÌA SÀN", "Thumbnail chuyển đổi"]].map(([label, note], index) => <article key={label} className="border border-foreground/10 p-2"><div className={`aspect-square relative flex items-center justify-center overflow-hidden ${index % 2 ? "bg-gradient-to-br from-neutral-900 to-red-950" : "bg-gradient-to-br from-red-950 to-amber-950"}`}><div className="absolute inset-0 dot-grid opacity-30" /><div className="relative text-center"><PackageCheck className="h-8 w-8 text-[#35ea52]/70 mx-auto" /><span className="text-[8px] font-mono text-white/40 mt-2 block">G7 · 3IN1</span></div><span className="absolute top-2 left-2 text-[8px] font-mono text-white/50">0{index + 1}</span></div><div className="p-2"><p className="text-[10px] font-mono font-bold text-[#35ea52]">{label}</p><p className="text-[10px] text-foreground/35 mt-1">{note}</p></div></article>)}</div><div className="flex items-center gap-2 text-[10px] text-foreground/35"><Sparkles className="h-3.5 w-3.5 text-[#35ea52]" /> Tạo với Seedream 5.0 Pro · đồng nhất màu sắc, logo và bao bì sản phẩm</div></section>

        <section id="final-copy" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={MessageSquareText} index="05" title="NỘI DUNG BÁN HÀNG" subtitle="Tiêu đề, mô tả, bullet, caption, ưu đãi và hook ngắn" /><ReadyBadge /></div><div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><div className="p-4 border border-foreground/10 space-y-4"><div><p className="text-[9px] font-mono text-foreground/30">TIÊU ĐỀ SẢN PHẨM</p><p className="text-sm font-semibold mt-1">{commerceCopy.title}</p></div><div><p className="text-[9px] font-mono text-foreground/30">MÔ TẢ SẢN PHẨM</p><p className="text-xs text-foreground/55 leading-relaxed mt-1">{commerceCopy.description}</p></div><ul className="space-y-1">{commerceCopy.bullets.map(item => <li key={item} className="flex gap-2 text-xs text-foreground/60"><Check className="h-3.5 w-3.5 text-[#35ea52] shrink-0" />{item}</li>)}</ul></div><div className="p-4 border border-foreground/10 space-y-4"><div className="inline-block px-3 py-2 bg-red-500/10 border border-red-500/20 text-red-300 text-sm font-bold">{commerceCopy.promotion}</div><div><p className="text-[9px] font-mono text-foreground/30">CAPTION QUẢNG CÁO</p><p className="text-xs text-foreground/60 leading-relaxed mt-1">{commerceCopy.caption}</p></div><div><p className="text-[9px] font-mono text-foreground/30 mb-2">HOOK NGẮN</p><div className="flex flex-wrap gap-2">{commerceCopy.hooks.map(hook => <span key={hook} className="px-2 py-1 bg-foreground/[0.05] text-[10px] text-foreground/55">{hook}</span>)}</div></div></div></div></section>

        <section id="final-testing" className="scroll-mt-4 border border-foreground/10 p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={FlaskConical} index="06" title="KẾ HOẠCH THỬ NGHIỆM A/B" subtitle="Biết rõ thử gì, đo gì và học được gì" /><ReadyBadge /></div><div className="grid grid-cols-1 md:grid-cols-4 gap-px bg-foreground/10 border border-foreground/10"><div className="p-4 bg-background"><p className="text-[9px] font-mono text-[#35ea52]">GIẢ THUYẾT</p><p className="text-xs text-foreground/60 mt-2">Hook tiện lợi tạo nhiều lượt nhấp hơn hook đặc sản Việt.</p></div><div className="p-4 bg-background"><p className="text-[9px] font-mono text-[#35ea52]">A SO VỚI B</p><p className="text-xs text-foreground/60 mt-2">A: Nỗi đau buổi sáng<br />B: Hương vị & bản sắc</p></div><div className="p-4 bg-background"><p className="text-[9px] font-mono text-[#35ea52]">CHỈ SỐ THÀNH CÔNG</p><p className="text-xs text-foreground/60 mt-2">CTR · CVR · thời gian xem · thêm vào giỏ</p></div><div className="p-4 bg-background"><p className="text-[9px] font-mono text-[#35ea52]">KẾT QUẢ CẦN HỌC</p><p className="text-xs text-foreground/60 mt-2">Động lực mua mạnh nhất theo từng kênh và thị trường.</p></div></div></section>

        <section id="final-learning" className="scroll-mt-4 border border-blue-400/15 bg-blue-400/[0.025] p-5 space-y-5"><div className="flex justify-between gap-3"><SectionTitle icon={BarChart3} index="07" title="BÀI HỌC HIỆU SUẤT" subtitle="Khuyến nghị tối ưu sau khi có dữ liệu chiến dịch" /><ReadyBadge optional /></div><div className="grid grid-cols-2 lg:grid-cols-4 gap-3">{[["GIỮ LẠI", "Thông điệp vị đậm và hình ảnh bao bì rõ ràng"], ["THAY ĐỔI", "Rút ngắn mở đầu nếu tỷ lệ xem 3 giây thấp"], ["DỪNG", "Claim không có nguồn hoặc không tạo chuyển đổi"], ["THỬ TIẾP", "Ưu đãi, CTA và thumbnail theo từng sàn"]].map(([label, text]) => <div key={label} className="p-3 border border-blue-400/10 bg-background"><p className="text-[9px] font-mono text-blue-300">{label}</p><p className="text-xs text-foreground/55 leading-relaxed mt-2">{text}</p></div>)}</div></section>

      </main>
    </div>
  </div>;
};
