"use client";

import * as React from "react";
import Image from "next/image";
import {
  BarChart3, Check, ChevronRight, Download, ExternalLink, FileText,
  FlaskConical, Image as ImageIcon, LayoutTemplate, Maximize2, PackageCheck, Rocket,
  ShieldAlert, ShieldCheck, Sparkles, Target, Video,
} from "lucide-react";
import type { ResearchCampaignPlan, ResearchEvidence, ResearchInput } from "@/types/research";
import type { VerifyChecklistResponseData } from "@/types/qa_checklist";
import { fetchSavedResult, mediaUrl, type SavedAsset } from "@/lib/studio-draft";
import { ProductPdpPreview } from "./product-pdp-preview";
import { PlatformVideoPlayer } from "./platform-video-player";
import { StagePackage } from "./stage-package";
import { StageDeploy } from "./stage-deploy";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

interface Props {
  plan?: ResearchCampaignPlan | null;
  input?: ResearchInput;
  campaignOutput?: Record<string, unknown> | null;
  qaResult?: VerifyChecklistResponseData | null;
}

type InspectorSection = "overview" | "copy" | "testing" | "assets" | "qa";

const unavailable = "Chưa có dữ liệu từ chiến dịch.";

function cleanOptionName(value: string | undefined, index: number) {
  if (!value) return `Phương án ${index === 0 ? "A" : "B"}`;
  return value.replace(/^\s*(route|phương án)\s*[ab]\s*[:\-–—]?\s*/i, "").trim() || `Phương án ${index === 0 ? "A" : "B"}`;
}

const sections: Array<{ id: InspectorSection; label: string; icon: React.ElementType }> = [
  { id: "overview", label: "Tổng quan", icon: Target },
  { id: "copy", label: "Nội dung", icon: FileText },
  { id: "testing", label: "A/B Test", icon: FlaskConical },
  { id: "assets", label: "Tài sản", icon: ImageIcon },
  { id: "qa", label: "QA & Triển khai", icon: ShieldCheck },
];

function InspectorTitle({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="border-b border-foreground/10 pb-4 font-sans"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#35ea52]">{eyebrow}</p><h2 className="mt-1.5 text-xl font-bold text-foreground">{title}</h2><p className="mt-1 text-xs leading-relaxed text-foreground/45">{description}</p></div>;
}

function Field({ label, children, highlight = false }: { label: string; children: React.ReactNode; highlight?: boolean }) {
  return <div className={`border p-4 font-sans ${highlight ? "border-[#35ea52]/25 bg-[#35ea52]/[0.035]" : "border-foreground/10 bg-foreground/[0.018]"}`}><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-foreground/50">{label}</p><div className="mt-2 text-sm leading-relaxed text-foreground/80">{children}</div></div>;
}

const evidenceLabels: Record<ResearchEvidence["basis"], string> = {
  product_brief: "Thông tin từ brief",
  supplied_source: "Tài liệu được cung cấp",
  external_research: "Nghiên cứu thị trường",
  general_marketing_knowledge: "Kiến thức marketing",
  assumption: "Giả định cần xác minh",
};

function cleanEvidenceDetail(value: string) {
  return value.replace(/^\s*\[[^\]]+\]\s*/, "").trim();
}

