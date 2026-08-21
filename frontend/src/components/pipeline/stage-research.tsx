"use client";

import * as React from "react";
import { AlertTriangle, CheckCircle2, ExternalLink, Lightbulb, Route, ShieldCheck, Target } from "lucide-react";
import { AgentLoading } from "./agent-loading";
import type { EvidenceBasis, ResearchCampaignPlan, ResearchDecision, ResearchEvidence } from "@/types/research";

interface Props { plan: ResearchCampaignPlan | null; isLoading: boolean; error: string | null; onRetry: () => void }
type Tab = "positioning" | "routes" | "sources";

const steps = ["Tìm xu hướng và hành vi mua hàng...", "Đọc và kiểm chứng nguồn tham khảo...", "Xác định khách hàng và thông điệp bán hàng...", "Hoàn thiện hai phương án quảng cáo để thử nghiệm..."];
const EVIDENCE_LABELS: Record<EvidenceBasis, string> = {
  product_brief: "Từ thông tin sản phẩm", supplied_source: "Từ nguồn bạn cung cấp",
  external_research: "Nghiên cứu bên ngoài", general_marketing_knowledge: "Kiến thức thị trường",
  assumption: "Giả định cần kiểm chứng",
};

interface CitationSource { number: number; title: string; url: string; usage: string }

function buildCitationRegistry(plan: ResearchCampaignPlan | null): CitationSource[] {
  if (!plan) return [];
  const sources = new Map<string, Omit<CitationSource, "number">>();
  for (const source of plan.source_summary.sources) sources.set(source.url, source);
  const positioning = plan.product_positioning;
  const evidenceBlocks = [
    positioning.main_campaign_angle.evidence, positioning.target_audience.evidence,
    positioning.key_selling_message.evidence, ...positioning.benefit_hierarchy.map(item => item.evidence),
    ...plan.creative_routes.map(route => route.evidence),
  ];
  for (const evidence of evidenceBlocks.flat()) {
    if (!evidence.source_url || sources.has(evidence.source_url)) continue;
    let title = evidence.source_url;
    try { title = new URL(evidence.source_url).hostname.replace(/^www\./, ""); } catch { /* URL is validated by the API. */ }
    sources.set(evidence.source_url, { title, url: evidence.source_url, usage: evidence.detail });
  }
  return [...sources.values()].map((source, index) => ({ ...source, number: index + 1 }));
}

function InlineCitations({ evidence, citationNumbers }: { evidence: ResearchEvidence[]; citationNumbers: Map<string, number> }) {
  const citations = [...new Map(evidence.flatMap(item => {
    if (!item.source_url) return [];
    const number = citationNumbers.get(item.source_url);
    return number === undefined ? [] : [[item.source_url, number] as const];
  })).entries()].map(([url, number]) => ({ url, number }));
  if (!citations.length) return null;
  return <sup className="ml-1 whitespace-nowrap">{citations.map(({ url, number }) => <a key={url} href={url} target="_blank" rel="noopener noreferrer" title={`Mở nguồn gốc ${number}`} className="text-[#35ea52] hover:underline font-mono text-[0.72em]">[{number}]</a>)}</sup>;
}

