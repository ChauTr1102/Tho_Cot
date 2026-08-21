"use client";
import * as React from "react";
import {
  Bot,
  Briefcase,
  CheckCircle2,
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
import { cn } from "@/lib/utils";
import {
  CAMPAIGN_OBJECTIVES,
  attachDefaultSampleProductPhotos,
  createEmptyResearchSubmission,
  createInitialResearchSubmission,
  type CampaignObjective,
  type ResearchSubmission,
} from "@/types/research";

const OBJECTIVE_LABELS: Record<CampaignObjective, string> = {
  awareness: "Tăng nhận biết", consideration: "Tăng cân nhắc", conversion: "Tăng đơn hàng",
  retention: "Giữ chân khách hàng", engagement: "Tăng tương tác", lead_generation: "Thu thập khách hàng tiềm năng",
};

interface Props {
  value: ResearchSubmission;
  onChange: React.Dispatch<React.SetStateAction<ResearchSubmission>>;
  initialInputMode?: "link" | "manual";
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
const inputClass = "h-9 bg-background/90 border-foreground/25 text-xs font-mono text-foreground font-medium placeholder:text-foreground/40 focus:border-[#35ea52] focus:ring-1 focus:ring-[#35ea52] shadow-sm";
const areaClass = "bg-background/90 border-foreground/25 text-xs font-mono text-foreground font-medium min-h-[88px] placeholder:text-foreground/40 focus:border-[#35ea52] focus:ring-1 focus:ring-[#35ea52] shadow-sm";

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="space-y-1.5">
      <span className="text-[11px] font-mono font-bold text-foreground/85 uppercase tracking-wider">{label}</span>
      {children}
      {hint && <span className="block text-[10.5px] font-mono text-foreground/60 font-medium">{hint}</span>}
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
    <section className="p-5 border border-foreground/15 bg-background/80 space-y-4 shadow-sm">
      <div className="flex items-center gap-2 border-b border-foreground/15 pb-2.5">
        <Icon className="h-4 w-4 text-[#35ea52]" />
        <h3 className="text-xs font-mono font-bold text-[#16A34A] dark:text-[#35ea52] tracking-widest uppercase">{title}</h3>
      </div>
      {children}
    </section>
  );
}

