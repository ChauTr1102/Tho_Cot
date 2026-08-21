"use client";

import * as React from "react";
import {
  ProductData,
  ProductImageItem,
  InputMode,
  CrawlSimulationResult,
} from "@/types/campaign";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Flame,
  Globe,
  Image as ImageIcon,
  Layers,
  Link2,
  Loader2,
  Plus,
  ShoppingBag,
  Sparkles,
  Star,
  Tag,
  Trash2,
  Upload,
  UserCheck,
  Volume2,
  Wand2,
  X,
} from "lucide-react";

// Platform helper
const getPlatformMeta = (urlOrPlatform: string): { name: string; color: string; badgeClass: string; icon: string } => {
  const lower = urlOrPlatform.toLowerCase();
  if (lower.includes("tiktok") || lower === "tiktok") {
    return {
      name: "TikTok Shop",
      color: "#FE2C55",
      badgeClass: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30",
      icon: "🎵",
    };
  }
  if (lower.includes("shopee") || lower === "shopee") {
    return {
      name: "Shopee",
      color: "#EE4D2D",
      badgeClass: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30",
      icon: "🛍️",
    };
  }
  if (lower.includes("amazon") || lower === "amazon") {
    return {
      name: "Amazon",
      color: "#FF9900",
      badgeClass: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
      icon: "📦",
    };
  }
  if (lower.includes("lazada") || lower === "lazada") {
    return {
      name: "Lazada",
      color: "#0F146D",
      badgeClass: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
      icon: "🛒",
    };
  }
  if (lower.includes("tiki") || lower === "tiki") {
    return {
      name: "Tiki",
      color: "#1A94FF",
      badgeClass: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/30",
      icon: "⚡",
    };
  }
  return {
    name: "Website / Sàn TMĐT",
    color: "#6366F1",
    badgeClass: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/30",
    icon: "🌐",
  };
};

const CATEGORY_OPTIONS = [
  "Mỹ phẩm & Chăm sóc sắc đẹp",
  "Thời trang & Phụ kiện",
  "Thiết bị Công nghệ & Điện tử",
  "Gia dụng & Đời sống thông minh",
  "Mẹ & Bé / Đồ chơi",
  "Sức khỏe & Thực phẩm bổ sung",
  "Thực phẩm & Đồ uống F&B",
  "Thể thao & Dã ngoại",
  "Khác",
];

const TONE_OPTIONS = [
  { label: "Gen Z Trendy & Hài hước", desc: "Bắt trend nhanh, ngôn ngữ dí dỏm, năng động, cuốn hút giới trẻ", icon: "🔥" },
  { label: "Chuyên gia phân tích uy tín", desc: "Logic, dẫn chứng khoa học, thông số chi tiết, tạo dựng lòng tin tuyệt đối", icon: "🧠" },
  { label: "Storytelling chạm cảm xúc", desc: "Kể chuyện từ trải nghiệm đời thực, giải quyết nỗi đau của khách hàng", icon: "✨" },
  { label: "Sang trọng & Đẳng cấp Luxury", desc: "Tối giản, quý phái, nâng tầm giá trị cá nhân người sử dụng", icon: "💎" },
  { label: "Review chân thực & Khách quan", desc: "Trực quan so sánh trước/sau, test độ bền, trung thực và gần gũi", icon: "🎯" },
];

const GOAL_OPTIONS = [
  { label: "Tăng chuyển đổi TikTok Shop / Shopee", desc: "Tối ưu hóa hành vi bấm vào giỏ hàng và chốt đơn ngay lập tức" },
  { label: "Tạo Video Viral triệu view", desc: "Kịch bản kích thích chia sẻ, bình luận và lan truyền tự nhiên" },
  { label: "Chạy Quảng Cáo (Facebook / TikTok Ads)", desc: "Mở đầu 3 giây Hook mạnh, giữ chân người xem và kêu gọi CTA rõ ràng" },
  { label: "Xây dựng thương hiệu & Uy tín", desc: "Định vị sản phẩm chất lượng cao trong tâm trí khách hàng lâu dài" },
];

const SUGGESTED_USPS = [
  "Freeship toàn quốc",
  "Chiết xuất 100% tự nhiên",
  "Bảo hành 1 đổi 1 trong 12 tháng",
  "Hiệu quả rõ rệt sau 7 ngày",
  "Thiết kế công thái học gọn nhẹ",
  "Chống nước chuẩn IPX7",
  "Giá sinh viên - chất lượng cao cấp",
  "Tặng kèm quà độc quyền",
];

interface StepInputViewProps {
  onSubmitProduct?: (data: ProductData) => void;
}