function EvidenceList({ evidence, citationNumbers }: { evidence: ResearchEvidence[]; citationNumbers: Map<string, number> }) {
  if (!evidence.length) return null;
  return <details className="group border-t border-foreground/10 pt-3"><summary className="cursor-pointer list-none text-[10px] font-mono text-foreground/35 hover:text-foreground/60 tracking-wider">CƠ SỞ ĐỀ XUẤT ({evidence.length})</summary><div className="space-y-2 mt-3">{evidence.map((item, index) => { const number = item.source_url ? citationNumbers.get(item.source_url) : undefined; return <div key={`${item.basis}-${index}`} className="p-3 border border-foreground/10 bg-background/40 text-xs font-mono"><div className="text-[#35ea52] tracking-wider mb-1">{number ? `[${number}] ` : ""}{EVIDENCE_LABELS[item.basis]}</div><p className="text-foreground/60 leading-relaxed">{item.detail}</p>{item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-foreground/40 hover:text-foreground"><ExternalLink className="h-3 w-3" /> Mở nguồn [{number}]</a>}</div>; })}</div></details>;
}

function DecisionCard({ title, helper, decision, citationNumbers }: { title: string; helper: string; decision: ResearchDecision; citationNumbers: Map<string, number> }) {
  return <article className="p-5 border border-foreground/10 bg-foreground/[0.02] space-y-4"><div><h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase">{title}</h3><p className="text-[11px] text-foreground/30 mt-1">{helper}</p></div><p className="text-base font-semibold text-foreground leading-relaxed">{decision.decision}<InlineCitations evidence={decision.evidence} citationNumbers={citationNumbers} /></p><div className="p-3 border-l-2 border-foreground/20 bg-background/30"><span className="block text-[10px] font-mono text-foreground/30 mb-1">VÌ SAO NÊN CHỌN</span><p className="text-sm text-foreground/55 leading-relaxed">{decision.rationale}<InlineCitations evidence={decision.evidence} citationNumbers={citationNumbers} /></p></div><EvidenceList evidence={decision.evidence} citationNumbers={citationNumbers} /></article>;
}

export const StageResearch: React.FC<Props> = ({ plan, isLoading, error, onRetry }) => {
  const [tab, setTab] = React.useState<Tab>("positioning");
  const citationSources = React.useMemo(() => buildCitationRegistry(plan), [plan]);
  const citationNumbers = React.useMemo(() => new Map(citationSources.map(source => [source.url, source.number])), [citationSources]);
  if (isLoading) return <div className="h-full flex flex-col justify-center max-w-xl mx-auto w-full"><AgentLoading agentName="TRỢ LÝ LẬP CHIẾN DỊCH" steps={steps} isComplete={false} /></div>;
  if (error) return <div className="min-h-[420px] flex items-center justify-center"><div className="max-w-lg text-center space-y-4"><AlertTriangle className="h-9 w-9 text-red-400 mx-auto" /><h2 className="font-mono font-bold">CHƯA THỂ TẠO ĐỀ XUẤT</h2><p className="text-sm text-foreground/50">{error}</p><button type="button" onClick={onRetry} className="px-5 py-2 border border-foreground text-xs font-mono hover:bg-foreground hover:text-background">THỬ LẠI</button></div></div>;
  if (!plan) return <div className="min-h-[420px] flex items-center justify-center text-sm text-foreground/35">Hãy nhập thông tin sản phẩm để nhận đề xuất chiến dịch bán hàng.</div>;

  const positioning = plan.product_positioning;
  const tabs: Array<[Tab, string]> = [["positioning", "CHIẾN LƯỢC BÁN HÀNG"], ["routes", "2 PHƯƠNG ÁN QUẢNG CÁO"], ["sources", "NGUỒN THAM KHẢO"]];
  return <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
    <header className="space-y-4 border-b border-foreground/10 pb-4"><div className="flex items-start justify-between gap-4"><div><div className="flex items-center gap-2 text-[#35ea52] text-[10px] font-mono tracking-widest mb-2"><CheckCircle2 className="h-3.5 w-3.5" /> ĐÃ SẴN SÀNG ĐỂ TRIỂN KHAI NỘI DUNG</div><h2 className="text-xl font-bold font-display tracking-wider text-foreground">ĐỀ XUẤT CHIẾN DỊCH BÁN HÀNG</h2><p className="text-sm text-foreground/45 mt-1">Chọn thông điệp, khách hàng và một trong hai hướng quảng cáo để bắt đầu tạo nội dung.</p></div><ShieldCheck className="h-6 w-6 text-[#35ea52] shrink-0" /></div><nav className="flex flex-wrap gap-2" aria-label="Nội dung đề xuất chiến dịch">{tabs.map(([id, label]) => <button key={id} type="button" onClick={() => setTab(id)} className={`px-4 py-2 text-xs font-mono font-bold tracking-wider border ${tab === id ? "bg-[#35ea52] text-black border-[#35ea52]" : "text-foreground/50 border-foreground/10 hover:border-foreground/30"}`}>{label}</button>)}</nav></header>
    <div className="flex-1 overflow-y-auto pb-6">
      {tab === "positioning" && <div className="space-y-5"><DecisionCard title="Góc tiếp cận chủ đạo" helper="Ý tưởng lớn xuyên suốt chiến dịch" decision={positioning.main_campaign_angle} citationNumbers={citationNumbers} /><DecisionCard title="Nhóm khách hàng nên tập trung" helper="Những người có khả năng quan tâm và mua cao nhất" decision={positioning.target_audience} citationNumbers={citationNumbers} /><DecisionCard title="Thông điệp bán hàng chính" helper="Điều khách hàng cần nhớ về sản phẩm" decision={positioning.key_selling_message} citationNumbers={citationNumbers} /><section className="space-y-3"><div className="flex items-center gap-2"><Target className="h-4 w-4 text-[#35ea52]" /><div><h3 className="text-xs font-mono font-bold tracking-widest">THỨ TỰ LỢI ÍCH NÊN TRUYỀN THÔNG</h3><p className="text-[11px] text-foreground/30 mt-1">Ưu tiên từ thông điệp mạnh nhất đến thông điệp bổ trợ</p></div></div>{[...positioning.benefit_hierarchy].sort((a, b) => a.rank - b.rank).map(item => <article key={item.rank} className="p-4 border border-foreground/10"><div className="flex gap-4"><span className="text-2xl font-mono text-[#35ea52]">{item.rank}</span><div className="space-y-2"><h4 className="font-semibold">{item.benefit}<InlineCitations evidence={item.evidence} citationNumbers={citationNumbers} /></h4><p className="text-sm text-foreground/50 leading-relaxed">{item.rationale}<InlineCitations evidence={item.evidence} citationNumbers={citationNumbers} /></p></div></div></article>)}</section></div>}
      {tab === "routes" && <div className="space-y-4"><div className="p-4 border border-[#35ea52]/20 bg-[#35ea52]/[0.04] text-sm text-foreground/55">Hai phương án dưới đây dùng để chạy thử A/B. Bắt đầu với cùng ngân sách và giữ lại phương án tạo nhiều lượt nhấp hoặc đơn hàng hơn.</div><div className="grid grid-cols-1 lg:grid-cols-2 gap-5">{plan.creative_routes.map((route, index) => <article key={route.route_name} className="p-5 border border-foreground/10 space-y-4"><div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2"><Route className="h-4 w-4 text-[#35ea52]" /><h3 className="font-mono font-bold text-[#35ea52]">PHƯƠNG ÁN {index + 1}</h3></div><span className="text-xs text-foreground/35">{route.route_name}</span></div><div><span className="text-[10px] font-mono text-foreground/35">CÂU MỞ ĐẦU THU HÚT</span><p className="font-semibold mt-1">{route.hook_idea}<InlineCitations evidence={route.evidence} citationNumbers={citationNumbers} /></p></div><div><span className="text-[10px] font-mono text-foreground/35">HÌNH ẢNH NÊN THỂ HIỆN</span><p className="text-sm text-foreground/60 mt-1">{route.visual_direction}</p></div><div><span className="text-[10px] font-mono text-foreground/35">GÓC KHAI THÁC THÔNG ĐIỆP</span><p className="text-sm text-foreground/60 mt-1">{route.message_angle}<InlineCitations evidence={route.evidence} citationNumbers={citationNumbers} /></p></div><div><span className="text-[10px] font-mono text-foreground/35 block mb-2">KÊNH PHÙ HỢP</span><div className="flex flex-wrap gap-2">{route.suggested_platform_usage.map(platform => <span key={platform} className="px-2 py-1 border border-foreground/15 text-[10px] font-mono">{platform}</span>)}</div></div><div className="p-3 border-l-2 border-foreground/20 bg-background/30"><span className="text-[10px] font-mono text-foreground/30">VÌ SAO CÓ THỂ HIỆU QUẢ</span><p className="text-xs text-foreground/50 leading-relaxed mt-1">{route.rationale}<InlineCitations evidence={route.evidence} citationNumbers={citationNumbers} /></p></div><EvidenceList evidence={route.evidence} citationNumbers={citationNumbers} /></article>)}</div></div>}
      {tab === "sources" && <div className="space-y-6"><p className="text-sm text-foreground/45">Số nguồn tại đây khớp với ký hiệu [1], [2] trong từng đề xuất. Một nguồn luôn giữ cùng số trên toàn bộ chiến dịch.</p><section className="space-y-3">{citationSources.length ? citationSources.map(source => <a id={`nguon-${source.number}`} key={source.url} href={source.url} target="_blank" rel="noreferrer" className="scroll-mt-6 block p-4 border border-foreground/10 hover:border-[#35ea52]/40"><div className="flex items-start gap-4"><span className="font-mono text-[#35ea52] font-bold">[{source.number}]</span><div className="flex-1"><h3 className="font-semibold text-sm">{source.title}</h3><p className="text-xs text-foreground/40 mt-2">Được dùng để: {source.usage}</p></div><ExternalLink className="h-4 w-4 shrink-0 text-[#35ea52]" /></div></a>) : <div className="p-5 border border-foreground/10 text-sm text-foreground/40">Chưa có nguồn bên ngoài được ghi nhận. Các nội dung hiện chỉ dựa trên thông tin sản phẩm hoặc giả định đã ghi rõ.</div>}</section><section className="p-5 border border-amber-500/20 bg-amber-500/5"><div className="flex items-center gap-2 mb-3"><Lightbulb className="h-4 w-4 text-amber-400" /><h3 className="text-xs font-mono font-bold text-amber-400 tracking-widest">CẦN XÁC MINH TRƯỚC KHI CHẠY QUẢNG CÁO</h3></div>{plan.source_summary.assumptions.length ? <ul className="space-y-2">{plan.source_summary.assumptions.map((item, index) => <li key={index} className="text-sm text-foreground/55">• {item}</li>)}</ul> : <p className="text-sm text-foreground/45">Không có giả định bổ sung cần xác minh.</p>}</section></div>}
    </div>
  </div>;
};
