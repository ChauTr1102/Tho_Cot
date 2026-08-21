"use client";
import * as React from "react";
import { Briefcase, Palette, TrendingUp, Upload, Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { CAMPAIGN_OBJECTIVES, type CampaignObjective, type ResearchSubmission } from "@/types/research";

interface Props { value: ResearchSubmission; onChange: React.Dispatch<React.SetStateAction<ResearchSubmission>> }
const split = (text: string) => [...new Set(text.split(/\r?\n/).map((item) => item.trim()).filter(Boolean))];
const join = (items: string[]) => items.join("\n");
const inputClass = "h-9 bg-foreground/[0.02] border-foreground/10 text-xs font-mono";
const areaClass = "bg-foreground/[0.02] border-foreground/10 text-xs font-mono min-h-[88px]";

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return <label className="space-y-1.5"><span className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider">{label}</span>{children}{hint && <span className="block text-[10px] font-mono text-foreground/30">{hint}</span>}</label>;
}
function ListField({ label, value, onChange, required }: { label: string; value: string[]; onChange: (items: string[]) => void; required?: boolean }) {
  return <Field label={`${label}${required ? " *" : ""}`} hint="Một giá trị mỗi dòng"><Textarea className={areaClass} value={join(value)} onChange={(e) => onChange(split(e.target.value))} /></Field>;
}
function Section({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) {
  return <section className="p-5 border border-foreground/10 bg-background/50 space-y-4"><div className="flex items-center gap-2 border-b border-foreground/10 pb-2"><Icon className="h-4 w-4 text-[#35ea52]" /><h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase">{title}</h3></div>{children}</section>;
}

export const StageProductInput: React.FC<Props> = ({ value, onChange }) => {
  const data = value.input;
  const setInput = (input: ResearchSubmission["input"]) => onChange((current) => ({ ...current, input }));
  const product = (patch: Partial<typeof data.product_brief>) => setInput({ ...data, product_brief: { ...data.product_brief, ...patch } });
  const brand = (patch: Partial<typeof data.brand_kit>) => setInput({ ...data, brand_kit: { ...data.brand_kit, ...patch } });
  const audience = (patch: Partial<typeof data.audience_brief>) => setInput({ ...data, audience_brief: { ...data.audience_brief, ...patch } });
  const market = (patch: Partial<typeof data.market_signal>) => setInput({ ...data, market_signal: { ...data.market_signal, ...patch } });
  return <div className="space-y-6 h-full flex flex-col">
    <div className="space-y-2 border-b border-foreground/10 pb-4"><h2 className="text-lg font-bold font-mono tracking-wider text-foreground">THÔNG TIN NGHIÊN CỨU · LƯỢC ĐỒ 1.0</h2><p className="text-sm font-mono text-foreground/40">Thông tin được gửi trực tiếp tới hệ thống nghiên cứu. Dấu * là trường bắt buộc.</p></div>
    <div className="flex-1 space-y-6 overflow-y-auto pr-2 pb-8">
      <Section icon={Briefcase} title="1. Thông tin sản phẩm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Campaign ID *"><Input className={inputClass} value={data.campaign_id} onChange={(e) => setInput({ ...data, campaign_id: e.target.value })} /></Field>
          <Field label="Product name *"><Input className={inputClass} value={data.product_brief.product_name} onChange={(e) => product({ product_name: e.target.value })} /></Field>
          <Field label="Category *"><Input className={inputClass} value={data.product_brief.category} onChange={(e) => product({ category: e.target.value })} /></Field>
          <Field label="Promotion"><Input className={inputClass} value={data.product_brief.promotion ?? ""} onChange={(e) => product({ promotion: e.target.value || null })} /></Field>
          <ListField label="Key selling points" required value={data.product_brief.key_selling_points} onChange={(key_selling_points) => product({ key_selling_points })} />
          <ListField label="Target markets" required value={data.product_brief.target_market} onChange={(target_market) => product({ target_market })} />
          <ListField label="Required claims" value={data.product_brief.required_claims} onChange={(required_claims) => product({ required_claims })} />
          <ListField label="Restricted claims" value={data.product_brief.restricted_claims} onChange={(restricted_claims) => product({ restricted_claims })} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Field label="Giá bán"><Input type="number" min="0" className={inputClass} value={data.product_brief.price?.amount ?? ""} onChange={(e) => product({ price: e.target.value ? { amount: Number(e.target.value), currency: data.product_brief.price?.currency ?? "VND", unit: data.product_brief.price?.unit ?? "sản phẩm", note: data.product_brief.price?.note ?? null } : null })} /></Field>
          <Field label="Currency"><Input className={inputClass} disabled={!data.product_brief.price} value={data.product_brief.price?.currency ?? ""} onChange={(e) => data.product_brief.price && product({ price: { ...data.product_brief.price, currency: e.target.value.toUpperCase() } })} /></Field>
          <Field label="Price unit"><Input className={inputClass} disabled={!data.product_brief.price} value={data.product_brief.price?.unit ?? ""} onChange={(e) => data.product_brief.price && product({ price: { ...data.product_brief.price, unit: e.target.value } })} /></Field>
          <Field label="Price note"><Input className={inputClass} disabled={!data.product_brief.price} value={data.product_brief.price?.note ?? ""} onChange={(e) => data.product_brief.price && product({ price: { ...data.product_brief.price, note: e.target.value || null } })} /></Field>
        </div>
      </Section>
      <Section icon={Palette} title="2. Bộ nhận diện & hình ảnh">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Brand color name *"><Input className={inputClass} value={data.brand_kit.brand_colors[0]?.name ?? ""} onChange={(e) => brand({ brand_colors: [{ ...(data.brand_kit.brand_colors[0] ?? { hex: null, verification_status: "unknown" }), name: e.target.value }] })} /></Field>
          <Field label="Brand color hex"><Input className={inputClass} value={data.brand_kit.brand_colors[0]?.hex ?? ""} onChange={(e) => brand({ brand_colors: [{ ...(data.brand_kit.brand_colors[0] ?? { name: "Brand color", verification_status: "unknown" }), hex: e.target.value.toUpperCase() || null }] })} /></Field>
          <ListField label="Tone of voice" required value={data.brand_kit.tone_of_voice} onChange={(tone_of_voice) => brand({ tone_of_voice })} />
          <Field label="Evidence bổ sung"><Textarea className={areaClass} value={value.evidence} onChange={(e) => onChange((current) => ({ ...current, evidence: e.target.value }))} /></Field>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Field label="Logo *"><Input type="file" accept="image/jpeg,image/png,image/webp,image/gif,image/bmp,image/tiff" onChange={(e) => { const file = e.target.files?.[0] ?? null; onChange((current) => ({ ...current, files: { ...current.files, logo: file }, input: { ...current.input, brand_kit: { ...current.input.brand_kit, logo: file?.name ?? "logo" } } })); }} /></Field>
          <Field label="Ảnh sản phẩm *"><Input type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,image/bmp,image/tiff" onChange={(e) => { const files = Array.from(e.target.files ?? []); onChange((current) => ({ ...current, files: { ...current.files, product_photos: files }, input: { ...current.input, brand_kit: { ...current.input.brand_kit, product_photos: files.map((file) => file.name) } } })); }} /></Field>
          <Field label="Hình ảnh hiện có"><Input type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,image/bmp,image/tiff" onChange={(e) => { const files = Array.from(e.target.files ?? []); onChange((current) => ({ ...current, files: { ...current.files, existing_product_visuals: files }, input: { ...current.input, brand_kit: { ...current.input.brand_kit, existing_product_visuals: files.map((file) => file.name) } } })); }} /></Field>
        </div>
        <p className="flex items-center gap-2 text-[10px] font-mono text-foreground/35"><Upload className="h-3.5 w-3.5" />JPEG, PNG, WebP, GIF, BMP hoặc TIFF · tối đa 20 MB mỗi ảnh</p>
      </Section>
      <Section icon={Users} title="3. Khách hàng mục tiêu"><div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ListField label="Target customers" required value={data.audience_brief.target_customer} onChange={(target_customer) => audience({ target_customer })} />
        <ListField label="Languages" required value={data.audience_brief.languages} onChange={(languages) => audience({ languages })} />
        <ListField label="Platforms" required value={data.audience_brief.platforms} onChange={(platforms) => audience({ platforms })} />
        <ListField label="Markets" required value={data.audience_brief.markets} onChange={(markets) => audience({ markets })} />
      </div></Section>
      <Section icon={TrendingUp} title="4. Tín hiệu thị trường">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ListField label="Trends" value={data.market_signal.trends} onChange={(trends) => market({ trends })} />
          <ListField label="Seasonal moments" value={data.market_signal.seasonal_moments} onChange={(seasonal_moments) => market({ seasonal_moments })} />
          <ListField label="Consumer pain points" value={data.market_signal.consumer_pain_points} onChange={(consumer_pain_points) => market({ consumer_pain_points })} />
          <ListField label="Search keywords" value={data.market_signal.search_keywords} onChange={(search_keywords) => market({ search_keywords })} />
          <ListField label="Competitor angles" value={data.market_signal.competitor_angles} onChange={(competitor_angles) => market({ competitor_angles })} />
        </div>
        <fieldset className="space-y-2"><legend className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider">Campaign objectives *</legend><div className="flex flex-wrap gap-4">{CAMPAIGN_OBJECTIVES.map((objective) => <label key={objective} className="flex items-center gap-2 text-xs font-mono text-foreground/60"><input type="checkbox" className="accent-[#35ea52]" checked={data.market_signal.campaign_objectives.includes(objective)} onChange={(e) => market({ campaign_objectives: e.target.checked ? [...data.market_signal.campaign_objectives, objective] : data.market_signal.campaign_objectives.filter((item: CampaignObjective) => item !== objective) })} />{objective}</label>)}</div></fieldset>
      </Section>
    </div>
  </div>;
};
