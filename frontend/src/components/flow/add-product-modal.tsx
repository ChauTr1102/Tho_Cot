"use client";

import * as React from "react";
import {
  ProductData,
  ProductImageItem,
  CrawlSimulationResult,
} from "@/types/campaign";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  CheckCircle2,
  Image as ImageIcon,
  Link2,
  Loader2,
  Plus,
  Star,
  Trash2,
  Upload,
  X,
} from "lucide-react";

interface AddProductModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaveProduct: (product: ProductData) => void;
}

const getPlatformMeta = (url: string): { name: string; icon: string } => {
  const lower = url.toLowerCase();
  if (lower.includes("tiktok")) return { name: "TIKTOK", icon: "▣" };
  if (lower.includes("shopee")) return { name: "SHOPEE", icon: "◈" };
  if (lower.includes("amazon")) return { name: "AMAZON", icon: "◎" };
  if (lower.includes("lazada")) return { name: "LAZADA", icon: "⬡" };
  if (lower.includes("tiki")) return { name: "TIKI", icon: "◐" };
  return { name: "E-COM", icon: "●" };
};

const makeUniqueId = (prefix: string) => {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`;
};

export const AddProductModal: React.FC<AddProductModalProps> = ({
  open,
  onOpenChange,
  onSaveProduct,
}) => {
  const [tab, setTab] = React.useState<"url" | "manual">("url");
  const [urlInput, setUrlInput] = React.useState("");
  const [isCrawling, setIsCrawling] = React.useState(false);
  const [crawledData, setCrawledData] = React.useState<CrawlSimulationResult | null>(null);
  const [title, setTitle] = React.useState("");
  const [productUrl, setProductUrl] = React.useState("");
  const [currentPrice, setCurrentPrice] = React.useState("");
  const [originalPrice, setOriginalPrice] = React.useState("");
  const [category, setCategory] = React.useState("");
  const [callToAction, setCallToAction] = React.useState("Shop now");
  const [description, setDescription] = React.useState("");
  const [images, setImages] = React.useState<ProductImageItem[]>([]);
  const [imageUrlInput, setImageUrlInput] = React.useState("");

  const platformMeta = React.useMemo(() => getPlatformMeta(urlInput), [urlInput]);

  const handleImportUrl = () => {
    if (!urlInput.trim()) { toast.error("Enter a valid product URL."); return; }
    setIsCrawling(true);
    setCrawledData(null);
    setTimeout(() => {
      let result: CrawlSimulationResult;
      const lower = urlInput.toLowerCase();
      if (lower.includes("tiktok")) {
        result = {
          title: "Lumiére Glow Lip Tint Ultra Hydrating 24h & Long Lasting",
          brand: "Lumiére Beauty", category: "Beauty & Personal Care",
          price: "189.000", originalPrice: "260.000", currency: "₫",
          images: [
            "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=600&q=80",
          ],
          description: "Vegan glass-finish lip tint with organic shea butter.",
          usps: ["Glass skin finish", "24h hydration", "100% vegan"],
          platform: "tiktok", rating: 4.9, reviewsCount: 14200, salesVolume: "48.5K+ sold",
          suggestedTone: "Gen Z Trendy", suggestedGoal: "Increase conversions",
          suggestedTargetAudience: { gender: "female", ageGroup: ["18-24", "25-34"], painPoints: ["Dry lips"], interests: ["Skincare"] },
        };
      } else if (lower.includes("shopee")) {
        result = {
          title: "MechStorm Tri-Mode Wireless Mechanical Keyboard RGB Gasket Mount",
          brand: "MechStorm", category: "Electronics & Gaming",
          price: "850.000", originalPrice: "1.250.000", currency: "₫",
          images: [
            "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?auto=format&fit=crop&w=600&q=80",
          ],
          description: "75% mechanical keyboard with Bluetooth 5.2, 2.4G and Type-C.",
          usps: ["Tri-mode connectivity", "Gasket Mount dampening", "4000mAh battery"],
          platform: "shopee", rating: 4.8, reviewsCount: 3890, salesVolume: "12.3K+ sold",
          suggestedTone: "Tech Reviewer", suggestedGoal: "Increase conversions",
          suggestedTargetAudience: { gender: "all", ageGroup: ["18-24", "25-34"], painPoints: ["Noisy keyboards"], interests: ["Gaming"] },
        };
      } else {
        result = {
          title: "AuraSound Hybrid ANC Wireless Headphones",
          brand: "AuraSound", category: "Electronics & Audio",
          price: "1.490.000", originalPrice: "2.100.000", currency: "₫",
          images: [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&q=80",
          ],
          description: "Over-ear with 38dB Hybrid ANC and 65h battery.",
          usps: ["38dB Hybrid ANC", "Hi-Res Audio", "65h battery"],
          platform: "amazon", rating: 4.9, reviewsCount: 8920, salesVolume: "25K+ sold",
          suggestedTone: "Luxury Lifestyle", suggestedGoal: "Video Ads",
          suggestedTargetAudience: { gender: "all", ageGroup: ["25-34"], painPoints: ["Noise"], interests: ["Audio"] },
        };
      }
      setCrawledData(result);
      setIsCrawling(false);
      toast.success("Product imported.");
    }, 1200);
  };

  const handleConfirmUrlImport = () => {
    if (!crawledData) return;
    const newProduct: ProductData = {
      id: makeUniqueId("prod"), name: crawledData.title, brand: crawledData.brand,
      category: crawledData.category, price: crawledData.price, originalPrice: crawledData.originalPrice,
      currency: crawledData.currency,
      images: crawledData.images.map((url, i) => ({ id: makeUniqueId("img"), url, isCover: i === 0, name: `Image ${i + 1}` })),
      description: crawledData.description, usps: crawledData.usps,
      targetAudience: crawledData.suggestedTargetAudience, toneOfVoice: crawledData.suggestedTone,
      campaignGoal: crawledData.suggestedGoal, sourceUrl: urlInput, platform: crawledData.platform,
      rating: crawledData.rating, salesVolume: crawledData.salesVolume,
    };
    onSaveProduct(newProduct); onOpenChange(false); resetModal();
    toast.success(`Added "${newProduct.name}".`);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const newImgs: ProductImageItem[] = [];
    Array.from(files).forEach((file, idx) => {
      newImgs.push({ id: makeUniqueId("file"), url: URL.createObjectURL(file), isCover: images.length === 0 && idx === 0, name: file.name });
    });
    setImages((prev) => [...prev, ...newImgs]);
    toast.success(`Uploaded ${newImgs.length} image(s).`);
    e.target.value = "";
  };

  const handleAddDirectUrl = () => {
    if (!imageUrlInput.trim()) return;
    try { new URL(imageUrlInput.trim()); } catch { toast.error("Invalid image URL."); return; }
    setImages((prev) => [...prev, { id: makeUniqueId("url"), url: imageUrlInput.trim(), isCover: images.length === 0, name: `Image ${images.length + 1}` }]);
    setImageUrlInput(""); toast.success("Image added.");
  };

  const handleSaveManualProduct = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) { toast.error("Product title required."); return; }
    const newProduct: ProductData = {
      id: makeUniqueId("prod"), name: title.trim(), category: category || "General",
      price: currentPrice.trim() || "0", originalPrice: originalPrice.trim() || undefined, currency: "₫",
      images: images.length > 0 ? images : [{ id: makeUniqueId("img-def"), url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80", isCover: true, name: "Default" }],
      description: description.trim() || "High quality product.", usps: ["Premium Quality", "Fast Shipping"],
      targetAudience: { gender: "all", ageGroup: ["18-24", "25-34"], painPoints: [], interests: [] },
      toneOfVoice: "Gen Z Trendy", campaignGoal: callToAction || "Shop now",
      sourceUrl: productUrl.trim() || undefined, platform: "custom",
    };
    onSaveProduct(newProduct); onOpenChange(false); resetModal();
    toast.success(`Saved "${newProduct.name}".`);
  };

  const resetModal = () => {
    setUrlInput(""); setCrawledData(null); setIsCrawling(false);
    setTitle(""); setProductUrl(""); setCurrentPrice(""); setOriginalPrice("");
    setCategory(""); setCallToAction("Shop now"); setDescription(""); setImages([]); setImageUrlInput("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl p-0 overflow-hidden bg-[#0a0a0a] border border-foreground/20 shadow-2xl rounded-none">
        {/* Corner accents */}
        <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-foreground/30 z-10" />
        <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-foreground/30 z-10" />

        {/* Header */}
        <div className="p-5 pb-4 border-b border-foreground/10">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-[#35ea52]" />
              <span className="text-[11px] font-mono text-foreground/30 tracking-widest uppercase">PRODUCT_ASSET</span>
            </div>
            <DialogTitle className="text-lg font-mono font-bold tracking-wider text-foreground uppercase">
              ADD.PRODUCT
            </DialogTitle>
            <p className="text-xs font-mono text-foreground/30">
              Import a public product page or enter details manually.
            </p>
          </div>

          {/* Tab Switcher — sharp brutalist */}
          <div className="flex mt-4 border border-foreground/15">
            <button
              type="button"
              onClick={() => setTab("url")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-mono tracking-wider transition-all ${
                tab === "url" ? "bg-foreground text-black font-bold" : "text-foreground/40 hover:text-foreground/60"
              }`}
            >
              <Link2 className="h-3 w-3" /> PASTE.URL
            </button>
            <div className="w-px bg-foreground/15" />
            <button
              type="button"
              onClick={() => setTab("manual")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-mono tracking-wider transition-all ${
                tab === "manual" ? "bg-foreground text-black font-bold" : "text-foreground/40 hover:text-foreground/60"
              }`}
            >
              <ImageIcon className="h-3 w-3" /> ADD.MANUALLY
            </button>
          </div>
        </div>

        {/* TAB 1: PASTE URL */}
        {tab === "url" && (
          <div className="p-5 space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-mono text-foreground/50 tracking-wider uppercase">PRODUCT.URL</label>
              <div className="relative flex items-center">
                <Input
                  placeholder="https://store.com/products/..."
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  disabled={isCrawling}
                  className="h-10 text-sm font-mono bg-transparent border-foreground/15 text-foreground/80 placeholder:text-foreground/20 pr-10 focus:border-foreground/40"
                  onKeyDown={(e) => { if (e.key === "Enter") handleImportUrl(); }}
                />
                {urlInput && (
                  <button type="button" onClick={() => { setUrlInput(""); setCrawledData(null); }}
                    className="absolute right-3 text-foreground/30 hover:text-foreground">
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-foreground/25 tracking-wider">SUPPORTED: TIKTOK · SHOPEE · AMAZON · LAZADA · TIKI</span>
                {urlInput && (
                  <span className="text-foreground/50 border border-foreground/15 px-1.5 py-0.5 tracking-wider">
                    {platformMeta.icon} {platformMeta.name}
                  </span>
                )}
              </div>
            </div>

            {isCrawling && (
              <div className="p-5 border border-foreground/10 text-center space-y-2 dither-pattern">
                <Loader2 className="h-5 w-5 text-foreground animate-spin mx-auto" />
                <p className="text-sm font-mono text-foreground/60 tracking-wider">ANALYZING.PRODUCT.LINK...</p>
              </div>
            )}

            {crawledData && !isCrawling && (
              <div className="p-4 border border-foreground/15 bg-foreground/[0.02] space-y-3 animate-in fade-in">
                <div className="flex items-center justify-between text-xs font-mono pb-2 border-b border-foreground/10">
                  <span className="text-[#35ea52] flex items-center gap-1.5 tracking-wider">
                    <CheckCircle2 className="h-3 w-3" /> DETECTED
                  </span>
                  <span className="text-foreground/30">{crawledData.salesVolume}</span>
                </div>
                <div className="flex gap-3">
                  <div className="h-16 w-16 border border-foreground/15 overflow-hidden bg-foreground/5 shrink-0">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={crawledData.images[0]} alt="product" className="w-full h-full object-cover" />
                  </div>
                  <div className="space-y-1 min-w-0 flex-1">
                    <p className="text-sm font-mono font-bold text-foreground/80 line-clamp-2">{crawledData.title}</p>
                    <p className="text-sm font-mono text-[#35ea52]">{crawledData.price} {crawledData.currency}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-foreground/10">
              <button type="button" onClick={() => onOpenChange(false)}
                className="px-4 py-2 border border-foreground/20 text-xs font-mono text-foreground/40 hover:text-foreground hover:border-foreground/40 transition-all tracking-wider">
                CANCEL
              </button>
              {crawledData ? (
                <button type="button" onClick={handleConfirmUrlImport}
                  className="px-4 py-2 bg-foreground text-black text-xs font-mono font-bold tracking-wider hover:bg-foreground/90 transition-all">
                  SAVE.ASSET
                </button>
              ) : (
                <button type="button" onClick={handleImportUrl} disabled={isCrawling || !urlInput.trim()}
                  className="px-4 py-2 border-2 border-foreground text-foreground text-xs font-mono font-bold tracking-wider hover:bg-foreground hover:text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed">
                  {isCrawling ? "IMPORTING..." : "IMPORT"}
                </button>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: ADD MANUALLY */}
        {tab === "manual" && (
          <form onSubmit={handleSaveManualProduct} className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">
                  TITLE <span className="text-[#35ea52]">*</span>
                </label>
                <Input placeholder="Product name..." value={title} onChange={(e) => setTitle(e.target.value)}
                  className="h-9 text-sm font-mono bg-transparent border-foreground/15 text-foreground/80 placeholder:text-foreground/15 focus:border-foreground/40" required />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">URL</label>
                <Input placeholder="https://..." value={productUrl} onChange={(e) => setProductUrl(e.target.value)}
                  className="h-9 text-sm font-mono bg-transparent border-foreground/15 text-foreground/80 placeholder:text-foreground/15 focus:border-foreground/40" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">PRICE</label>
                <Input placeholder="189.000" value={currentPrice} onChange={(e) => setCurrentPrice(e.target.value)}
                  className="h-9 text-sm font-mono bg-transparent border-foreground/15 text-foreground/80 placeholder:text-foreground/15 focus:border-foreground/40" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">ORIG.PRICE</label>
                <Input placeholder="260.000" value={originalPrice} onChange={(e) => setOriginalPrice(e.target.value)}
                  className="h-9 text-sm font-mono bg-transparent border-foreground/15 text-foreground/60 placeholder:text-foreground/15 focus:border-foreground/40" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">CATEGORY</label>
                <Input placeholder="Beauty / Electronics" value={category} onChange={(e) => setCategory(e.target.value)}
                  className="h-9 text-sm font-mono bg-transparent border-foreground/15 text-foreground/80 placeholder:text-foreground/15 focus:border-foreground/40" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">
                  CTA <span className="text-[#35ea52]">*</span>
                </label>
                <Input placeholder="Shop now" value={callToAction} onChange={(e) => setCallToAction(e.target.value)}
                  className="h-9 text-sm font-mono bg-transparent border-foreground/15 text-foreground/80 placeholder:text-foreground/15 focus:border-foreground/40" required />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">
                DESCRIPTION <span className="text-[#35ea52]">*</span>
              </label>
              <Textarea placeholder="Product benefits, features, ingredients..."
                value={description} onChange={(e) => setDescription(e.target.value)} rows={3}
                className="text-sm font-mono bg-transparent border-foreground/15 text-foreground/80 placeholder:text-foreground/15 leading-relaxed focus:border-foreground/40" required />
            </div>

            {/* Image Upload — brutalist */}
            <div className="space-y-2">
              <label className="text-[11px] font-mono text-foreground/40 tracking-wider uppercase">
                IMAGES <span className="text-[#35ea52]">*</span>
              </label>
              <label className="flex flex-col items-center justify-center w-full p-5 border border-dashed border-foreground/20 cursor-pointer bg-foreground/[0.01] hover:bg-foreground/[0.03] transition-colors">
                <Upload className="h-5 w-5 text-foreground/30 mb-1" />
                <p className="text-xs font-mono text-foreground/50 tracking-wider">CHOOSE.FILES</p>
                <p className="text-[11px] font-mono text-foreground/20">PNG, JPG, WEBP — Max 15MB</p>
                <input type="file" multiple accept="image/*" className="hidden" onChange={handleFileUpload} />
              </label>

              <div className="flex gap-2">
                <Input placeholder="Or paste image URL..." value={imageUrlInput} onChange={(e) => setImageUrlInput(e.target.value)}
                  className="h-8 text-xs font-mono bg-transparent border-foreground/15 text-foreground/60 placeholder:text-foreground/15 focus:border-foreground/40" />
                <button type="button" onClick={handleAddDirectUrl} disabled={!imageUrlInput.trim()}
                  className="h-8 px-3 border border-foreground/20 text-[11px] font-mono text-foreground/40 hover:bg-foreground hover:text-black transition-all disabled:opacity-30 tracking-wider shrink-0 flex items-center gap-1">
                  <Plus className="h-2.5 w-2.5" /> ADD
                </button>
              </div>

              {images.length > 0 && (
                <div className="grid grid-cols-4 sm:grid-cols-6 gap-1.5 pt-1">
                  {images.map((img) => (
                    <div key={img.id}
                      className={`relative aspect-square border overflow-hidden bg-foreground/[0.02] group ${img.isCover ? "border-foreground/50" : "border-foreground/10"}`}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={img.url} alt="asset" className="w-full h-full object-cover" />
                      {img.isCover && (
                        <span className="absolute top-0.5 left-0.5 text-[7px] font-mono font-bold bg-foreground text-black px-1">
                          COVER
                        </span>
                      )}
                      <div className="absolute inset-0 bg-background/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                        {!img.isCover && (
                          <button type="button" onClick={() => setImages(images.map((i) => ({ ...i, isCover: i.id === img.id })))}
                            className="p-1 border border-foreground/50 text-foreground hover:bg-foreground hover:text-black" title="Set cover">
                            <Star className="h-2.5 w-2.5" />
                          </button>
                        )}
                        <button type="button" onClick={() => setImages(images.filter((i) => i.id !== img.id))}
                          className="p-1 bg-red-600 text-foreground" title="Delete">
                          <Trash2 className="h-2.5 w-2.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-foreground/10">
              <span className="text-[11px] font-mono text-foreground/20 tracking-wider">VND (₫) · ACTIVE</span>
              <div className="flex items-center gap-2">
                <button type="button" onClick={() => onOpenChange(false)}
                  className="px-4 py-2 border border-foreground/20 text-xs font-mono text-foreground/40 hover:text-foreground hover:border-foreground/40 transition-all tracking-wider">
                  CANCEL
                </button>
                <button type="submit"
                  className="px-4 py-2 bg-foreground text-black text-xs font-mono font-bold tracking-wider hover:bg-foreground/90 transition-all">
                  SAVE.ASSET
                </button>
              </div>
            </div>
          </form>
        )}

        <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-foreground/30" />
        <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-foreground/30" />
      </DialogContent>
    </Dialog>
  );
};
