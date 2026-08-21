"use client";

import * as React from "react";
import { ProductData } from "@/types/campaign";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  Check,
  Clapperboard,
  Copy,
  Download,
  Image as ImageIcon,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Sparkles,
  Wand2,
} from "lucide-react";

interface GenerateAdsViewProps {
  products: ProductData[];
  selectedProduct: ProductData | null;
  onSelectProduct: (product: ProductData) => void;
  onOpenAddModal: () => void;
}

type AdType =
  | "auto"
  | "showcase"
  | "detail"
  | "ingredient"
  | "lifestyle"
  | "promo"
  | "specification";

type AspectRatioType = "1:1" | "3:2" | "2:3" | "16:9" | "9:16";

const AD_TYPES: { id: AdType; title: string; desc: string; icon: string }[] = [
  { id: "auto", title: "TỰ ĐỘNG.CHỌN", desc: "AI chọn góc tiếp cận có khả năng chuyển đổi cao", icon: "▣" },
  { id: "showcase", title: "TRƯNG BÀY.SẢN PHẨM", desc: "Ảnh chủ đạo trong studio với ánh sáng sạch", icon: "◈" },
  { id: "detail", title: "CHI TIẾT.SẢN PHẨM", desc: "Cận cảnh chất liệu và độ hoàn thiện", icon: "◎" },
  { id: "ingredient", title: "CẤU TRÚC", desc: "Hình tách lớp và các thành phần chính", icon: "⬡" },
  { id: "lifestyle", title: "PHONG CÁCH SỐNG", desc: "Bối cảnh sử dụng thực tế hằng ngày", icon: "◐" },
  { id: "promo", title: "QUẢNG CÁO.KHUYẾN MÃI", desc: "Banner ưu đãi nổi bật, CTA và nhãn khuyến mãi", icon: "⚡" },
  { id: "specification", title: "KÍCH THƯỚC.THÔNG SỐ", desc: "Kích thước và quy cách đóng gói", icon: "▧" },
];

