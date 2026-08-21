"use client";
import * as React from "react";
import {
  Briefcase,
  ExternalLink,
  FileText,
  ImageIcon,
  Link2,
  Loader2,
  Palette,
  PenLine,
  Plus,
  RotateCcw,
  Sparkles,
  Trash2,
  TrendingUp,
  Upload,
  Users,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  CAMPAIGN_OBJECTIVES,
  createEmptyResearchSubmission,
  createInitialResearchSubmission,
  type CampaignObjective,
  type ResearchSubmission,
} from "@/types/research";

interface Props {
  value: ResearchSubmission;
  onChange: React.Dispatch<React.SetStateAction<ResearchSubmission>>;
}

const toArr = (val: unknown): string[] => {
  if (!val) return [];
  if (Array.isArray(val)) return val.flat().map((x) => String(x).trim()).filter(Boolean);
  if (typeof val === "string") return val.split(/\r?\n/).map((x) => x.trim()).filter(Boolean);
  return [];
};

const split = (text: string) => [...new Set(text.split(/\r?\n/).map((item) => item.trim()).filter(Boolean))];
const join = (items: unknown) =>
  Array.isArray(items) ? items.join("\n") : typeof items === "string" ? items : "";
const inputClass = "h-9 bg-foreground/[0.02] border-foreground/10 text-xs font-mono";
const areaClass = "bg-foreground/[0.02] border-foreground/10 text-xs font-mono min-h-[88px]";

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="space-y-1.5">
      <span className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider">{label}</span>
      {children}
      {hint && <span className="block text-[10px] font-mono text-foreground/30">{hint}</span>}
    </label>
  );
}

function ListField({
  label,
  value,
  onChange,
  required,
}: {
  label: string;
  value: string[];
  onChange: (items: string[]) => void;
  required?: boolean;
}) {
  return (
    <Field label={`${label}${required ? " *" : ""}`} hint="Một giá trị mỗi dòng">
      <Textarea className={areaClass} value={join(value)} onChange={(e) => onChange(split(e.target.value))} />
    </Field>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="p-5 border border-foreground/10 bg-background/50 space-y-4">
      <div className="flex items-center gap-2 border-b border-foreground/10 pb-2">
        <Icon className="h-4 w-4 text-[#35ea52]" />
        <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase">{title}</h3>
      </div>
      {children}
    </section>
  );
}