export const StepInputView: React.FC<StepInputViewProps> = ({ onSubmitProduct }) => {
  const [activeTab, setActiveTab] = React.useState<InputMode>("link");

  // Link input state
  const [inputUrl, setInputUrl] = React.useState("");
  const [isCrawling, setIsCrawling] = React.useState(false);
  const [extractedData, setExtractedData] = React.useState<CrawlSimulationResult | null>(null);

  // Full form state
  const [formData, setFormData] = React.useState<ProductData>({
    name: "",
    brand: "",
    category: CATEGORY_OPTIONS[0],
    price: "",
    originalPrice: "",
    currency: "₫",
    images: [],
    description: "",
    usps: [],
    targetAudience: {
      gender: "all",
      ageGroup: ["18-24 (Gen Z)", "25-34 (Văn phòng)"],
      painPoints: [],
      interests: [],
    },
    toneOfVoice: TONE_OPTIONS[0].label,
    campaignGoal: GOAL_OPTIONS[0].label,
  });

  // Custom inputs helper
  const [customUspInput, setCustomUspInput] = React.useState("");
  const [customPainPointInput, setCustomPainPointInput] = React.useState("");
  const [imageUrlInput, setImageUrlInput] = React.useState("");
  const [showSummaryDialog, setShowSummaryDialog] = React.useState(false);

  // Auto-detect platform from current URL
  const currentPlatform = React.useMemo(() => {
    return getPlatformMeta(inputUrl);
  }, [inputUrl]);

  // Handle URL Crawl simulation
  const handleStartCrawl = async (urlToCrawl?: string) => {
    const url = urlToCrawl || inputUrl;
    if (!url.trim()) {
      toast.error("Vui lòng nhập đường link sản phẩm!");
      return;
    }

    setIsCrawling(true);
    setExtractedData(null);

    setTimeout(() => {
      let result: CrawlSimulationResult;
      const lower = url.toLowerCase();
      if (lower.includes("tiktok")) {
        result = {
          title: "Son Dưỡng Căng Mọng Glow Lip Tint Dưỡng Ẩm 24h & Khóa Màu Tự Nhiên",
          brand: "Lumiére Beauty",
          category: "Mỹ phẩm & Chăm sóc sắc đẹp",
          price: "189.000",
          originalPrice: "260.000",
          currency: "₫",
          images: [
            "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1627384113743-6bd5a479fffd?auto=format&fit=crop&w=600&q=80",
          ],
          description:
            "Dòng son tint bóng thuần chay chiết xuất dầu bơ hạt mỡ hữu cơ và Axit Hyaluronic đa phân tử giúp cấp ẩm tức thì, làm đầy rãnh môi và giữ lớp finish mọng nước suốt 8 giờ.",
          usps: [
            "Hiệu ứng tráng gương căng bóng chuẩn Glass Skin",
            "Dưỡng ẩm sâu 24h với Hyaluronic Acid",
            "Chiết xuất 100% thuần chay không chì",
            "Khóa màu tự nhiên bền suốt 8 tiếng",
          ],
          platform: "tiktok",
          rating: 4.9,
          reviewsCount: 14200,
          salesVolume: "48.5K+ đã bán",
          suggestedTone: "Gen Z Trendy & Hài hước",
          suggestedGoal: "Tăng chuyển đổi TikTok Shop / Shopee",
          suggestedTargetAudience: {
            gender: "female",
            ageGroup: ["18-24 (Gen Z)", "25-34 (Văn phòng)"],
            painPoints: ["Môi khô nứt nẻ", "Son bết dính", "Màu son mau trôi"],
            interests: ["Skincare", "Trang điểm", "Xu hướng TikTok"],
          },
        };
      } else if (lower.includes("shopee")) {
        result = {
          title: "Bàn Phím Cơ Không Dây Tri-Mode Hot-swap RGB Gasket Mount Tinh Tế",
          brand: "MechStorm Gaming",
          category: "Thiết bị Công nghệ & Điện tử",
          price: "850.000",
          originalPrice: "1.250.000",
          currency: "₫",
          images: [
            "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?auto=format&fit=crop&w=600&q=80",
          ],
          description:
            "Bàn phím cơ layout 75% gọn nhẹ, hỗ trợ 3 chế độ kết nối Type-C, Bluetooth và 2.4Ghz. Cấu trúc Gasket Mount 5 lớp tiêu âm cực êm ái.",
          usps: [
            "3 Chế độ kết nối siêu tốc (Bluetooth/2.4G/Type-C)",
            "Cấu trúc Gasket Mount tiêu âm cao cấp",
            "Pin dung lượng 4000mAh dùng 30 ngày",
          ],
          platform: "shopee",
          rating: 4.8,
          reviewsCount: 3890,
          salesVolume: "12.3K+ đã bán",
          suggestedTone: "Chuyên gia phân tích uy tín",
          suggestedGoal: "Tăng chuyển đổi TikTok Shop / Shopee",
          suggestedTargetAudience: {
            gender: "all",
            ageGroup: ["18-24 (Gen Z)", "25-34 (Văn phòng)"],
            painPoints: ["Bàn phím cũ gõ ồn", "Dây cáp vướng víu"],
            interests: ["Setup bàn làm việc", "Gaming"],
          },
        };
      } else if (lower.includes("amazon")) {
        result = {
          title: "Tai Nghe Chống Ồn Chủ Động ANC Không Dây Hi-Res Audio Bass Boost Pro",
          brand: "AuraSound International",
          category: "Thiết bị Công nghệ & Điện tử",
          price: "1.490.000",
          originalPrice: "2.100.000",
          currency: "₫",
          images: [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&q=80",
          ],
          description:
            "Tai nghe chụp tai Over-Ear với công nghệ Hybrid Active Noise Cancellation loại bỏ 95% tiếng ồn xung quanh.",
          usps: [
            "Khử ồn chủ động Hybrid ANC 38dB đỉnh cao",
            "Âm thanh chuẩn Hi-Res Audio âm bass sâu",
            "Thời lượng pin khủng 65 giờ liên tục",
          ],
          platform: "amazon",
          rating: 4.9,
          reviewsCount: 8920,
          salesVolume: "25K+ sản phẩm",
          suggestedTone: "Sang trọng & Đẳng cấp Luxury",
          suggestedGoal: "Chạy Quảng Cáo (Facebook / TikTok Ads)",
          suggestedTargetAudience: {
            gender: "all",
            ageGroup: ["25-34 (Văn phòng)", "35-45 (Gia đình)"],
            painPoints: ["Tiếng ồn môi trường làm mất tập trung", "Tai nghe đeo lâu bị đau tai"],
            interests: ["Âm nhạc chất lượng cao", "Làm việc tập trung"],
          },
        };
      } else {
        result = {
          title: "Sản Phẩm Thương Mại Điện Tử",
          brand: "Thương hiệu",
          category: "Gia dụng & Đời sống thông minh",
          price: "350.000",
          originalPrice: "499.000",
          currency: "₫",
          images: [
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80",
          ],
          description: "Sản phẩm chất lượng vượt trội, thiết kế hiện đại bắt mắt.",
          usps: ["Độ hoàn thiện cao cấp", "Bảo hành chính hãng"],
          platform: "custom",
          rating: 4.8,
          reviewsCount: 1540,
          salesVolume: "5.6K+ đã bán",
          suggestedTone: "Review chân thực & Khách quan",
          suggestedGoal: "Tăng chuyển đổi TikTok Shop / Shopee",
          suggestedTargetAudience: {
            gender: "all",
            ageGroup: ["18-24 (Gen Z)", "25-34 (Văn phòng)"],
            painPoints: ["Chưa tìm được sản phẩm ưng ý"],
            interests: ["Mua sắm tiện ích"],
          },
        };
      }

      setExtractedData(result);
      setIsCrawling(false);
      toast.success("Đã trích xuất thông tin sản phẩm thành công!");
    }, 1200);
  };

  // Transfer extracted link data into full form
  const applyExtractedDataToForm = (data: CrawlSimulationResult) => {
    setFormData({
      name: data.title,
      brand: data.brand,
      category: data.category,
      price: data.price,
      originalPrice: data.originalPrice || "",
      currency: data.currency || "₫",
      images: data.images.map((imgUrl, idx) => ({
        id: `img-${Date.now()}-${idx}`,
        url: imgUrl,
        isCover: idx === 0,
        name: `Ảnh ${idx + 1}`,
      })),
      description: data.description,
      usps: [...data.usps],
      targetAudience: {
        gender: data.suggestedTargetAudience.gender,
        ageGroup: [...data.suggestedTargetAudience.ageGroup],
        painPoints: [...data.suggestedTargetAudience.painPoints],
        interests: [...data.suggestedTargetAudience.interests],
      },
      toneOfVoice: data.suggestedTone,
      campaignGoal: data.suggestedGoal,
      sourceUrl: inputUrl,
      platform: data.platform,
      rating: data.rating,
      reviewsCount: data.reviewsCount,
      salesVolume: data.salesVolume,
    });
    setActiveTab("form");
    toast.info("Đã chuyển dữ liệu vào Form chi tiết để bạn kiểm tra và bổ sung!");
  };

  // Media handlers
  const handleAddImageUrl = () => {
    if (!imageUrlInput.trim()) return;
    try {
      new URL(imageUrlInput.trim());
    } catch {
      toast.error("Vui lòng nhập đường link URL ảnh hợp lệ!");
      return;
    }

    const newImage: ProductImageItem = {
      id: `img-custom-${Date.now()}`,
      url: imageUrlInput.trim(),
      isCover: formData.images.length === 0,
      name: `Ảnh ${formData.images.length + 1}`,
    };

    setFormData((prev) => ({
      ...prev,
      images: [...prev.images, newImage],
    }));
    setImageUrlInput("");
    toast.success("Đã thêm ảnh vào danh sách!");
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newImages: ProductImageItem[] = [];
    Array.from(files).forEach((file, index) => {
      const url = URL.createObjectURL(file);
      newImages.push({
        id: `img-file-${Date.now()}-${index}`,
        url,
        isCover: formData.images.length === 0 && index === 0,
        name: file.name,
        size: `${(file.size / 1024).toFixed(1)} KB`,
      });
    });

    setFormData((prev) => ({
      ...prev,
      images: [...prev.images, ...newImages],
    }));
    toast.success(`Đã thêm ${newImages.length} ảnh!`);
    e.target.value = "";
  };

  const handleSetCoverImage = (id: string) => {
    setFormData((prev) => ({
      ...prev,
      images: prev.images.map((img) => ({
        ...img,
        isCover: img.id === id,
      })),
    }));
    toast.success("Đã chọn làm ảnh bìa chính!");
  };

  const handleDeleteImage = (id: string) => {
    setFormData((prev) => {
      const filtered = prev.images.filter((img) => img.id !== id);
      if (filtered.length > 0 && !filtered.some((img) => img.isCover)) {
        filtered[0].isCover = true;
      }
      return {
        ...prev,
        images: filtered,
      };
    });
    toast.info("Đã xóa ảnh");
  };

  // USP Handlers
  const handleAddUsp = (uspText: string) => {
    const text = uspText.trim();
    if (!text) return;
    if (formData.usps.includes(text)) {
      toast.warning("Điểm nổi bật này đã có trong danh sách!");
      return;
    }
    setFormData((prev) => ({ ...prev, usps: [...prev.usps, text] }));
    setCustomUspInput("");
  };

  const handleRemoveUsp = (text: string) => {
    setFormData((prev) => ({ ...prev, usps: prev.usps.filter((item) => item !== text) }));
  };

  // Pain Points Handlers
  const handleAddPainPoint = (pointText: string) => {
    const text = pointText.trim();
    if (!text) return;
    if (formData.targetAudience.painPoints.includes(text)) return;
    setFormData((prev) => ({
      ...prev,
      targetAudience: {
        ...prev.targetAudience,
        painPoints: [...prev.targetAudience.painPoints, text],
      },
    }));
    setCustomPainPointInput("");
  };

  const handleRemovePainPoint = (text: string) => {
    setFormData((prev) => ({
      ...prev,
      targetAudience: {
        ...prev.targetAudience,
        painPoints: prev.targetAudience.painPoints.filter((p) => p !== text),
      },
    }));
  };

  // Submit validation & action
  const handleFinalSubmit = () => {
    if (!formData.name.trim()) {
      toast.error("Vui lòng nhập tên sản phẩm!");
      return;
    }
    if (!formData.price.trim()) {
      toast.error("Vui lòng nhập giá bán sản phẩm!");
      return;
    }

    if (onSubmitProduct) {
      onSubmitProduct(formData);
    } else {
      setShowSummaryDialog(true);
    }
    toast.success("Thông tin sản phẩm đã sẵn sàng!");
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 pb-16">
      {/* Feature Mode Switcher */}
      <div className="flex items-center justify-center">
        <div className="inline-flex p-1.5 rounded-xl bg-muted/70 border border-border max-w-md w-full shadow-sm">
          <button
            type="button"
            onClick={() => setActiveTab("link")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs sm:text-sm font-medium transition-all ${
              activeTab === "link"
                ? "bg-background text-foreground shadow-sm font-semibold border border-border/50"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Link2 className="h-4 w-4 text-primary" />
            <span>Nhập Link Sản Phẩm</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("form")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs sm:text-sm font-medium transition-all ${
              activeTab === "form"
                ? "bg-background text-foreground shadow-sm font-semibold border border-border/50"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Layers className="h-4 w-4 text-primary" />
            <span>Điền Form Đầy Đủ</span>
          </button>
        </div>
      </div>

      {/* OPTION 1: LINK IMPORT VIEW */}
      {activeTab === "link" && (
        <div className="space-y-6">
          <Card className="border-border/80 shadow-sm bg-card/60 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Wand2 className="h-4 w-4 text-primary" />
                    Quét & Phân Tích Thông Tin Tự Động
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Dán đường link sản phẩm từ TikTok Shop, Shopee, Amazon, Lazada hoặc sàn TMĐT.
                  </CardDescription>
                </div>

                {inputUrl && (
                  <Badge variant="outline" className={`w-fit text-xs ${currentPlatform.badgeClass}`}>
                    <span className="mr-1">{currentPlatform.icon}</span>
                    {currentPlatform.name}
                  </Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* URL Input Bar */}
              <div className="space-y-2">
                <div className="relative flex items-center">
                  <div className="absolute left-3.5 text-muted-foreground pointer-events-none">
                    <Globe className="h-4 w-4" />
                  </div>
                  <Input
                    placeholder="Dán link sản phẩm (TikTok Shop, Shopee, Amazon, Lazada...)"
                    value={inputUrl}
                    onChange={(e) => setInputUrl(e.target.value)}
                    disabled={isCrawling}
                    className="pl-10 pr-24 h-12 text-sm bg-background border-border"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleStartCrawl();
                    }}
                  />
                  <div className="absolute right-2 flex items-center gap-1">
                    {inputUrl && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          setInputUrl("");
                          setExtractedData(null);
                        }}
                        disabled={isCrawling}
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      type="button"
                      onClick={() => handleStartCrawl()}
                      disabled={isCrawling || !inputUrl.trim()}
                      className="h-9 px-3 gap-1.5 text-xs font-semibold"
                    >
                      {isCrawling ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          <span>Đang quét...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                          <span>Quét dữ liệu</span>
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground pt-1">
                  <span className="font-medium">Nền tảng hỗ trợ:</span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-sm">
                    🎵 TikTok Shop
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-sm">
                    🛍️ Shopee
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-sm">
                    📦 Amazon
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-sm">
                    🛒 Lazada
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-sm">
                    🌐 Sàn TMĐT khác
                  </span>
                </div>
              </div>

              {/* Crawling state */}
              {isCrawling && (
                <div className="rounded-xl border border-primary/30 bg-primary/5 p-6 text-center space-y-3">
                  <Loader2 className="h-6 w-6 text-primary animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-foreground">
                    Đang kết nối và bóc tách thông tin sản phẩm...
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Hệ thống đang trích xuất hình ảnh, thông số giá, mô tả và điểm nổi bật (USPs).
                  </p>
                </div>
              )}

              {/* Extracted Data Card */}
              {extractedData && !isCrawling && (
                <div className="rounded-xl border border-border bg-background p-5 space-y-6 shadow-sm">
                  <div className="flex items-center justify-between pb-3 border-b">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                      <span className="text-sm font-semibold text-foreground">
                        Thông Tin Sản Phẩm Trích Xuất
                      </span>
                    </div>
                    <Badge variant="outline" className={getPlatformMeta(extractedData.platform).badgeClass}>
                      {getPlatformMeta(extractedData.platform).name}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                    {/* Image Preview (4 cols) */}
                    <div className="md:col-span-4 space-y-3">
                      <div className="aspect-square rounded-lg border overflow-hidden bg-muted relative">
                        {extractedData.images[0] ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={extractedData.images[0]}
                            alt={extractedData.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                            <ImageIcon className="h-8 w-8" />
                          </div>
                        )}
                        <span className="absolute bottom-2 left-2 rounded bg-background/70 px-2 py-0.5 text-xs text-foreground font-mono">
                          {extractedData.images.length} Ảnh
                        </span>
                      </div>

                      <div className="flex gap-2 overflow-x-auto pb-1">
                        {extractedData.images.map((img, i) => (
                          <div key={i} className="h-12 w-12 rounded border overflow-hidden shrink-0">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={img} alt="thumb" className="w-full h-full object-cover" />
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Extracted Details (8 cols) */}
                    <div className="md:col-span-8 space-y-4">
                      <div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                          <span className="font-semibold text-foreground">{extractedData.brand}</span>
                          <span>•</span>
                          <span>{extractedData.category}</span>
                        </div>
                        <h3 className="text-base sm:text-lg font-bold text-foreground leading-snug">
                          {extractedData.title}
                        </h3>
                      </div>

                      {/* Price Bar */}
                      <div className="flex flex-wrap items-baseline gap-3 p-2.5 rounded-lg bg-muted/40 border">
                        <div className="text-lg font-extrabold text-primary">
                          {extractedData.price} {extractedData.currency}
                        </div>
                        {extractedData.originalPrice && (
                          <div className="text-xs text-muted-foreground line-through">
                            {extractedData.originalPrice} {extractedData.currency}
                          </div>
                        )}
                        <div className="flex items-center gap-1 text-xs text-amber-500 ml-auto font-medium">
                          <Star className="h-3.5 w-3.5 fill-amber-500 text-amber-500" />
                          <span>{extractedData.rating}</span>
                          <span className="text-muted-foreground">({extractedData.salesVolume})</span>
                        </div>
                      </div>

                      {/* USPs */}
                      <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                          <Flame className="h-3.5 w-3.5 text-amber-500" /> Điểm Nổi Bật (USPs):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {extractedData.usps.map((usp, idx) => (
                            <Badge key={idx} variant="secondary" className="text-sm font-normal py-0.5">
                              ✓ {usp}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      {/* Target audience */}
                      <div className="p-3 rounded-lg bg-muted/30 border text-xs space-y-1">
                        <div className="font-semibold text-foreground flex items-center gap-1">
                          <UserCheck className="h-3.5 w-3.5 text-primary" /> Khách hàng mục tiêu:
                        </div>
                        <p className="text-muted-foreground text-sm">
                          {extractedData.suggestedTargetAudience.ageGroup.join(", ")} •{" "}
                          {extractedData.suggestedTargetAudience.painPoints.join(" • ")}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-3 border-t">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => applyExtractedDataToForm(extractedData)}
                      className="w-full sm:w-auto gap-2 text-xs"
                    >
                      <Layers className="h-3.5 w-3.5" />
                      Chuyển Sang Form Để Chỉnh Sửa Thêm
                    </Button>
                    <Button
                      type="button"
                      onClick={() => {
                        applyExtractedDataToForm(extractedData);
                        handleFinalSubmit();
                      }}
                      className="w-full sm:w-auto gap-2 text-xs font-semibold bg-primary text-primary-foreground"
                    >
                      <span>Sử Dụng Dữ Liệu Này</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* OPTION 2: FULL FORM MANUAL INPUT VIEW */}
      {activeTab === "form" && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleFinalSubmit();
          }}
          className="space-y-6"
        >
          {/* SECTION: BASIC PRODUCT INFO */}
          <Card className="border-border/80 shadow-sm bg-card/60 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <ShoppingBag className="h-4 w-4 text-primary" />
                Thông Tin Sản Phẩm
              </CardTitle>
              <CardDescription className="text-xs">
                Tên sản phẩm, thương hiệu, ngành hàng và mức giá bán.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
                <div className="sm:col-span-8 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                    Tên sản phẩm <span className="text-rose-500">*</span>
                  </label>
                  <Input
                    placeholder="Nhập tên đầy đủ của sản phẩm..."
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-background"
                    required
                  />
                </div>

                <div className="sm:col-span-4 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Thương hiệu</label>
                  <Input
                    placeholder="Nhập tên thương hiệu (nếu có)..."
                    value={formData.brand || ""}
                    onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                    className="bg-background"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
                <div className="sm:col-span-6 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Ngành hàng</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {CATEGORY_OPTIONS.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="sm:col-span-3 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                    Giá bán <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Input
                      placeholder="189.000"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                      className="bg-background pr-8"
                      required
                    />
                    <span className="absolute right-2.5 top-2.5 text-xs text-muted-foreground font-semibold">
                      ₫
                    </span>
                  </div>
                </div>

                <div className="sm:col-span-3 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Giá gốc niêm yết</label>
                  <div className="relative">
                    <Input
                      placeholder="260.000"
                      value={formData.originalPrice || ""}
                      onChange={(e) => setFormData({ ...formData, originalPrice: e.target.value })}
                      className="bg-background pr-8 text-muted-foreground"
                    />
                    <span className="absolute right-2.5 top-2.5 text-xs text-muted-foreground font-semibold">
                      ₫
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* SECTION: IMAGES & MEDIA */}
          <Card className="border-border/80 shadow-sm bg-card/60 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <ImageIcon className="h-4 w-4 text-primary" />
                    Hình Ảnh Sản Phẩm ({formData.images.length})
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Tải ảnh từ máy tính hoặc dán link URL ảnh. Ảnh đầu tiên hoặc có ngôi sao sẽ là Ảnh Bìa chính.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                {/* File Upload (6 cols) */}
                <div className="md:col-span-6">
                  <label className="flex flex-col items-center justify-center w-full h-28 border-2 border-dashed border-border rounded-xl cursor-pointer bg-background hover:bg-muted/50 transition-colors">
                    <div className="flex flex-col items-center justify-center pt-2 pb-3 px-4 text-center">
                      <Upload className="h-6 w-6 text-muted-foreground mb-1.5" />
                      <p className="text-xs font-semibold text-foreground">
                        Tải ảnh từ máy tính
                      </p>
                      <p className="text-sm text-muted-foreground">
                        PNG, JPG, WEBP (Chọn được nhiều ảnh cùng lúc)
                      </p>
                    </div>
                    <input
                      type="file"
                      multiple
                      accept="image/*"
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                  </label>
                </div>

                {/* Direct Image URL input (6 cols) */}
                <div className="md:col-span-6 flex flex-col justify-between p-3.5 rounded-xl border bg-background space-y-2">
                  <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <Link2 className="h-3.5 w-3.5 text-primary" /> Thêm ảnh qua Link URL:
                  </span>
                  <div className="flex items-center gap-2">
                    <Input
                      placeholder="Dán link ảnh (https://...)"
                      value={imageUrlInput}
                      onChange={(e) => setImageUrlInput(e.target.value)}
                      className="text-xs h-9"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddImageUrl();
                        }
                      }}
                    />
                    <Button
                      type="button"
                      size="sm"
                      onClick={handleAddImageUrl}
                      disabled={!imageUrlInput.trim()}
                      className="h-9 px-3 shrink-0 text-xs"
                    >
                      <Plus className="h-3.5 w-3.5" /> Thêm
                    </Button>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Hỗ trợ link ảnh từ CDN sàn TMĐT, Unsplash, Imgur...
                  </span>
                </div>
              </div>

              {/* Images Grid */}
              {formData.images.length === 0 ? (
                <div className="p-6 text-center rounded-lg border border-dashed text-xs text-muted-foreground space-y-1">
                  <p className="font-medium text-foreground">Chưa có hình ảnh nào</p>
                  <p>Hãy tải ảnh lên để bổ sung tư liệu trực quan cho sản phẩm.</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 pt-2">
                  {formData.images.map((img) => (
                    <div
                      key={img.id}
                      className={`group relative rounded-lg border overflow-hidden bg-muted aspect-square transition-all ${
                        img.isCover ? "ring-2 ring-primary border-primary shadow-sm" : "hover:border-border"
                      }`}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={img.url}
                        alt={img.name || "Product image"}
                        className="w-full h-full object-cover"
                      />

                      {img.isCover && (
                        <span className="absolute top-1.5 left-1.5 bg-primary text-primary-foreground text-xs font-bold px-1.5 py-0.5 rounded shadow">
                          Ảnh bìa
                        </span>
                      )}

                      <div className="absolute inset-0 bg-background/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 p-1">
                        {!img.isCover && (
                          <Button
                            type="button"
                            variant="secondary"
                            size="icon"
                            onClick={() => handleSetCoverImage(img.id)}
                            className="h-7 w-7 text-xs"
                            title="Đặt làm ảnh bìa"
                          >
                            <Star className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Button
                          type="button"
                          variant="destructive"
                          size="icon"
                          onClick={() => handleDeleteImage(img.id)}
                          className="h-7 w-7 text-xs"
                          title="Xóa ảnh"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* SECTION: DESCRIPTION & USPs */}
          <Card className="border-border/80 shadow-sm bg-card/60 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Tag className="h-4 w-4 text-primary" />
                Mô Tả & Điểm Khác Biệt (USPs)
              </CardTitle>
              <CardDescription className="text-xs">
                Mô tả chi tiết và các điểm mạnh nổi bật của sản phẩm.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Mô tả sản phẩm</label>
                <Textarea
                  placeholder="Mô tả công dụng, tính năng, cấu tạo, chất liệu, trải nghiệm thực tế..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  className="text-xs bg-background leading-relaxed"
                />
              </div>

              {/* USPs Tag List */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Flame className="h-3.5 w-3.5 text-amber-500" />
                  Điểm Bán Hàng Độc Nhất (USPs) ({formData.usps.length})
                </label>

                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Nhập USP mới (Ví dụ: Kháng nước IPX7, Cấp ẩm 24h, Pin 60 giờ...)"
                    value={customUspInput}
                    onChange={(e) => setCustomUspInput(e.target.value)}
                    className="text-xs h-9 bg-background"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddUsp(customUspInput);
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => handleAddUsp(customUspInput)}
                    disabled={!customUspInput.trim()}
                    className="h-9 px-3 shrink-0 text-xs"
                  >
                    <Plus className="h-3.5 w-3.5" /> Thêm USP
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2 pt-1 min-h-[32px]">
                  {formData.usps.length === 0 ? (
                    <span className="text-xs text-muted-foreground italic">
                      Chưa có USP nào. Hãy nhập ở trên hoặc chọn gợi ý bên dưới!
                    </span>
                  ) : (
                    formData.usps.map((usp, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs font-medium"
                      >
                        <span>✓ {usp}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveUsp(usp)}
                          className="hover:text-destructive transition-colors ml-0.5"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))
                  )}
                </div>

                {/* Suggested USP chips */}
                <div className="pt-2">
                  <span className="text-sm text-muted-foreground font-medium block mb-1.5">
                    Gợi ý nhanh 1-click:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {SUGGESTED_USPS.map((sug, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleAddUsp(sug)}
                        className="text-sm px-2 py-0.5 rounded border bg-background hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                      >
                        + {sug}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* SECTION: TARGET AUDIENCE & TONE */}
          <Card className="border-border/80 shadow-sm bg-card/60 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Volume2 className="h-4 w-4 text-primary" />
                Khách Hàng Mục Tiêu & Định Hướng Truyền Thông
              </CardTitle>
              <CardDescription className="text-xs">
                Chân dung khách hàng, phong cách giọng điệu (Tone of Voice) và mục tiêu chiến dịch.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
                <div className="sm:col-span-4 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Giới tính mục tiêu</label>
                  <div className="grid grid-cols-3 gap-1.5">
                    {(
                      [
                        { id: "all", label: "Tất cả" },
                        { id: "female", label: "Nữ" },
                        { id: "male", label: "Nam" },
                      ] as const
                    ).map((g) => (
                      <button
                        key={g.id}
                        type="button"
                        onClick={() =>
                          setFormData({
                            ...formData,
                            targetAudience: { ...formData.targetAudience, gender: g.id },
                          })
                        }
                        className={`py-1.5 px-2 rounded-md text-xs font-medium border transition-all ${
                          formData.targetAudience.gender === g.id
                            ? "bg-primary text-primary-foreground border-primary shadow-sm"
                            : "bg-background text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {g.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="sm:col-span-8 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Nhóm độ tuổi mục tiêu</label>
                  <div className="flex flex-wrap gap-2">
                    {["18-24 (Gen Z)", "25-34 (Văn phòng)", "35-45 (Gia đình)", "45+ (Trung niên)"].map(
                      (age) => {
                        const isSelected = formData.targetAudience.ageGroup.includes(age);
                        return (
                          <button
                            key={age}
                            type="button"
                            onClick={() => {
                              setFormData({
                                ...formData,
                                targetAudience: {
                                  ...formData.targetAudience,
                                  ageGroup: isSelected
                                    ? formData.targetAudience.ageGroup.filter((a) => a !== age)
                                    : [...formData.targetAudience.ageGroup, age],
                                },
                              });
                            }}
                            className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-all ${
                              isSelected
                                ? "bg-primary text-primary-foreground border-primary shadow-sm"
                                : "bg-background text-muted-foreground hover:text-foreground"
                            }`}
                          >
                            {isSelected ? "✓ " : ""}
                            {age}
                          </button>
                        );
                      }
                    )}
                  </div>
                </div>
              </div>

              {/* Pain points */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">
                  Nỗi đau / Vấn đề khách hàng gặp phải (Pain Points)
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Nhập vấn đề khách hàng (Ví dụ: Môi khô nứt nẻ, Bàn phím gõ ồn...)"
                    value={customPainPointInput}
                    onChange={(e) => setCustomPainPointInput(e.target.value)}
                    className="text-xs h-9 bg-background"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddPainPoint(customPainPointInput);
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => handleAddPainPoint(customPainPointInput)}
                    disabled={!customPainPointInput.trim()}
                    className="h-9 px-3 shrink-0 text-xs"
                  >
                    <Plus className="h-3.5 w-3.5" /> Thêm
                  </Button>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {formData.targetAudience.painPoints.map((p, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 text-xs"
                    >
                      <span>{p}</span>
                      <button type="button" onClick={() => handleRemovePainPoint(p)}>
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Tone of Voice */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">
                  Phong cách Giọng điệu (Tone of Voice)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  {TONE_OPTIONS.map((tone) => (
                    <div
                      key={tone.label}
                      onClick={() => setFormData({ ...formData, toneOfVoice: tone.label })}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        formData.toneOfVoice === tone.label
                          ? "bg-primary/5 border-primary ring-1 ring-primary"
                          : "bg-background hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-center gap-2 font-semibold text-xs text-foreground mb-1">
                        <span>{tone.icon}</span>
                        <span>{tone.label}</span>
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {tone.desc}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Campaign Goal */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">Mục tiêu Chiến Dịch</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {GOAL_OPTIONS.map((goal) => (
                    <div
                      key={goal.label}
                      onClick={() => setFormData({ ...formData, campaignGoal: goal.label })}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        formData.campaignGoal === goal.label
                          ? "bg-primary/5 border-primary ring-1 ring-primary"
                          : "bg-background hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs font-semibold text-foreground mb-1">
                        <span>{goal.label}</span>
                        {formData.campaignGoal === goal.label && (
                          <Check className="h-3.5 w-3.5 text-primary" />
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {goal.desc}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bottom Action Bar */}
          <div className="sticky bottom-4 z-40 p-4 rounded-2xl bg-card/90 border border-border/80 shadow-2xl backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setFormData({
                    name: "",
                    brand: "",
                    category: CATEGORY_OPTIONS[0],
                    price: "",
                    originalPrice: "",
                    currency: "₫",
                    images: [],
                    description: "",
                    usps: [],
                    targetAudience: {
                      gender: "all",
                      ageGroup: ["18-24 (Gen Z)"],
                      painPoints: [],
                      interests: [],
                    },
                    toneOfVoice: TONE_OPTIONS[0].label,
                    campaignGoal: GOAL_OPTIONS[0].label,
                  });
                  toast.info("Đã làm trống form");
                }}
                className="text-xs text-muted-foreground hover:text-destructive"
              >
                Làm Trống Form
              </Button>

              <span className="text-xs text-muted-foreground hidden md:inline">
                {formData.images.length} Ảnh • {formData.usps.length} USP • {formData.toneOfVoice}
              </span>
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <Dialog open={showSummaryDialog} onOpenChange={setShowSummaryDialog}>
                <DialogTrigger asChild>
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1 sm:flex-none text-xs"
                    disabled={!formData.name}
                  >
                    Xem Tóm Tắt Dữ Liệu
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-amber-500" />
                      Tóm Tắt Hồ Sơ Sản Phẩm
                    </DialogTitle>
                    <DialogDescription className="text-xs">
                      Xem lại toàn bộ thông tin sản phẩm trước khi chuyển tiếp.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-4 text-xs py-2">
                    <div className="p-3 rounded-lg bg-muted/50 space-y-1">
                      <p className="font-semibold text-sm text-foreground">{formData.name || "(Chưa có tên)"}</p>
                      <p className="text-muted-foreground">{formData.brand} • {formData.category} • Giá: {formData.price} {formData.currency}</p>
                    </div>

                    {formData.images.length > 0 && (
                      <div className="space-y-1.5">
                        <p className="font-semibold text-foreground">Hình ảnh ({formData.images.length}):</p>
                        <div className="flex gap-2 overflow-x-auto pb-1">
                          {formData.images.map((img) => (
                            <div key={img.id} className="h-16 w-16 rounded border overflow-hidden shrink-0 relative">
                              {/* eslint-disable-next-line @next/next/no-img-element */}
                              <img src={img.url} alt="img" className="w-full h-full object-cover" />
                              {img.isCover && <span className="absolute bottom-0 inset-x-0 bg-primary text-[10px] text-center text-primary-foreground">Cover</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="space-y-1">
                      <p className="font-semibold text-foreground">Điểm nổi bật (USPs):</p>
                      <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                        {formData.usps.map((u, i) => (
                          <li key={i}>{u}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-muted-foreground p-3 rounded-lg border">
                      <div>
                        <span className="font-medium text-foreground">Tone of Voice:</span> {formData.toneOfVoice}
                      </div>
                      <div>
                        <span className="font-medium text-foreground">Mục tiêu:</span> {formData.campaignGoal}
                      </div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>

              <Button
                type="submit"
                className="flex-1 sm:flex-none gap-2 text-xs font-semibold px-6 bg-primary text-primary-foreground shadow-md"
              >
                <span>Xác Nhận & Tiếp Tục</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};