export const GenerateAdsView: React.FC<GenerateAdsViewProps> = ({
  products,
  selectedProduct,
  onSelectProduct,
  onOpenAddModal,
}) => {
  const [workflowTab, setWorkflowTab] = React.useState<"image_create" | "image_clone" | "video_create" | "video_clone">("image_create");
  const [aspectRatio, setAspectRatio] = React.useState<AspectRatioType>("1:1");
  const [numImages, setNumImages] = React.useState<number>(2);
  const [language, setLanguage] = React.useState<string>("Vietnamese");
  const [adType, setAdType] = React.useState<AdType>("auto");
  const [customInstructions, setCustomInstructions] = React.useState("");
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [generatedResults, setGeneratedResults] = React.useState<
    Array<{ id: string; url: string; prompt: string; title: string }>
  >([]);

  React.useEffect(() => {
    if (!selectedProduct && products.length > 0) {
      onSelectProduct(products[0]);
    }
  }, [products, selectedProduct, onSelectProduct]);

  const handleGenerate = () => {
    if (!selectedProduct) {
      toast.error("Hãy chọn hoặc thêm sản phẩm trước.");
      return;
    }
    setIsGenerating(true);
    setGeneratedResults([]);
    setTimeout(() => {
      const cover = selectedProduct.images[0]?.url || "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80";
      const newOutputs = [
        {
          id: `gen-1-${Math.random().toString(36).slice(2, 8)}`,
          url: cover,
          title: `${selectedProduct.name} — Variation 1`,
          prompt: `Commercial ad for ${selectedProduct.name}, ${adType} style, ${aspectRatio} format.`,
        },
        {
          id: `gen-2-${Math.random().toString(36).slice(2, 8)}`,
          url: selectedProduct.images[1]?.url || cover,
          title: `${selectedProduct.name} — Variation 2`,
          prompt: `Dynamic social ad with bold headline for ${selectedProduct.name}.`,
        },
      ];
      if (numImages === 4) {
        newOutputs.push(
          {
            id: `gen-3-${Math.random().toString(36).slice(2, 8)}`,
            url: selectedProduct.images[2]?.url || cover,
            title: `${selectedProduct.name} — Variation 3`,
            prompt: `Lifestyle context ad for ${selectedProduct.name}.`,
          },
          {
            id: `gen-4-${Math.random().toString(36).slice(2, 8)}`,
            url: cover,
            title: `${selectedProduct.name} — Variation 4`,
            prompt: `Minimalist studio highlighting product features.`,
          }
        );
      }
      setGeneratedResults(newOutputs);
      setIsGenerating(false);
      toast.success(`Đã tạo ${newOutputs.length} mẫu quảng cáo.`);
    }, 2400);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Page Header — brutalist */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 opacity-40">
          <div className="w-6 h-px bg-foreground" />
          <span className="text-[11px] font-mono tracking-widest">∞</span>
          <div className="flex-1 h-px bg-foreground" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-wider text-foreground font-mono uppercase">
          GENERATE.ADS
        </h1>
        <p className="text-sm text-foreground/35 font-mono tracking-wider">
          Create new product ads or recreate a proven visual structure.
        </p>
      </div>

      {/* 4 Workflow Tabs — terminal buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {([
          { id: "image_create" as const, label: "TẠO.ẢNH", icon: ImageIcon },
          { id: "image_clone" as const, label: "NHÂN BẢN.ẢNH", icon: Layers },
          { id: "video_create" as const, label: "TẠO.VIDEO", icon: Clapperboard },
          { id: "video_clone" as const, label: "NHÂN BẢN.VIDEO", icon: Wand2 },
        ]).map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setWorkflowTab(tab.id)}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 text-sm font-mono tracking-wider border transition-all ${
                workflowTab === tab.id
                  ? "bg-foreground text-white border-foreground font-bold"
                  : "bg-transparent text-foreground/40 border-foreground/15 hover:border-foreground/40 hover:text-foreground/70"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Subheader info bar */}
      <div className="p-3 border border-foreground/10 bg-foreground/[0.02] flex items-center gap-3">
        <div className="h-8 w-8 border border-foreground/20 flex items-center justify-center">
          <ImageIcon className="h-4 w-4 text-foreground/50" />
        </div>
        <div>
          <h2 className="text-sm font-mono font-bold text-foreground/80 tracking-wider uppercase">
            {workflowTab === "image_create" && "IMAGE.AD.CREATION"}
            {workflowTab === "image_clone" && "IMAGE.AD.CLONING"}
            {workflowTab === "video_create" && "VIDEO.AD.CREATION"}
            {workflowTab === "video_clone" && "VIDEO.AD.CLONING"}
          </h2>
          <p className="text-xs text-foreground/25 font-mono">
            Choose a product, format, and creative direction.
          </p>
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* LEFT COLUMN — Configuration */}
        <div className="lg:col-span-7 space-y-4">
          {/* [01] CHOOSE PRODUCT */}
          <div className="border border-foreground/10 bg-background relative">
            {/* Corner accents */}
            <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-foreground/25" />
            <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-foreground/25" />

            <div className="p-4 border-b border-foreground/10 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-mono font-bold text-white bg-foreground px-1.5 py-0.5 tracking-wider">
                  01
                </span>
                <div>
                  <p className="text-sm font-mono font-bold text-foreground/80 tracking-wider">CHỌN.SẢN PHẨM</p>
                  <p className="text-[11px] text-foreground/25 font-mono">Chọn tài nguyên sản phẩm để tạo nội dung.</p>
                </div>
              </div>
              <button
                type="button"
                onClick={onOpenAddModal}
                className="flex items-center gap-1.5 px-3 py-1.5 border border-foreground/20 text-xs font-mono text-foreground/50 hover:text-foreground hover:border-foreground/50 transition-colors tracking-wider"
              >
                <Plus className="h-3 w-3" /> ADD.NEW
              </button>
            </div>

            <div className="p-4">
              {products.length === 0 ? (
                <div className="p-6 border border-dashed border-foreground/15 text-center space-y-2">
                  <p className="text-sm font-mono text-foreground/50">CHƯA CÓ TÀI NGUYÊN SẢN PHẨM</p>
                  <p className="text-xs text-foreground/25 font-mono">Nhập bằng URL hoặc thêm thủ công.</p>
                  <button
                    type="button"
                    onClick={onOpenAddModal}
                    className="text-xs font-mono border border-foreground/30 px-3 py-1.5 text-foreground/60 hover:bg-foreground hover:text-white transition-all tracking-wider"
                  >
                    + ADD.PRODUCT
                  </button>
                </div>
              ) : selectedProduct ? (
                <div className="flex items-center justify-between gap-3 p-3 border border-foreground/10 bg-foreground/[0.02]">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-12 w-12 border border-foreground/20 overflow-hidden bg-foreground/5 shrink-0">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={selectedProduct.images[0]?.url || ""}
                        alt="product"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="space-y-0.5 min-w-0">
                      <p className="text-sm font-mono font-bold text-foreground/80 truncate">{selectedProduct.name}</p>
                      <p className="text-sm font-mono text-[#35ea52]">{selectedProduct.price} {selectedProduct.currency}</p>
                    </div>
                  </div>
                  <select
                    value={selectedProduct.id}
                    onChange={(e) => {
                      const found = products.find((p) => p.id === e.target.value);
                      if (found) onSelectProduct(found);
                    }}
                    className="h-8 border border-foreground/20 bg-background px-2 text-xs font-mono text-foreground/60 focus-visible:outline-none"
                  >
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name.slice(0, 28)}...
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}
            </div>

            <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-foreground/25" />
            <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-foreground/25" />
          </div>

          {/* [02] IMAGE SETTINGS */}
          <div className="border border-foreground/10 bg-background relative">
            <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-foreground/25" />
            <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-foreground/25" />

            <div className="p-4 border-b border-foreground/10 flex items-center gap-2.5">
              <span className="text-xs font-mono font-bold text-white bg-foreground px-1.5 py-0.5 tracking-wider">
                02
              </span>
              <div>
                <p className="text-sm font-mono font-bold text-foreground/80 tracking-wider">CÀI ĐẶT.HÌNH ẢNH</p>
                <p className="text-[11px] text-foreground/25 font-mono">Kích thước, số lượng và phong cách hình ảnh.</p>
              </div>
            </div>

            <div className="p-4 space-y-5">
              {/* Aspect Ratio */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-mono text-foreground/50 tracking-wider uppercase">TỶ LỆ KHUNG HÌNH</label>
                  <span className="text-xs font-mono text-foreground/30">{aspectRatio}</span>
                </div>
                <div className="grid grid-cols-5 gap-2">
                  {([
                    { id: "1:1" as const, label: "1:1", iconClass: "w-4 h-4 border" },
                    { id: "3:2" as const, label: "3:2", iconClass: "w-5 h-3.5 border" },
                    { id: "2:3" as const, label: "2:3", iconClass: "w-3.5 h-5 border" },
                    { id: "16:9" as const, label: "16:9", iconClass: "w-6 h-3 border" },
                    { id: "9:16" as const, label: "9:16", iconClass: "w-3 h-6 border" },
                  ]).map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setAspectRatio(item.id)}
                      className={`flex flex-col items-center justify-center p-3 border text-center transition-all ${
                        aspectRatio === item.id
                          ? "bg-foreground text-white border-foreground"
                          : "bg-transparent text-foreground/40 border-foreground/10 hover:border-foreground/30"
                      }`}
                    >
                      <div className={`mb-1.5 ${item.iconClass} ${aspectRatio === item.id ? "border-black" : "border-foreground/30"}`} />
                      <span className="text-xs font-mono font-bold">{item.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Number & Language */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-foreground/50 tracking-wider uppercase">SỐ LƯỢNG ẢNH</label>
                  <select
                    value={numImages}
                    onChange={(e) => setNumImages(Number(e.target.value))}
                    className="w-full h-9 border border-foreground/15 bg-background px-3 text-sm font-mono text-foreground/70 focus-visible:outline-none"
                  >
                    <option value={1}>1</option>
                    <option value={2}>2 (mặc định)</option>
                    <option value={4}>4</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-foreground/50 tracking-wider uppercase">NGÔN NGỮ</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full h-9 border border-foreground/15 bg-background px-3 text-sm font-mono text-foreground/70 focus-visible:outline-none"
                  >
                    <option value="Vietnamese">VI — Tiếng Việt</option>
                    <option value="English">EN — English</option>
                    <option value="Japanese">JP — 日本語</option>
                  </select>
                </div>
              </div>

              {/* Ad Type Grid */}
              <div className="space-y-2">
                <label className="text-xs font-mono text-foreground/50 tracking-wider uppercase">LOẠI QUẢNG CÁO</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  {AD_TYPES.map((type) => (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setAdType(type.id)}
                      className={`p-3 border text-left transition-all flex items-start gap-2.5 ${
                        adType === type.id
                          ? "bg-foreground/5 border-foreground/50"
                          : "bg-transparent border-foreground/8 hover:border-foreground/20"
                      }`}
                    >
                      <span className="text-sm font-mono">{type.icon}</span>
                      <div className="space-y-0.5 flex-1 min-w-0">
                        <p className={`text-xs font-mono font-bold tracking-wider ${
                          adType === type.id ? "text-foreground" : "text-foreground/50"
                        }`}>
                          {type.title}
                        </p>
                        <p className="text-[11px] text-foreground/25 font-mono line-clamp-1">{type.desc}</p>
                      </div>
                      {adType === type.id && <Check className="h-3 w-3 text-[#35ea52] shrink-0 mt-0.5" />}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Instructions */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-foreground/50 tracking-wider uppercase">
                  HƯỚNG DẪN <span className="text-foreground/20">(không bắt buộc)</span>
                </label>
                <Textarea
                  placeholder="Mô tả bối cảnh, phong cách, tiêu đề hoặc yêu cầu..."
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  rows={2}
                  className="text-sm font-mono bg-transparent border-foreground/15 text-foreground/70 placeholder:text-foreground/20 focus:border-foreground/40"
                />
              </div>

              {/* Generate Button — brutalist */}
              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating || !selectedProduct}
                className="w-full h-11 border-2 border-foreground text-foreground font-mono text-sm tracking-widest uppercase flex items-center justify-center gap-2 hover:bg-foreground hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>ĐANG TẠO...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>TẠO.NỘI DUNG</span>
                  </>
                )}
              </button>
            </div>

            <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-foreground/25" />
            <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-foreground/25" />
          </div>
        </div>

        {/* RIGHT COLUMN — Live Preview */}
        <div className="lg:col-span-5">
          <div className="border border-foreground/10 bg-background relative">
            <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-foreground/25" />
            <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-foreground/25" />

            {/* Header */}
            <div className="p-4 border-b border-foreground/10 space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#35ea52]" />
                <span className="text-[11px] font-mono text-foreground/30 tracking-widest uppercase">
                  GENERATION_PREVIEW
                </span>
              </div>
              <p className="text-[15px] font-mono font-bold text-foreground/80 tracking-wider">
                GENERATED.RESULTS
              </p>
              {/* Status tags */}
              <div className="flex flex-wrap gap-2 text-[11px] font-mono">
                <span className="px-2 py-0.5 border border-foreground/10 text-foreground/35">
                  SIZE: <span className="text-foreground/60">{aspectRatio}</span>
                </span>
                <span className="px-2 py-0.5 border border-foreground/10 text-foreground/35">
                  COUNT: <span className="text-foreground/60">{numImages}</span>
                </span>
                <span className="px-2 py-0.5 border border-foreground/10 text-foreground/35">
                  TYPE: <span className="text-foreground/60">{adType.toUpperCase()}</span>
                </span>
              </div>
            </div>

            {/* Content Area */}
            <div className="p-4">
              {isGenerating ? (
                <div className="py-16 text-center space-y-4 border border-foreground/10 dither-pattern">
                  <Loader2 className="h-6 w-6 text-foreground animate-spin mx-auto" />
                  <div className="space-y-1">
                    <p className="text-sm font-mono text-foreground/70 tracking-wider">RENDERING.VARIATIONS...</p>
                    <p className="text-xs font-mono text-foreground/25">Applying composition and branding.</p>
                  </div>
                </div>
              ) : generatedResults.length === 0 ? (
                <div className="py-16 px-4 text-center border border-dashed border-foreground/15 space-y-3 dot-grid">
                  <div className="h-10 w-10 border border-foreground/20 flex items-center justify-center mx-auto">
                    <ImageIcon className="h-5 w-5 text-foreground/30" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-mono text-foreground/50 tracking-wider">CHƯA CÓ HÌNH ẢNH ĐƯỢC TẠO</p>
                    <p className="text-xs font-mono text-foreground/25 max-w-xs mx-auto">
                      Complete settings and start generation. Results will appear here.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {generatedResults.map((result) => (
                      <div key={result.id} className="group relative border border-foreground/10 overflow-hidden bg-foreground/[0.02] hover:border-foreground/30 transition-all">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={result.url} alt={result.title} className="w-full aspect-square object-cover" />
                        <div className="absolute inset-0 bg-background/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 p-2">
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(result.prompt);
                              toast.success("Prompt copied.");
                            }}
                            className="p-2 border border-foreground/50 text-foreground hover:bg-foreground hover:text-white transition-all"
                            title="Copy prompt"
                          >
                            <Copy className="h-3.5 w-3.5" />
                          </button>
                          <a
                            href={result.url}
                            target="_blank"
                            rel="noreferrer"
                            className="p-2 bg-foreground text-white hover:bg-foreground/80 transition-all"
                            title="Download"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={handleGenerate}
                    className="w-full flex items-center justify-center gap-2 py-2 border border-foreground/20 text-xs font-mono text-foreground/50 hover:text-foreground hover:border-foreground/50 transition-colors tracking-wider"
                  >
                    <RefreshCw className="h-3 w-3" /> REGENERATE
                  </button>
                </div>
              )}
            </div>

            <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-foreground/25" />
            <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-foreground/25" />
          </div>
        </div>
      </div>
    </div>
  );
};