export const StageProductInput: React.FC<Props> = ({ value, onChange, initialInputMode = "link" }) => {
  const [inputMode, setInputMode] = React.useState<"link" | "manual">(initialInputMode);
  const [tiktokUrl, setTiktokUrl] = React.useState("");
  const [newImageUrl, setNewImageUrl] = React.useState("");
  const [isExtracting, setIsExtracting] = React.useState(false);
  const [isExtractingFile, setIsExtractingFile] = React.useState(false);
  const [extractedFileName, setExtractedFileName] = React.useState<string | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [extractedSuccess, setExtractedSuccess] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

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

  const applyExtractionPayload = (payload: any, sourceLabel: string) => {
    const pb = payload?.product_brief;
    const bk = payload?.brand_kit;
    const ab = payload?.audience_brief;
    const ms = payload?.market_signal;

    const productName = pb?.product_name || "Sản phẩm chiến dịch";
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

    const targetCustomer = toArr(ab?.target_customer || ["Khách hàng mua sắm online"]);
    const languages = toArr(ab?.language || ["vi", "en"]);
    const platforms = toArr(ab?.platform || ["TikTok Shop", "Shopee", "Facebook"]);
    const markets = toArr(ab?.market || ["Việt Nam"]);

    const trends = toArr(ms?.trend || ["Livestream Shopping", "Short-form Video Trends"]);
    const seasonalMoments = toArr(ms?.seasonal_moment || ["Mega Sale", "Mùa mua sắm"]);
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
    toast.success(`Đã trích xuất & tự động điền toàn bộ thông tin từ ${sourceLabel}!`);
  };

  const handleExtractFromUrl = async () => {
    if (!tiktokUrl.trim()) {
      toast.error("Hãy nhập URL sản phẩm hợp lệ.");
      return;
    }
    setIsExtracting(true);
    try {
      const res = await api.extractProduct({ url: tiktokUrl.trim(), render: true });
      applyExtractionPayload(res.data, "URL sản phẩm");
    } catch (error: unknown) {
      toast.error(error instanceof Error ? error.message : "Không thể trích xuất dữ liệu từ URL.");
    } finally {
      setIsExtracting(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    const validExts = [".pdf", ".docx", ".doc", ".txt", ".md", ".json"];
    const lowerName = file.name.toLowerCase();
    if (!validExts.some((ext) => lowerName.endsWith(ext))) {
      toast.error("Vui lòng tải lên file định dạng PDF, DOCX, DOC hoặc TXT.");
      return;
    }

    setIsExtractingFile(true);
    setExtractedFileName(file.name);
    try {
      const res = await api.extractDocumentFile(file);
      applyExtractionPayload(res.data, `tài liệu "${file.name}"`);
    } catch (error: unknown) {
      toast.error(error instanceof Error ? error.message : "Không thể trích xuất thông tin từ file tài liệu.");
    } finally {
      setIsExtractingFile(false);
    }
  };

  const handleResetEmpty = () => {
    onChange(createEmptyResearchSubmission());
    toast.info("Đã xóa trắng form để nhập thủ công từ đầu.");
  };

  const handleLoadSample = async () => {
    try {
      onChange(await attachDefaultSampleProductPhotos(createInitialResearchSubmission()));
      toast.success("Đã tải dữ liệu mẫu và ảnh sản phẩm G7 Coffee.");
    } catch {
      toast.error("Không thể tải ảnh sản phẩm mẫu G7.");
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="space-y-2 border-b border-foreground/15 pb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">
            THÔNG TIN SẢN PHẨM & MỤC TIÊU BÁN HÀNG
          </h2>
          <span className="text-[10px] font-mono font-bold text-[#16A34A] dark:text-[#35ea52] border border-[#35ea52]/40 bg-[#35ea52]/10 px-2 py-0.5 tracking-widest uppercase">
            2 CHẾ ĐỘ NHẬP LIỆU
          </span>
        </div>
        <p className="text-sm font-mono text-foreground/80 font-medium">
          Cung cấp đủ thông tin để nhận chiến lược, nội dung và tài sản bán hàng phù hợp với từng kênh.
        </p>

        {/* 2 OPTIONS TAB SWITCHER */}
        <div className="flex mt-3 border border-foreground/25 bg-foreground/[0.03]">
          <button
            type="button"
            onClick={() => setInputMode("link")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-mono tracking-wider transition-all ${
              inputMode === "link"
                ? "bg-[#28C840] text-white font-bold shadow-md"
                : "text-foreground/80 font-bold hover:text-foreground hover:bg-foreground/[0.08]"
            }`}
          >
            <Link2 className="h-3.5 w-3.5" />
            DÁN LINK SẢN PHẨM
          </button>
          <div className="w-px bg-foreground/25" />
          <button
            type="button"
            onClick={() => setInputMode("manual")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-mono tracking-wider transition-all ${
              inputMode === "manual"
                ? "bg-[#28C840] text-white font-bold shadow-md"
                : "text-foreground/80 font-bold hover:text-foreground hover:bg-foreground/[0.08]"
            }`}
          >
            <PenLine className="h-3.5 w-3.5" />
            NHẬP THÔNG TIN THỦ CÔNG
          </button>
        </div>
      </div>

      {/* OPTION 1: LINK IMPORT VIEW */}
      {inputMode === "link" && (
        <div className="p-4 border border-[#35ea52]/40 bg-[#35ea52]/[0.04] space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#16A34A] dark:text-[#35ea52]" />
              <span className="text-xs font-mono font-bold tracking-wider text-foreground uppercase">
                LẤY THÔNG TIN TỪ LINK SẢN PHẨM
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold text-foreground/70">TỰ ĐỘNG ĐỌC & ĐIỀN FORM</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Link2 className="absolute left-3 top-2.5 h-4 w-4 text-foreground/50" />
              <Input
                placeholder="https://... (Dán link sản phẩm tại đây)"
                value={tiktokUrl}
                onChange={(e) => setTiktokUrl(e.target.value)}
                disabled={isExtracting}
                className="h-9 pl-9 text-xs font-mono font-medium bg-background border-foreground/30 text-foreground placeholder:text-foreground/45 focus:border-[#35ea52]"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleExtractFromUrl();
                }}
              />
            </div>
            <button
              type="button"
              onClick={handleExtractFromUrl}
              disabled={isExtracting || !tiktokUrl.trim()}
              className="h-9 px-4 bg-[#35ea52] text-black text-xs font-mono font-bold tracking-wider hover:bg-[#35ea52]/90 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 shrink-0 shadow-sm"
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

          <div className="flex items-center justify-between text-[11px] font-mono font-medium text-foreground/75 pt-1">
            <span>
              {extractedSuccess
                ? "✓ Đã tự động điền form bên dưới. Bạn có thể kiểm tra và chỉnh sửa nếu cần."
                : "Hệ thống sẽ tự động phân tích sản phẩm, thương hiệu, giá, USPs, tệp khách hàng và tín hiệu thị trường."}
            </span>
          </div>
        </div>
      )}

      {/* OPTION 2: MANUAL CONTROLS & DOC/PDF UPLOADER */}
      {inputMode === "manual" && (
        <div className="space-y-3 animate-in fade-in duration-200">
          <div className="p-3 border border-foreground/20 bg-foreground/[0.03] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <PenLine className="h-4 w-4 text-foreground/70" />
              <span className="text-xs font-mono font-semibold text-foreground/85">
                CHẾ ĐỘ TỰ ĐIỀN THỦ CÔNG: Nhập thông tin chi tiết hoặc tải file tài liệu để AI tự điền.
              </span>
            </div>
            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.txt,.md,.json"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleFileUpload(file);
                  e.target.value = "";
                }}
              />
              <button
                type="button"
                disabled={isExtractingFile}
                onClick={() => fileInputRef.current?.click()}
                className="h-7 px-3 bg-[#35ea52] text-black text-[11px] font-mono font-bold tracking-wider hover:bg-[#35ea52]/90 transition-all flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
              >
                {isExtractingFile ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin" />
                    ĐANG ĐỌC FILE...
                  </>
                ) : (
                  <>
                    <Upload className="h-3 w-3" />
                    TẢI FILE DOC / PDF
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleResetEmpty}
                className="h-7 px-3 border border-foreground/30 text-[11px] font-mono font-semibold text-foreground/80 hover:text-foreground hover:border-foreground/60 transition-all flex items-center gap-1.5"
              >
                <RotateCcw className="h-3 w-3" />
                XÓA TRẮNG FORM
              </button>
              <button
                type="button"
                onClick={handleLoadSample}
                className="h-7 px-3 border border-[#35ea52]/50 text-[#16A34A] dark:text-[#35ea52] text-[11px] font-mono font-bold hover:bg-[#35ea52]/10 transition-all flex items-center gap-1.5"
              >
                <FileText className="h-3 w-3" />
                TẢI DỮ LIỆU MẪU
              </button>
            </div>
          </div>

          {/* Drag & Drop Document Card */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const file = e.dataTransfer.files?.[0];
              if (file) void handleFileUpload(file);
            }}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "p-3.5 border border-dashed text-center cursor-pointer transition-all bg-background/60 flex flex-col sm:flex-row items-center justify-between gap-3",
              isDragging
                ? "border-[#35ea52] bg-[#35ea52]/10 shadow-sm"
                : "border-foreground/30 hover:border-[#35ea52] hover:bg-foreground/[0.03]"
            )}
          >
            <div className="flex items-center gap-3 text-left">
              <div className="size-8 rounded-none border border-[#35ea52]/50 bg-[#35ea52]/15 grid place-items-center text-[#16A34A] dark:text-[#35ea52] shrink-0 font-bold">
                {isExtractingFile ? <Loader2 className="size-4 animate-spin" /> : <FileText className="size-4" />}
              </div>
              <div>
                <p className="text-xs font-mono font-bold text-foreground flex items-center gap-2">
                  <span>KÉO THẢ HOẶC CHỌN FILE BRIEF / SPEC SHEET (PDF, DOCX, TXT)</span>
                  {extractedFileName && (
                    <span className="text-[10px] text-[#16A34A] dark:text-[#35ea52] font-semibold border border-[#35ea52]/40 bg-[#35ea52]/10 px-1.5 py-0.2">
                      Đã đọc: {extractedFileName}
                    </span>
                  )}
                </p>
              </div>
            </div>
            <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-[#16A34A] dark:text-[#35ea52] border border-[#35ea52]/50 bg-[#35ea52]/5 px-2.5 py-1 shrink-0 hover:bg-[#35ea52]/15">
              <Upload className="size-3" />
              CHỌN TÀI LIỆU
            </span>
          </div>
        </div>
      )}

      {/* DETAILED FORM SECTIONS: ALWAYS VISIBLE */}
      <div className="flex-1 space-y-6 overflow-y-auto pr-2 pb-8">
        {/* Loading Banner when extracting */}
        {isExtracting && (
          <div className="p-3.5 border border-[#35ea52]/50 bg-[#35ea52]/10 flex items-center gap-3 animate-in fade-in duration-200">
            <Loader2 className="h-4 w-4 text-[#35ea52] animate-spin shrink-0" />
            <div>
              <h4 className="text-xs font-mono font-bold text-foreground">
                HỆ THỐNG ĐANG PHÂN TÍCH LINK SẢN PHẨM & TỰ ĐỘNG ĐIỀN FORM...
              </h4>
              <p className="text-[11px] font-mono text-foreground/70">
                Thông số, hình ảnh và phân khúc khách hàng sẽ xuất hiện trực tiếp trong các ô bên dưới.
              </p>
            </div>
          </div>
        )}

        {/* Success Banner when link extracted */}
        {inputMode === "link" && extractedSuccess && (
          <div className="p-3 border border-[#35ea52]/40 bg-[#35ea52]/[0.05] flex flex-wrap items-center justify-between gap-3 animate-in fade-in duration-200">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#35ea52]" />
              <span className="text-xs font-mono font-bold text-foreground">
                ĐÃ NẠP DỮ LIỆU TỪ LINK:{" "}
                <span className="text-[#16A34A] dark:text-[#35ea52]">{data.product_brief.product_name || "Sản phẩm"}</span>
              </span>
            </div>
            <button
              type="button"
              onClick={() => {
                setExtractedSuccess(false);
                setTiktokUrl("");
              }}
              className="h-7 px-3 border border-foreground/30 text-[11px] font-mono font-bold text-foreground/80 hover:text-foreground transition-all"
            >
              Trích xuất link khác
            </button>
          </div>
        )}

        <Section icon={Briefcase} title="1. Thông tin sản phẩm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Mã chiến dịch *">
              <Input
                className={inputClass}
                value={data.campaign_id}
                onChange={(e) => setInput({ ...data, campaign_id: e.target.value })}
              />
            </Field>
            <Field label="Tên sản phẩm *">
              <Input
                className={inputClass}
                value={data.product_brief.product_name}
                onChange={(e) => product({ product_name: e.target.value })}
              />
            </Field>
            <Field label="Ngành hàng *">
              <Input
                className={inputClass}
                value={data.product_brief.category}
                onChange={(e) => product({ category: e.target.value })}
              />
            </Field>
            <Field label="Ưu đãi / khuyến mãi">
              <Input
                className={inputClass}
                value={data.product_brief.promotion ?? ""}
                onChange={(e) => product({ promotion: e.target.value || null })}
              />
            </Field>
            <ListField
              label="Điểm bán hàng nổi bật"
              required
              value={data.product_brief.key_selling_points}
              onChange={(key_selling_points) => product({ key_selling_points })}
            />
            <ListField
              label="Thị trường mục tiêu"
              required
              value={data.product_brief.target_market}
              onChange={(target_market) => product({ target_market })}
            />
            <ListField
              label="Thông tin bắt buộc phải nhắc"
              value={data.product_brief.required_claims}
              onChange={(required_claims) => product({ required_claims })}
            />
            <ListField
              label="Nội dung không được sử dụng"
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
            <Field label="Đơn vị tiền tệ">
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
            <Field label="Đơn vị bán">
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
            <Field label="Ghi chú giá">
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
            <label className="text-[11px] font-mono font-bold text-foreground/85 uppercase tracking-wider">
              Tên màu thương hiệu *
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
            <label className="text-[11px] font-mono font-bold text-foreground/85 uppercase tracking-wider">
              Mã màu thương hiệu
            </label>
            <div className="flex items-center gap-2">
              <div
                className="w-9 h-9 border border-foreground/30 shrink-0 shadow-inner"
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
            label="Giọng điệu thương hiệu"
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
        <div className="space-y-3 pt-3 border-t border-foreground/15">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ImageIcon className="h-4 w-4 text-[#35ea52]" />
              <span className="text-xs font-mono font-bold tracking-wider text-foreground uppercase">
                ẢNH SẢN PHẨM ({data.brand_kit.product_photos.length}) <span className="text-[#35ea52]">*</span>
              </span>
            </div>
            {data.brand_kit.product_photos.length > 0 && (
              <span className="text-[10px] font-mono font-bold text-[#16A34A] dark:text-[#35ea52] bg-[#35ea52]/10 px-2 py-0.5 border border-[#35ea52]/40">
                ✓ {data.brand_kit.product_photos.length} ảnh đã nạp
              </span>
            )}
          </div>

          {/* Photo Grid Preview */}
          {data.brand_kit.product_photos.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2.5 p-3 border border-foreground/20 bg-black/40">
              {data.brand_kit.product_photos.map((photoUrl, idx) => (
                <div
                  key={idx}
                  className={`relative aspect-square border group overflow-hidden bg-foreground/[0.03] transition-all ${
                    idx === 0 ? "border-[#35ea52]/70 ring-1 ring-[#35ea52]/40" : "border-foreground/25"
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
                  <div className="absolute top-1 left-1 bg-black/85 px-1.5 py-0.5 text-[9px] font-mono font-bold text-white border border-white/20 flex items-center gap-1">
                    <span>#{idx + 1}</span>
                    {idx === 0 && <span className="text-[#35ea52]">ẢNH BÌA</span>}
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
                        className="p-1.5 bg-white/25 hover:bg-[#35ea52] hover:text-black text-white rounded text-[10px] font-mono font-bold transition-colors"
                        title="Đặt làm ảnh bìa"
                      >
                        Bìa
                      </button>
                    )}
                    <a
                      href={photoUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1.5 bg-white/25 hover:bg-white/40 text-white rounded transition-colors"
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
                className="h-9 text-xs font-mono font-medium bg-background border-foreground/30 text-foreground placeholder:text-foreground/45 focus:border-[#35ea52]"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAddImageUrl();
                }}
              />
              <button
                type="button"
                onClick={handleAddImageUrl}
                disabled={!newImageUrl.trim()}
                className="h-9 px-4 border border-[#35ea52] bg-[#35ea52]/10 text-[#16A34A] dark:text-[#35ea52] text-xs font-mono font-bold hover:bg-[#35ea52] hover:text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed shrink-0 flex items-center gap-1 shadow-sm"
              >
                <Plus className="h-3.5 w-3.5" /> THÊM URL
              </button>
            </div>

            {/* Custom Styled File Upload Button */}
            <div className="md:col-span-4">
              <label className="h-9 px-3 border border-dashed border-foreground/30 hover:border-[#35ea52] bg-background/80 hover:bg-foreground/[0.04] cursor-pointer flex items-center justify-center gap-2 text-xs font-mono font-bold text-foreground/80 hover:text-foreground transition-all shadow-sm">
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-foreground/15">
          {/* Logo Card */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-mono font-bold text-foreground/85 uppercase tracking-wider flex items-center justify-between">
              <span>Logo thương hiệu (không bắt buộc)</span>
              {value.files.logo && (
                <span className="text-[#16A34A] dark:text-[#35ea52] font-mono font-bold text-[10.5px]">✓ {value.files.logo.name}</span>
              )}
            </label>
            <label className="flex flex-col items-center justify-center p-4 border border-dashed border-foreground/25 hover:border-[#35ea52] bg-background/60 hover:bg-foreground/[0.03] cursor-pointer transition-all min-h-[90px] group shadow-sm">
              <Upload className="h-4 w-4 text-foreground/50 group-hover:text-[#35ea52] transition-colors mb-1" />
              <span className="text-xs font-mono font-bold text-foreground/80 group-hover:text-foreground tracking-wider">
                {value.files.logo ? "BẤM ĐỂ ĐỔI LOGO" : "CHỌN TỆP LOGO (PNG, SVG, JPG)"}
              </span>
              <span className="text-[10.5px] font-mono font-medium text-foreground/55 mt-0.5">Kích thước tối đa 10 MB</span>
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
            <label className="text-[11px] font-mono font-bold text-foreground/85 uppercase tracking-wider flex items-center justify-between">
              <span>Hình ảnh banner / tư liệu hiện có</span>
              {data.brand_kit.existing_product_visuals.length > 0 && (
                <span className="text-[#16A34A] dark:text-[#35ea52] font-mono font-bold text-[10.5px]">
                  ✓ {data.brand_kit.existing_product_visuals.length} tư liệu
                </span>
              )}
            </label>
            <label className="flex flex-col items-center justify-center p-4 border border-dashed border-foreground/25 hover:border-[#35ea52] bg-background/60 hover:bg-foreground/[0.03] cursor-pointer transition-all min-h-[90px] group shadow-sm">
              <Upload className="h-4 w-4 text-foreground/50 group-hover:text-[#35ea52] transition-colors mb-1" />
              <span className="text-xs font-mono font-bold text-foreground/80 group-hover:text-foreground tracking-wider">
                TẢI LÊN BANNER / TƯ LIỆU QUẢNG CÁO
              </span>
              <span className="text-[10.5px] font-mono font-medium text-foreground/55 mt-0.5">Chọn nhiều tệp ảnh cùng lúc</span>
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
            <span className="text-[10.5px] font-mono font-bold text-foreground/70 uppercase tracking-wider">
              Tư liệu banner đã nạp:
            </span>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 p-2 border border-foreground/15 bg-black/20">
              {data.brand_kit.existing_product_visuals.map((visualUrl, vIdx) => (
                <div key={vIdx} className="relative aspect-video border border-foreground/20 overflow-hidden group">
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
        <ListField label="Nhóm khách hàng" required value={data.audience_brief.target_customer} onChange={(target_customer) => audience({ target_customer })} />
        <ListField label="Ngôn ngữ nội dung" required value={data.audience_brief.languages} onChange={(languages) => audience({ languages })} />
        <ListField label="Kênh bán hàng" required value={data.audience_brief.platforms} onChange={(platforms) => audience({ platforms })} />
        <ListField label="Khu vực bán" required value={data.audience_brief.markets} onChange={(markets) => audience({ markets })} />
      </div></Section>
      <Section icon={TrendingUp} title="4. Tín hiệu thị trường">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ListField label="Xu hướng liên quan" value={data.market_signal.trends} onChange={(trends) => market({ trends })} />
          <ListField label="Dịp bán hàng / mùa vụ" value={data.market_signal.seasonal_moments} onChange={(seasonal_moments) => market({ seasonal_moments })} />
          <ListField label="Vấn đề khách hàng đang gặp" value={data.market_signal.consumer_pain_points} onChange={(consumer_pain_points) => market({ consumer_pain_points })} />
          <ListField label="Từ khóa khách hàng tìm kiếm" value={data.market_signal.search_keywords} onChange={(search_keywords) => market({ search_keywords })} />
          <ListField label="Góc truyền thông của đối thủ" value={data.market_signal.competitor_angles} onChange={(competitor_angles) => market({ competitor_angles })} />
        </div>
        <fieldset className="space-y-2"><legend className="text-[11px] font-mono font-bold text-foreground/85 uppercase tracking-wider">Mục tiêu chiến dịch *</legend><div className="flex flex-wrap gap-4">{CAMPAIGN_OBJECTIVES.map((objective) => <label key={objective} className="flex items-center gap-2 text-xs font-mono font-semibold text-foreground/85 hover:text-foreground cursor-pointer"><input type="checkbox" className="accent-[#35ea52] h-4 w-4" checked={data.market_signal.campaign_objectives.includes(objective)} onChange={(e) => market({ campaign_objectives: e.target.checked ? [...data.market_signal.campaign_objectives, objective] : data.market_signal.campaign_objectives.filter((item: CampaignObjective) => item !== objective) })} />{OBJECTIVE_LABELS[objective]}</label>)}</div></fieldset>
      </Section>
    </div>
  </div>
  );
};