export const StageProductInput: React.FC<Props> = ({ value, onChange }) => {
  const [inputMode, setInputMode] = React.useState<"link" | "manual">("link");
  const [tiktokUrl, setTiktokUrl] = React.useState("");
  const [newImageUrl, setNewImageUrl] = React.useState("");
  const [isExtracting, setIsExtracting] = React.useState(false);
  const [extractedSuccess, setExtractedSuccess] = React.useState(false);

  const data = value.input;
  const setInput = (input: ResearchSubmission["input"]) => onChange((current) => ({ ...current, input }));
  const product = (patch: Partial<typeof data.product_brief>) =>
    setInput({ ...data, product_brief: { ...data.product_brief, ...patch } });
  const brand = (patch: Partial<typeof data.brand_kit>) =>
    setInput({ ...data, brand_kit: { ...data.brand_kit, ...patch } });
  const audience = (patch: Partial<typeof data.audience_brief>) =>
    setInput({ ...data, audience_brief: { ...data.audience_brief, ...patch } });
  const market = (patch: Partial<typeof data.market_signal>) =>
    setInput({ ...data, market_signal: { ...data.market_signal, ...patch } });

  const handleAddImageUrl = () => {
    if (!newImageUrl.trim()) return;
    const urlToAdd = newImageUrl.trim();
    brand({ product_photos: [...data.brand_kit.product_photos, urlToAdd] });
    setNewImageUrl("");
    toast.success("Đã thêm hình ảnh vào danh sách!");
  };

  const handleExtractFromUrl = async () => {
    if (!tiktokUrl.trim()) {
      toast.error("Hãy nhập URL TikTok Shop hợp lệ.");
      return;
    }
    setIsExtracting(true);
    try {
      const res = await api.extractProduct({ url: tiktokUrl.trim(), render: true });
      const payload = res.data;
      const pb = payload?.product_brief;
      const bk = payload?.brand_kit;
      const ab = payload?.audience_brief;
      const ms = payload?.market_signal;

      const productName = pb?.product_name || "Sản phẩm TikTok Shop";
      const category = pb?.category || "E-Commerce";
      const keySellingPoints = toArr(pb?.key_selling_points);
      const targetMarkets = toArr(pb?.target_market);
      const requiredClaims = toArr(pb?.required_claims);
      const restrictedClaims = toArr(pb?.restricted_or_forbidden_claims);

      const priceAmount = pb?.price_or_promotion?.price ?? null;
      const priceCurrency = pb?.price_or_promotion?.currency || "VND";
      const promotion = pb?.price_or_promotion?.promotion || null;

      const brandColors = bk?.brand_colors?.primary
        ? [
            {
              name: bk.brand_colors.primary,
              hex: bk.brand_colors.primary.startsWith("#") ? bk.brand_colors.primary : "#10b981",
              verification_status: "estimated" as const,
            },
          ]
        : [
            {
              name: "Màu chủ đạo",
              hex: "#10b981",
              verification_status: "estimated" as const,
            },
          ];

      const toneOfVoice = toArr(
        bk?.tone_of_voice?.attributes?.length
          ? bk.tone_of_voice.attributes
          : bk?.tone_of_voice?.description || ["Trẻ trung", "Năng động", "Thân thiện"]
      );

      const targetCustomer = toArr(ab?.target_customer || ["Khách hàng mua sắm online trên TikTok Shop"]);
      const languages = toArr(ab?.language || ["vi", "en"]);
      const platforms = toArr(ab?.platform || ["TikTok Shop"]);
      const markets = toArr(ab?.market || ["Việt Nam"]);

      const trends = toArr(ms?.trend || ["Livestream Shopping", "Short-form Video Trends"]);
      const seasonalMoments = toArr(ms?.seasonal_moment || ["Mùa hè", "Mega Sale"]);
      const consumerPainPoints = toArr(ms?.consumer_pain_point || ["Cần sản phẩm chất lượng, tiện dụng"]);
      const searchKeywords = toArr(ms?.search_keyword || [productName]);
      const competitorAngles = toArr(ms?.competitor_angle);

      onChange((current) => ({
        ...current,
        input: {
          schema_version: "1.0",
          campaign_id: current.input.campaign_id || `campaign-${Date.now()}`,
          product_brief: {
            product_name: productName,
            category: category,
            key_selling_points: keySellingPoints.length ? keySellingPoints : ["Chất lượng cao", "Tiện dụng"],
            price:
              priceAmount !== null
                ? {
                    amount: priceAmount,
                    currency: priceCurrency,
                    unit: "sản phẩm",
                    note: promotion,
                  }
                : null,
            promotion: promotion,
            target_market: targetMarkets.length ? targetMarkets : ["Việt Nam"],
            required_claims: requiredClaims,
            restricted_claims: restrictedClaims,
          },
          brand_kit: {
            logo: bk?.logo?.path || current.input.brand_kit.logo || "logo.png",
            brand_colors: brandColors,
            tone_of_voice: toneOfVoice.length ? toneOfVoice : ["Trẻ trung", "Năng động"],
            product_photos: toArr(bk?.product_photos),
            existing_product_visuals: toArr(bk?.existing_product_visuals),
          },
          audience_brief: {
            target_customer: targetCustomer,
            languages: languages,
            platforms: platforms,
            markets: markets,
          },
          market_signal: {
            trends: trends,
            seasonal_moments: seasonalMoments,
            consumer_pain_points: consumerPainPoints,
            search_keywords: searchKeywords,
            competitor_angles: competitorAngles,
            campaign_objectives: ["conversion", "awareness"],
          },
        },
      }));

      setExtractedSuccess(true);
      toast.success("Đã trích xuất & tự động điền toàn bộ thông tin sản phẩm!");
    } catch (error: any) {
      toast.error(error.message || "Không thể trích xuất dữ liệu từ URL.");
    } finally {
      setIsExtracting(false);
    }
  };

  const handleResetEmpty = () => {
    onChange(createEmptyResearchSubmission());
    toast.info("Đã xóa trắng form để nhập thủ công từ đầu.");
  };

  const handleLoadSample = () => {
    onChange(createInitialResearchSubmission());
    toast.success("Đã tải dữ liệu mẫu (G7 Coffee).");
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="space-y-2 border-b border-foreground/10 pb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">
            THÔNG TIN NGHIÊN CỨU · LƯỢC ĐỒ 1.0
          </h2>
          <span className="text-[10px] font-mono text-[#35ea52] border border-[#35ea52]/30 px-2 py-0.5 tracking-widest uppercase">
            2 CHẾ ĐỘ NHẬP LIỆU
          </span>
        </div>
        <p className="text-sm font-mono text-foreground/40">
          Chọn phương thức cung cấp dữ liệu sản phẩm để hệ thống AI tiến hành nghiên cứu.
        </p>

        {/* 2 OPTIONS TAB SWITCHER */}
        <div className="flex mt-3 border border-foreground/20 bg-foreground/[0.02]">
          <button
            type="button"
            onClick={() => setInputMode("link")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-mono tracking-wider transition-all ${
              inputMode === "link"
                ? "bg-[#35ea52] text-black font-bold shadow-md"
                : "text-foreground/50 hover:text-foreground hover:bg-foreground/[0.05]"
            }`}
          >
            <Link2 className="h-3.5 w-3.5" />
            LỰA CHỌN 1: DÁN LINK TIKTOK SHOP (TỰ ĐỘNG)
          </button>
          <div className="w-px bg-foreground/20" />
          <button
            type="button"
            onClick={() => setInputMode("manual")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-mono tracking-wider transition-all ${
              inputMode === "manual"
                ? "bg-foreground text-black font-bold shadow-md"
                : "text-foreground/50 hover:text-foreground hover:bg-foreground/[0.05]"
            }`}
          >
            <PenLine className="h-3.5 w-3.5" />
            LỰA CHỌN 2: NHẬP THÔNG TIN TỪ ĐẦU (THỦ CÔNG)
          </button>
        </div>
      </div>

      {/* OPTION 1: LINK IMPORT VIEW */}
      {inputMode === "link" && (
        <div className="p-4 border border-[#35ea52]/30 bg-[#35ea52]/[0.03] space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#35ea52]" />
              <span className="text-xs font-mono font-bold tracking-wider text-foreground uppercase">
                NHẬP TỰ ĐỘNG TỪ TIKTOK SHOP URL
              </span>
            </div>
            <span className="text-[10px] font-mono text-foreground/40">GEMINI + AGNO + PLAYWRIGHT</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Link2 className="absolute left-3 top-2.5 h-4 w-4 text-foreground/30" />
              <Input
                placeholder="https://shop.tiktok.com/vn/pdp/..."
                value={tiktokUrl}
                onChange={(e) => setTiktokUrl(e.target.value)}
                disabled={isExtracting}
                className="h-9 pl-9 text-xs font-mono bg-background/80 border-foreground/20 text-foreground placeholder:text-foreground/25 focus:border-[#35ea52]"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleExtractFromUrl();
                }}
              />
            </div>
            <button
              type="button"
              onClick={handleExtractFromUrl}
              disabled={isExtracting || !tiktokUrl.trim()}
              className="h-9 px-4 bg-[#35ea52] text-black text-xs font-mono font-bold tracking-wider hover:bg-[#35ea52]/90 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 shrink-0"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ĐANG TRÍCH XUẤT...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  TRÍCH XUẤT & ĐIỀN FORM
                </>
              )}
            </button>
          </div>

          <div className="flex items-center justify-between text-[10px] font-mono text-foreground/40 pt-1">
            <span>
              {extractedSuccess
                ? "✓ Đã tự động điền form bên dưới. Bạn có thể kiểm tra và chỉnh sửa nếu cần."
                : "Hệ thống AI sẽ tự động đọc sản phẩm, thương hiệu, giá, USPs, tệp khách hàng và tín hiệu thị trường."}
            </span>
          </div>
        </div>
      )}

      {/* OPTION 2: MANUAL CONTROLS */}
      {inputMode === "manual" && (
        <div className="p-3 border border-foreground/15 bg-foreground/[0.02] flex flex-wrap items-center justify-between gap-3 animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <PenLine className="h-4 w-4 text-foreground/50" />
            <span className="text-xs font-mono text-foreground/70">
              CHẾ ĐỘ TỰ ĐIỀN THỦ CÔNG: Nhập thông tin chi tiết vào các mục bên dưới.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleResetEmpty}
              className="h-7 px-3 border border-foreground/20 text-[11px] font-mono text-foreground/60 hover:text-foreground hover:border-foreground/40 transition-all flex items-center gap-1.5"
            >
              <RotateCcw className="h-3 w-3" />
              XÓA TRẮNG FORM
            </button>
            <button
              type="button"
              onClick={handleLoadSample}
              className="h-7 px-3 border border-[#35ea52]/30 text-[#35ea52] text-[11px] font-mono hover:bg-[#35ea52]/10 transition-all flex items-center gap-1.5"
            >
              <FileText className="h-3 w-3" />
              TẢI DỮ LIỆU MẪU
            </button>
          </div>
        </div>
      )}

      {/* DETAILED FORM SECTIONS */}
      <div className="flex-1 space-y-6 overflow-y-auto pr-2 pb-8">
        <Section icon={Briefcase} title="1. Thông tin sản phẩm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Campaign ID *">
              <Input
                className={inputClass}
                value={data.campaign_id}
                onChange={(e) => setInput({ ...data, campaign_id: e.target.value })}
              />
            </Field>
            <Field label="Product name *">
              <Input
                className={inputClass}
                value={data.product_brief.product_name}
                onChange={(e) => product({ product_name: e.target.value })}
              />
            </Field>
            <Field label="Category *">
              <Input
                className={inputClass}
                value={data.product_brief.category}
                onChange={(e) => product({ category: e.target.value })}
              />
            </Field>
            <Field label="Promotion">
              <Input
                className={inputClass}
                value={data.product_brief.promotion ?? ""}
                onChange={(e) => product({ promotion: e.target.value || null })}
              />
            </Field>
            <ListField
              label="Key selling points"
              required
              value={data.product_brief.key_selling_points}
              onChange={(key_selling_points) => product({ key_selling_points })}
            />
            <ListField
              label="Target markets"
              required
              value={data.product_brief.target_market}
              onChange={(target_market) => product({ target_market })}
            />
            <ListField
              label="Required claims"
              value={data.product_brief.required_claims}
              onChange={(required_claims) => product({ required_claims })}
            />
            <ListField
              label="Restricted claims"
              value={data.product_brief.restricted_claims}
              onChange={(restricted_claims) => product({ restricted_claims })}
            />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Field label="Giá bán">
              <Input
                type="number"
                min="0"
                className={inputClass}
                value={data.product_brief.price?.amount ?? ""}
                onChange={(e) =>
                  product({
                    price: e.target.value
                      ? {
                          amount: Number(e.target.value),
                          currency: data.product_brief.price?.currency ?? "VND",
                          unit: data.product_brief.price?.unit ?? "sản phẩm",
                          note: data.product_brief.price?.note ?? null,
                        }
                      : null,
                  })
                }
              />
            </Field>
            <Field label="Currency">
              <Input
                className={inputClass}
                disabled={!data.product_brief.price}
                value={data.product_brief.price?.currency ?? ""}
                onChange={(e) =>
                  data.product_brief.price &&
                  product({ price: { ...data.product_brief.price, currency: e.target.value.toUpperCase() } })
                }
              />
            </Field>
            <Field label="Price unit">
              <Input
                className={inputClass}
                disabled={!data.product_brief.price}
                value={data.product_brief.price?.unit ?? ""}
                onChange={(e) =>
                  data.product_brief.price &&
                  product({ price: { ...data.product_brief.price, unit: e.target.value } })
                }
              />
            </Field>
            <Field label="Price note">
              <Input
                className={inputClass}
                disabled={!data.product_brief.price}
                value={data.product_brief.price?.note ?? ""}
                onChange={(e) =>
                  data.product_brief.price &&
                  product({ price: { ...data.product_brief.price, note: e.target.value || null } })
                }
              />
            </Field>
          </div>
        </Section>

      <Section icon={Palette} title="2. Bộ nhận diện & hình ảnh">
        {/* Color & Tone Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider">
              Brand color name *
            </label>
            <div className="flex gap-2">
              <Input
                className={inputClass}
                placeholder="VD: Emerald Green, Deep Black..."
                value={data.brand_kit.brand_colors[0]?.name ?? ""}
                onChange={(e) =>
                  brand({
                    brand_colors: [
                      {
                        ...(data.brand_kit.brand_colors[0] ?? { hex: null, verification_status: "unknown" }),
                        name: e.target.value,
                      },
                    ],
                  })
                }
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider">
              Brand color hex
            </label>
            <div className="flex items-center gap-2">
              <div
                className="w-9 h-9 border border-foreground/20 shrink-0 shadow-inner"
                style={{
                  backgroundColor: data.brand_kit.brand_colors[0]?.hex || "#10b981",
                }}
              />
              <Input
                className={inputClass}
                placeholder="#10B981"
                value={data.brand_kit.brand_colors[0]?.hex ?? ""}
                onChange={(e) =>
                  brand({
                    brand_colors: [
                      {
                        ...(data.brand_kit.brand_colors[0] ?? { name: "Brand color", verification_status: "unknown" }),
                        hex: e.target.value.toUpperCase() || null,
                      },
                    ],
                  })
                }
              />
            </div>
          </div>

          <ListField
            label="Tone of voice"
            required
            value={data.brand_kit.tone_of_voice}
            onChange={(tone_of_voice) => brand({ tone_of_voice })}
          />
          <Field label="Evidence bổ sung">
            <Textarea
              className={areaClass}
              placeholder="Ghi chú thêm về thương hiệu, thông tin kiểm chứng..."
              value={value.evidence}
              onChange={(e) => onChange((current) => ({ ...current, evidence: e.target.value }))}
            />
          </Field>
        </div>

        {/* PRODUCT PHOTOS PREVIEW & MANAGEMENT */}
        <div className="space-y-3 pt-3 border-t border-foreground/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ImageIcon className="h-4 w-4 text-[#35ea52]" />
              <span className="text-xs font-mono font-bold tracking-wider text-foreground uppercase">
                ẢNH SẢN PHẨM ({data.brand_kit.product_photos.length}) <span className="text-[#35ea52]">*</span>
              </span>
            </div>
            {data.brand_kit.product_photos.length > 0 && (
              <span className="text-[10px] font-mono text-[#35ea52] bg-[#35ea52]/10 px-2 py-0.5 border border-[#35ea52]/30">
                ✓ {data.brand_kit.product_photos.length} ảnh đã nạp
              </span>
            )}
          </div>

          {/* Photo Grid Preview */}
          {data.brand_kit.product_photos.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2.5 p-3 border border-foreground/15 bg-black/40">
              {data.brand_kit.product_photos.map((photoUrl, idx) => (
                <div
                  key={idx}
                  className={`relative aspect-square border group overflow-hidden bg-foreground/[0.03] transition-all ${
                    idx === 0 ? "border-[#35ea52]/60 ring-1 ring-[#35ea52]/30" : "border-foreground/20"
                  }`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={photoUrl}
                    alt={`product-${idx}`}
                    referrerPolicy="no-referrer"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                    onError={(e) => {
                      (e.target as HTMLElement).style.opacity = "0.3";
                    }}
                  />
                  <div className="absolute top-1 left-1 bg-black/85 px-1.5 py-0.5 text-[8px] font-mono text-white/90 border border-white/10 flex items-center gap-1">
                    <span>#{idx + 1}</span>
                    {idx === 0 && <span className="text-[#35ea52] font-bold">ẢNH BÌA</span>}
                  </div>
                  <div className="absolute inset-0 bg-black/75 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 p-1">
                    {idx !== 0 && (
                      <button
                        type="button"
                        onClick={() => {
                          const updated = [...data.brand_kit.product_photos];
                          const [chosen] = updated.splice(idx, 1);
                          updated.unshift(chosen);
                          brand({ product_photos: updated });
                          toast.success("Đã đặt làm ảnh bìa chính!");
                        }}
                        className="p-1.5 bg-white/20 hover:bg-[#35ea52] hover:text-black text-white rounded text-[10px] font-mono transition-colors"
                        title="Đặt làm ảnh bìa"
                      >
                        Bìa
                      </button>
                    )}
                    <a
                      href={photoUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1.5 bg-white/20 hover:bg-white/30 text-white rounded transition-colors"
                      title="Xem ảnh gốc"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                    <button
                      type="button"
                      onClick={() => {
                        const updated = data.brand_kit.product_photos.filter((_, i) => i !== idx);
                        brand({ product_photos: updated });
                        toast.info(`Đã xóa ảnh #${idx + 1}`);
                      }}
                      className="p-1.5 bg-red-600/80 hover:bg-red-600 text-white rounded transition-colors"
                      title="Xóa ảnh"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Clean Upload & URL Input Bar */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-2 pt-1">
            {/* Direct URL Input */}
            <div className="md:col-span-8 flex gap-1.5">
              <Input
                placeholder="Dán trực tiếp URL ảnh (https://...)..."
                value={newImageUrl}
                onChange={(e) => setNewImageUrl(e.target.value)}
                className="h-9 text-xs font-mono bg-background/80 border-foreground/20 text-foreground placeholder:text-foreground/30 focus:border-[#35ea52]"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAddImageUrl();
                }}
              />
              <button
                type="button"
                onClick={handleAddImageUrl}
                disabled={!newImageUrl.trim()}
                className="h-9 px-4 border border-[#35ea52] bg-[#35ea52]/10 text-[#35ea52] text-xs font-mono font-bold hover:bg-[#35ea52] hover:text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed shrink-0 flex items-center gap-1"
              >
                <Plus className="h-3.5 w-3.5" /> THÊM URL
              </button>
            </div>

            {/* Custom Styled File Upload Button */}
            <div className="md:col-span-4">
              <label className="h-9 px-3 border border-dashed border-foreground/30 hover:border-[#35ea52] bg-foreground/[0.02] hover:bg-foreground/[0.05] cursor-pointer flex items-center justify-center gap-2 text-xs font-mono text-foreground/70 hover:text-foreground transition-all">
                <Upload className="h-3.5 w-3.5 text-[#35ea52]" />
                <span>TẢI TỆP TỪ MÁY</span>
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp,image/gif,image/bmp,image/tiff"
                  className="hidden"
                  onChange={(e) => {
                    const files = Array.from(e.target.files ?? []);
                    if (!files.length) return;
                    const newBlobUrls = files.map((file) => URL.createObjectURL(file));
                    onChange((current) => ({
                      ...current,
                      files: { ...current.files, product_photos: [...current.files.product_photos, ...files] },
                      input: {
                        ...current.input,
                        brand_kit: {
                          ...current.input.brand_kit,
                          product_photos: [...current.input.brand_kit.product_photos, ...newBlobUrls],
                        },
                      },
                    }));
                    toast.success(`Đã thêm ${files.length} ảnh từ thiết bị.`);
                    e.target.value = "";
                  }}
                />
              </label>
            </div>
          </div>
        </div>

        {/* LOGO & EXISTING VISUALS TILES */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-foreground/10">
          {/* Logo Card */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider flex items-center justify-between">
              <span>Logo thương hiệu *</span>
              {value.files.logo && (
                <span className="text-[#35ea52] font-mono text-[10px]">✓ {value.files.logo.name}</span>
              )}
            </label>
            <label className="flex flex-col items-center justify-center p-4 border border-dashed border-foreground/20 hover:border-[#35ea52]/60 bg-foreground/[0.01] hover:bg-foreground/[0.03] cursor-pointer transition-all min-h-[90px] group">
              <Upload className="h-4 w-4 text-foreground/30 group-hover:text-[#35ea52] transition-colors mb-1" />
              <span className="text-xs font-mono text-foreground/60 group-hover:text-foreground tracking-wider">
                {value.files.logo ? "BẤM ĐỂ ĐỔI LOGO" : "CHỌN TỆP LOGO (PNG, SVG, JPG)"}
              </span>
              <span className="text-[10px] font-mono text-foreground/30">Kích thước tối đa 10 MB</span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif,image/bmp,image/tiff,image/svg+xml"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0] ?? null;
                  onChange((current) => ({
                    ...current,
                    files: { ...current.files, logo: file },
                    input: {
                      ...current.input,
                      brand_kit: { ...current.input.brand_kit, logo: file?.name ?? "logo.png" },
                    },
                  }));
                  if (file) toast.success(`Đã chọn logo: ${file.name}`);
                }}
              />
            </label>
          </div>

          {/* Existing Visuals Card */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider flex items-center justify-between">
              <span>Hình ảnh banner / tư liệu hiện có</span>
              {data.brand_kit.existing_product_visuals.length > 0 && (
                <span className="text-[#35ea52] font-mono text-[10px]">
                  ✓ {data.brand_kit.existing_product_visuals.length} tư liệu
                </span>
              )}
            </label>
            <label className="flex flex-col items-center justify-center p-4 border border-dashed border-foreground/20 hover:border-[#35ea52]/60 bg-foreground/[0.01] hover:bg-foreground/[0.03] cursor-pointer transition-all min-h-[90px] group">
              <Upload className="h-4 w-4 text-foreground/30 group-hover:text-[#35ea52] transition-colors mb-1" />
              <span className="text-xs font-mono text-foreground/60 group-hover:text-foreground tracking-wider">
                TẢI LÊN BANNER / TƯ LIỆU QUẢNG CÁO
              </span>
              <span className="text-[10px] font-mono text-foreground/30">Chọn nhiều tệp ảnh cùng lúc</span>
              <input
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp,image/gif,image/bmp,image/tiff"
                className="hidden"
                onChange={(e) => {
                  const files = Array.from(e.target.files ?? []);
                  if (!files.length) return;
                  const newBlobUrls = files.map((file) => URL.createObjectURL(file));
                  onChange((current) => ({
                    ...current,
                    files: { ...current.files, existing_product_visuals: [...current.files.existing_product_visuals, ...files] },
                    input: {
                      ...current.input,
                      brand_kit: {
                        ...current.input.brand_kit,
                        existing_product_visuals: [
                          ...current.input.brand_kit.existing_product_visuals,
                          ...newBlobUrls,
                        ],
                      },
                    },
                  }));
                  toast.success(`Đã tải lên ${files.length} ảnh tư liệu.`);
                  e.target.value = "";
                }}
              />
            </label>
          </div>
        </div>

        {/* Existing Visuals Gallery Preview if any */}
        {data.brand_kit.existing_product_visuals.length > 0 && (
          <div className="space-y-1.5 pt-2">
            <span className="text-[10px] font-mono text-foreground/40 uppercase tracking-wider">
              Tư liệu banner đã nạp:
            </span>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 p-2 border border-foreground/10 bg-black/20">
              {data.brand_kit.existing_product_visuals.map((visualUrl, vIdx) => (
                <div key={vIdx} className="relative aspect-video border border-foreground/15 overflow-hidden group">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={visualUrl}
                    alt={`visual-${vIdx}`}
                    referrerPolicy="no-referrer"
                    className="w-full h-full object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const updated = data.brand_kit.existing_product_visuals.filter((_, i) => i !== vIdx);
                      brand({ existing_product_visuals: updated });
                    }}
                    className="absolute top-1 right-1 p-1 bg-red-600/80 hover:bg-red-600 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="h-2.5 w-2.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
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
  </div>
  );
};