function EvidenceBlock({ rationale, evidence, citationNumbers, sourceTitles }: { rationale?: string; evidence?: ResearchEvidence[]; citationNumbers: Map<string, number>; sourceTitles: Map<string, string>; compact?: boolean }) {
  const items = evidence ?? [];
  if (!rationale && items.length === 0) return null;
  return <details className="group mt-4 border-t border-foreground/10 pt-3 font-sans">
    <summary className="flex w-fit cursor-pointer list-none items-center gap-2 text-[13px] font-medium text-foreground/55 transition-colors hover:text-foreground/85 [&::-webkit-details-marker]:hidden">
      <ChevronRight className="h-4 w-4 shrink-0 transition-transform group-open:rotate-90" />
      <span>Xem căn cứ</span>
    </summary>
    <div className="ml-2 mt-4 space-y-5 border-l border-foreground/12 pl-5 pr-2">
      {rationale ? <div>
        <p className="text-[13px] font-semibold text-foreground/80">Vì sao chọn hướng này</p>
        <p className="mt-2 text-[14px] leading-7 text-foreground/65">{rationale}</p>
      </div> : null}
      {items.map((item, index) => {
        const number = item.source_url ? citationNumbers.get(item.source_url) : undefined;
        return <div key={`${item.detail}-${index}`} className="space-y-2">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="text-[13px] font-semibold text-foreground/70">{evidenceLabels[item.basis]}</span>
            {number ? <a href={item.source_url!} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()} className="inline-flex items-center gap-1.5 text-[13px] font-semibold leading-5 text-[#35ea52] hover:underline">[{number}] {sourceTitles.get(item.source_url!) || new URL(item.source_url!).hostname.replace(/^www\./, "")}<ExternalLink className="h-3.5 w-3.5" /></a> : null}
          </div>
          <p className="text-[14px] leading-7 text-foreground/55">{cleanEvidenceDetail(item.detail)}</p>
        </div>;
      })}
    </div>
  </details>;
}

export function FinalOutputWorkspace({ plan, input, campaignOutput, qaResult }: Props) {
  const [section, setSection] = React.useState<InspectorSection>("overview");
  const [routeIndex, setRouteIndex] = React.useState<0 | 1>(0);
  const [mobilePane, setMobilePane] = React.useState<"preview" | "content">("preview");
  const [savedAssets, setSavedAssets] = React.useState<SavedAsset[]>([]);
  const [viewingAsset, setViewingAsset] = React.useState<{ url: string; label: string } | null>(null);
  const campaignId = input?.campaign_id;

  React.useEffect(() => {
    if (!campaignId) return;
    let active = true;
    void fetchSavedResult(campaignId, true).then((result) => {
      if (active) setSavedAssets(result?.assets ?? []);
    });
    return () => { active = false; };
  }, [campaignId]);
  const positioning = plan?.product_positioning;
  const routes = plan?.creative_routes ?? [];
  const selectedRoute = routes[routeIndex];
  // The posters the studio rendered per creative route, keyed "A" / "B". Two
  // hypotheses printed above no artwork is a plan; the pair is what makes it an
  // experiment somebody can run. Empty for a kit built before the studio varied
  // artwork by route, and the cards simply omit the image in that case.
  const abVariants = (campaignOutput?.ab_variants ?? {}) as Record<string, string>;
  const mediaBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api").replace(/\/api\/?$/, "");
  const dto = campaignOutput?.commerce_copy as { product_title?: string; product_description?: string; listing_bullet_points?: string[]; ad_caption?: string; promotion_copy?: string; short_hook_lines?: string[] } | undefined;
  const productName = input?.product_brief.product_name || "Sản phẩm chưa có tên";
  const briefPoints = input?.product_brief.key_selling_points ?? [];
  const copy = {
    title: dto?.product_title || productName,
    description: dto?.product_description || briefPoints.join(". "),
    bullets: dto?.listing_bullet_points?.length ? dto.listing_bullet_points : briefPoints,
    caption: dto?.ad_caption || "",
    promotion: dto?.promotion_copy || input?.product_brief.promotion || "",
    hooks: dto?.short_hook_lines ?? [],
  };
  const angle = selectedRoute?.message_angle || positioning?.main_campaign_angle.decision || unavailable;
  const audience = positioning?.target_audience.decision || input?.audience_brief.target_customer.join(" · ") || unavailable;
  const message = positioning?.key_selling_message.decision || briefPoints.join(" · ") || unavailable;
  const inputImages = [...(input?.brand_kit.product_photos ?? []), ...(input?.brand_kit.existing_product_visuals ?? [])].map((image) => // A bare filename used to be resolved against the G7 sample folder, so any
      // campaign whose photos were named `product_01.jpg` previewed G7's coffee
      // regardless of what it was selling. A name with no path is not a URL and
      // is dropped instead of being pointed at a stranger's product.
      image.includes("/") || image.startsWith("data:") || image.startsWith("blob:") ? image : "").filter(Boolean);
  const generatedImages = savedAssets.filter((asset) => asset.kind === "image");
  const tiktokImages = generatedImages.filter((asset) => asset.platform === "tiktok_shop").map((asset) => mediaUrl(asset.url));
  const shopeeImages = generatedImages.filter((asset) => asset.platform === "shopee").map((asset) => mediaUrl(asset.url));
  const images = generatedImages.length ? generatedImages.map((asset) => mediaUrl(asset.url)) : inputImages;
  const savedVideos = savedAssets.filter((asset) => asset.kind === "video");
  const preferredVideo = savedVideos.find((asset) => asset.name === "master_final.mp4") ?? savedVideos.find((asset) => asset.name === "master_15s.mp4") ?? savedVideos[0];
  const outputVideos = ((campaignOutput?.short_form_video_asset as { generated_video_urls?: string[] } | undefined)?.generated_video_urls ?? []).filter((url) => {
    try {
      const parsed = new URL(url, "http://localhost");
      return parsed.hostname !== "example.com" && !parsed.pathname.toLowerCase().includes("/mock/");
    } catch {
      return false;
    }
  });
  const videos = preferredVideo ? [mediaUrl(preferredVideo.url)] : outputVideos.map(mediaUrl);
  const assetImage = (matcher: (name: string) => boolean) => {
    const asset = savedAssets.find((item) => item.kind === "image" && matcher(item.name.toLowerCase()));
    return asset ? mediaUrl(asset.url) : undefined;
  };
  const featuredAssets = [
    { label: "Ảnh hero", image: assetImage((name) => name === "hero.jpg") ?? images[0] },
    { label: "Chi tiết SKU", image: assetImage((name) => name.includes("detail")) ?? shopeeImages[1] ?? images[1] },
    { label: "Ảnh chiến dịch", image: assetImage((name) => name.includes("sale") || name.includes("lifestyle")) ?? tiktokImages[1] ?? images[2] },
    { label: "Ảnh bìa sàn", image: assetImage((name) => name.includes("cover") || name.includes("main_image")) ?? tiktokImages[0] ?? shopeeImages[0] ?? images[3] },
  ];
  const qaPassed = !qaResult || qaResult.issues.length === 0;
  const citationUrls = [...new Set([...(plan?.source_summary.sources.map((source) => source.url) ?? []), ...(positioning ? [positioning.main_campaign_angle, positioning.target_audience, positioning.key_selling_message].flatMap((decision) => decision.evidence.map((item) => item.source_url).filter((url): url is string => Boolean(url))) : []), ...routes.flatMap((route) => route.evidence.map((item) => item.source_url).filter((url): url is string => Boolean(url)))])];
  const citationNumbers = new Map(citationUrls.map((url, index) => [url, index + 1]));
  const sourceTitles = new Map(plan?.source_summary.sources.map((source) => [source.url, source.title]) ?? []);

  const preview = <div className="bg-neutral-100 p-3 lg:p-5"><ProductPdpPreview productName={copy.title} category={input?.product_brief.category} images={images} tiktokImages={tiktokImages.length ? tiktokImages : images} shopeeImages={shopeeImages.length ? shopeeImages : images} videos={videos} price={input?.product_brief.price ?? null} promotion={input?.product_brief.promotion ?? copy.promotion} description={copy.description} caption={copy.caption} bullets={copy.bullets} angle={angle} /></div>;

  const inspector = <div className="flex min-h-full flex-col bg-background">
    <header className="border-b border-foreground/10 p-4 lg:p-5">
      <div className="flex items-start justify-between gap-4"><div><div className="flex items-center gap-2 text-[9px] font-mono tracking-[0.18em] text-[#35ea52]"><PackageCheck className="h-3.5 w-3.5" /> GÓI CHIẾN DỊCH HOÀN CHỈNH</div><h1 className="mt-2 text-xl font-display font-bold text-foreground">{productName}</h1></div>{!qaPassed ? <div className="shrink-0 border border-amber-400/30 px-2 py-1 text-[9px] font-mono text-amber-400">{qaResult?.issues.length} LƯU Ý</div> : null}</div>
      <div className="mt-4 flex gap-1 border border-foreground/10 bg-foreground/[0.025] p-1">{[0, 1].map((index) => <button key={index} type="button" onClick={() => setRouteIndex(index as 0 | 1)} className={`flex-1 px-3 py-2 text-[10px] font-mono font-bold transition-colors ${routeIndex === index ? "bg-[#35ea52] text-black" : "text-foreground/40 hover:text-foreground"}`}>PHƯƠNG ÁN {index === 0 ? "A" : "B"}<span className="ml-2 hidden font-sans font-normal opacity-60 xl:inline">{cleanOptionName(routes[index]?.route_name, index)}</span></button>)}</div>
    </header>
    <nav className="flex shrink-0 overflow-x-auto border-b border-foreground/10 px-2" aria-label="Nội dung báo cáo">{sections.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => setSection(id)} className={`inline-flex shrink-0 items-center gap-1.5 border-b-2 px-3 py-3 text-[10px] font-medium transition-colors ${section === id ? "border-[#35ea52] text-foreground" : "border-transparent text-foreground/35 hover:text-foreground/70"}`}><Icon className="h-3.5 w-3.5" />{label}</button>)}</nav>
    <div className="flex-1 p-4 lg:p-5">
      {section === "overview" && <div className="space-y-4 font-sans"><InspectorTitle eyebrow="01 · Chiến lược" title="Tổng quan chiến dịch" description="Các quyết định cốt lõi đang điều khiển nội dung và bản xem trước, kèm bằng chứng kiểm chứng." /><Field label="Góc chiến dịch đang xem" highlight>{angle}<EvidenceBlock rationale={selectedRoute?.rationale || positioning?.main_campaign_angle.rationale} evidence={selectedRoute?.evidence || positioning?.main_campaign_angle.evidence} citationNumbers={citationNumbers} sourceTitles={sourceTitles} /></Field><Field label="Khách hàng mục tiêu">{audience}<EvidenceBlock rationale={positioning?.target_audience.rationale} evidence={positioning?.target_audience.evidence} citationNumbers={citationNumbers} sourceTitles={sourceTitles} /></Field><Field label="Thông điệp bán hàng">{message}<EvidenceBlock rationale={positioning?.key_selling_message.rationale} evidence={positioning?.key_selling_message.evidence} citationNumbers={citationNumbers} sourceTitles={sourceTitles} /></Field><Field label="Lợi ích ưu tiên"><ol className="divide-y divide-foreground/10">{(positioning?.benefit_hierarchy ?? []).slice(0, 4).map((item, index) => <li key={item.benefit} className="py-4 first:pt-0 last:pb-0"><div className="flex items-start gap-3"><span className="w-6 shrink-0 text-sm font-semibold text-[#35ea52]">{String(index + 1).padStart(2, "0")}</span><span className="text-sm font-medium leading-6 text-foreground/75">{item.benefit}</span></div><div className="ml-9"><EvidenceBlock rationale={item.rationale} evidence={item.evidence} citationNumbers={citationNumbers} sourceTitles={sourceTitles} /></div></li>)}</ol></Field></div>}
      {section === "copy" && <div className="space-y-4"><InspectorTitle eyebrow="02 · Commerce copy" title="Nội dung sản phẩm" description="Nội dung dùng trong trang sản phẩm và quảng cáo theo nền tảng." /><Field label="Tiêu đề sản phẩm">{copy.title}</Field><Field label="Mô tả sản phẩm"><p className="text-xs leading-6">{copy.description}</p></Field><Field label="Bullet points"><ul className="space-y-2">{copy.bullets.map((item) => <li key={item} className="flex gap-2 text-xs"><Check className="h-3.5 w-3.5 shrink-0 text-[#35ea52]" />{item}</li>)}</ul></Field><Field label="Caption quảng cáo"><p className="text-xs leading-6">{copy.caption}</p></Field><Field label="Ưu đãi"><span className="inline-block border border-red-400/25 bg-red-400/10 px-2 py-1 text-xs font-bold text-red-300">{copy.promotion}</span></Field></div>}
      {section === "testing" && <div className="space-y-4"><InspectorTitle eyebrow="03 · Experiment" title="Phương án A/B" description="Chọn phương án ở đầu bảng để đồng bộ nội dung, preview và evidence bên trái." />{[0, 1].map((index) => { const route = routes[index]; const active = routeIndex === index; return <article key={index} onClick={() => setRouteIndex(index as 0 | 1)} className={`w-full cursor-pointer border p-4 text-left ${active ? "border-[#35ea52]/40 bg-[#35ea52]/[0.04]" : "border-foreground/10"}`}><div className="flex items-center justify-between"><span className={`px-2 py-1 text-[9px] font-mono font-bold ${active ? "bg-[#35ea52] text-black" : "bg-foreground/10 text-foreground/50"}`}>PHƯƠNG ÁN {index === 0 ? "A" : "B"}</span>{active && <span className="text-[9px] font-mono text-[#35ea52]">ĐANG PREVIEW</span>}</div><h3 className="mt-3 text-sm font-bold text-foreground">{cleanOptionName(route?.route_name, index)}</h3><p className="mt-2 text-xs leading-5 text-foreground/50">{route?.hook_idea || copy.hooks[index] || unavailable}</p>{abVariants[index === 0 ? "A" : "B"] ? <a href={`${mediaBase}${abVariants[index === 0 ? "A" : "B"]}`} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()} className="mt-3 block overflow-hidden border border-foreground/10">{/* eslint-disable-next-line @next/next/no-img-element */}<img src={`${mediaBase}${abVariants[index === 0 ? "A" : "B"]}`} alt={`Poster phương án ${index === 0 ? "A" : "B"}`} loading="lazy" className="aspect-[4/5] w-full bg-foreground/5 object-cover" /></a> : null}<div className="mt-4 grid gap-3 sm:grid-cols-2"><div><p className="text-[8px] font-mono text-foreground/30">GIẢ THUYẾT</p><p className="mt-1 text-[10px] leading-5 text-foreground/55">{route?.test_objective || unavailable}</p></div><div><p className="text-[8px] font-mono text-foreground/30">CÁCH ĐO</p><p className="mt-1 text-[10px] leading-5 text-foreground/55">{route?.testing_plan || unavailable}</p></div></div><EvidenceBlock rationale={route?.rationale} evidence={route?.evidence} citationNumbers={citationNumbers} sourceTitles={sourceTitles} /></article>; })}<Field label="Quy tắc quyết định"><div className="grid gap-2 text-xs sm:grid-cols-2"><span><b className="text-[#35ea52]">CTR cao, CVR thấp:</b> tối ưu trang bán hàng.</span><span><b className="text-[#35ea52]">CTR và CVR cao:</b> mở rộng phương án thắng.</span></div></Field></div>}
      {section === "assets" && <div className="space-y-5">
        <InspectorTitle eyebrow="04 · Creative assets" title="Tài sản chiến dịch" description="Ảnh và video thật đã tạo cho từng nền tảng, sẵn sàng xem trước trước khi bàn giao." />
        <section>
          <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold text-foreground">Bộ ảnh chính</h3><span className="text-[10px] text-foreground/40">4 tài sản</span></div>
          <div className="grid grid-cols-2 gap-3">{featuredAssets.map((asset, index) => <article key={asset.label} className="overflow-hidden border border-foreground/10 bg-foreground/[0.02] p-2">
            <button type="button" disabled={!asset.image} onClick={() => asset.image && setViewingAsset({ url: asset.image, label: asset.label })} aria-label={`Xem đầy đủ ${asset.label}`} className="group relative block aspect-square w-full overflow-hidden bg-neutral-950 disabled:cursor-default">{asset.image ? <><Image src={asset.image} alt={asset.label} fill unoptimized className="object-cover transition-transform duration-300 group-hover:scale-[1.03]" /><span className="absolute bottom-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/65 text-white opacity-0 transition-opacity group-hover:opacity-100"><Maximize2 className="h-4 w-4" /></span></> : <ImageIcon className="absolute inset-0 m-auto h-7 w-7 text-[#35ea52]/50" />}</button>
            <div className="flex items-center gap-2 px-1 pb-0.5 pt-2.5"><span className="text-[10px] font-semibold text-[#35ea52]">{String(index + 1).padStart(2, "0")}</span><p className="text-[11px] font-semibold text-foreground/75">{asset.label}</p></div>
          </article>)}</div>
        </section>
        {videos[0] ? <Field label="Video quảng cáo">
          <div className="mx-auto w-full max-w-[320px] overflow-hidden rounded-lg border border-foreground/10 bg-black shadow-xl">
            <div className="aspect-[9/16]"><PlatformVideoPlayer src={videos[0]} poster={tiktokImages[0] ?? shopeeImages[0] ?? images[0]} title={productName} caption={copy.caption} platform="tiktok" /></div>
          </div>
          <div className="mt-3 flex items-center justify-between gap-3 border-t border-foreground/10 pt-3 text-xs">
            <span className="inline-flex min-w-0 items-center gap-2 text-foreground/75"><Video className="h-4 w-4 shrink-0 text-[#35ea52]" /><b className="truncate">{preferredVideo?.name ?? "Video chiến dịch"}</b></span>
            <span className="shrink-0 text-[10px] text-foreground/40">Video dọc · Có thể phát và tua</span>
          </div>
        </Field> : <Field label="Video quảng cáo"><p className="text-xs text-foreground/45">Campaign này chưa có video được tạo.</p></Field>}

        {[{ label: "TikTok Shop", assets: tiktokImages, accent: "#fe2c55" }, { label: "Shopee", assets: shopeeImages, accent: "#ee4d2d" }].map((group) => group.assets.length ? <section key={group.label} className="border border-foreground/10 p-4">
          <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold text-foreground">{group.label}</h3><span className="text-[10px] text-foreground/40">{group.assets.length} ảnh</span></div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{group.assets.map((image, index) => <article key={image} className="overflow-hidden border border-foreground/10 bg-foreground/[0.02]"><button type="button" onClick={() => setViewingAsset({ url: image, label: `${group.label} · Ảnh ${index + 1}` })} aria-label={`Xem đầy đủ ảnh ${index + 1} của ${group.label}`} className="group relative block aspect-square w-full overflow-hidden bg-neutral-950"><Image src={image} alt={`${group.label} ${index + 1}`} fill unoptimized className="object-cover transition-transform duration-300 group-hover:scale-[1.03]" /><span className="absolute bottom-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/65 text-white opacity-0 transition-opacity group-hover:opacity-100"><Maximize2 className="h-4 w-4" /></span></button><p className="truncate px-2 py-2 text-[10px] font-medium text-foreground/55">Ảnh {String(index + 1).padStart(2, "0")}</p><div className="h-0.5" style={{ backgroundColor: group.accent }} /></article>)}</div>
        </section> : null)}

        {!generatedImages.length && images.length ? <section className="border border-foreground/10 p-4"><h3 className="mb-3 text-sm font-semibold">Ảnh sản phẩm được cung cấp</h3><div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{images.map((image, index) => <button type="button" key={image} onClick={() => setViewingAsset({ url: image, label: `Ảnh sản phẩm ${index + 1}` })} aria-label={`Xem đầy đủ ảnh sản phẩm ${index + 1}`} className="group relative aspect-square overflow-hidden border border-foreground/10"><Image src={image} alt={`Ảnh sản phẩm ${index + 1}`} fill unoptimized className="object-cover transition-transform duration-300 group-hover:scale-[1.03]" /><span className="absolute bottom-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/65 text-white opacity-0 transition-opacity group-hover:opacity-100"><Maximize2 className="h-4 w-4" /></span></button>)}</div></section> : null}
        <p className="flex items-center gap-2 text-[11px] text-foreground/40"><Sparkles className="h-3.5 w-3.5 text-[#35ea52]" /> Tài sản được tải trực tiếp từ thư mục media của campaign hiện tại.</p>
      </div>}
      {section === "qa" && <div className="space-y-4"><InspectorTitle eyebrow="05 · Handoff" title="QA & triển khai" description="Kiểm tra độ sẵn sàng, tải gói hoặc đưa nội dung lên nền tảng." /><div className={`flex items-start gap-3 border p-4 ${qaPassed ? "border-[#35ea52]/25 bg-[#35ea52]/[0.035]" : "border-amber-400/25 bg-amber-400/[0.035]"}`}>{qaPassed ? <ShieldCheck className="h-5 w-5 shrink-0 text-[#35ea52]" /> : <ShieldAlert className="h-5 w-5 shrink-0 text-amber-400" />}<div><b className={`text-xs ${qaPassed ? "text-[#35ea52]" : "text-amber-400"}`}>{qaPassed ? "ĐÃ SẴN SÀNG TRIỂN KHAI" : `${qaResult?.issues.length} LƯU Ý CẦN XEM`}</b><p className="mt-1 text-[10px] leading-5 text-foreground/45">{qaPassed ? "Nội dung và tài sản bắt buộc đã vượt qua kiểm tra." : qaResult?.issues[0]?.message}</p></div></div>{qaResult?.issues.map((issue) => <Field key={issue.rule_id} label={issue.rule_id}>{issue.message}</Field>)}<div className="border border-foreground/10 p-4"><div className="mb-3 flex items-center gap-2"><Download className="h-4 w-4 text-[#35ea52]" /><b className="text-xs">Gói bàn giao</b></div><StagePackage /></div><div className="border border-foreground/10 p-4"><div className="mb-3 flex items-center gap-2"><Rocket className="h-4 w-4 text-[#35ea52]" /><b className="text-xs">Đăng lên nền tảng</b></div><StageDeploy /></div></div>}
    </div>
    <footer className="flex shrink-0 items-center border-t border-foreground/10 bg-background p-3"><button type="button" onClick={() => setSection("qa")} className="inline-flex h-10 w-full items-center justify-center gap-2 bg-[#35ea52] px-4 text-[10px] font-mono font-bold text-black"><Rocket className="h-3.5 w-3.5" /> KIỂM TRA & TRIỂN KHAI <ChevronRight className="h-3.5 w-3.5" /></button></footer>
  </div>;

  return <div className="flex min-h-[760px] flex-col border border-foreground/10 bg-background">
    <div className="grid grid-cols-2 border-b border-foreground/10 bg-background p-1 lg:hidden"><button type="button" onClick={() => setMobilePane("preview")} className={`flex items-center justify-center gap-2 py-2 text-[10px] font-mono ${mobilePane === "preview" ? "bg-[#35ea52] font-bold text-black" : "text-foreground/45"}`}><LayoutTemplate className="h-3.5 w-3.5" /> PREVIEW</button><button type="button" onClick={() => setMobilePane("content")} className={`flex items-center justify-center gap-2 py-2 text-[10px] font-mono ${mobilePane === "content" ? "bg-[#35ea52] font-bold text-black" : "text-foreground/45"}`}><BarChart3 className="h-3.5 w-3.5" /> NỘI DUNG</button></div>
    <div className="min-h-0 flex-1 lg:grid lg:grid-cols-[minmax(0,1fr)_680px]">
      <section className={`self-start border-l border-foreground/10 ${mobilePane === "preview" ? "block" : "hidden"} lg:order-2 lg:block`}>{preview}</section>
      <section className={`min-h-full ${mobilePane === "content" ? "block" : "hidden"} lg:order-1 lg:block`}>{inspector}</section>
    </div>
    <Dialog open={Boolean(viewingAsset)} onOpenChange={(open) => { if (!open) setViewingAsset(null); }}>
      <DialogContent className="h-[92vh] max-w-[min(96vw,1200px)] grid-rows-[auto_minmax(0,1fr)] overflow-hidden rounded-lg bg-black p-3 text-white sm:max-w-[min(96vw,1200px)]">
        <DialogTitle className="pr-12 text-sm font-semibold text-white">{viewingAsset?.label ?? "Xem đầy đủ hình ảnh"}</DialogTitle>
        <div className="relative min-h-0 flex-1 overflow-hidden rounded bg-neutral-950">
          {viewingAsset ? <Image src={viewingAsset.url} alt={viewingAsset.label} fill unoptimized sizes="96vw" className="object-contain" /> : null}
        </div>
      </DialogContent>
    </Dialog>
  </div>;
}
