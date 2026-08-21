"use client";

import * as React from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Link2, Sparkles, Loader2, Edit3, Briefcase, Palette, Users, TrendingUp, History } from "lucide-react";

export const StageProductInput: React.FC = () => {
  const [inputMode, setInputMode] = React.useState<"link" | "manual">("link");
  const [url, setUrl] = React.useState("");
  const [isFetching, setIsFetching] = React.useState(false);
  const [hasFetched, setHasFetched] = React.useState(false);

  const handleFetch = async () => {
    if (!url) return;
    setIsFetching(true);
    
    try {
      const formData = new FormData();
      formData.append("campaign_id", "mock-campaign-123");
      formData.append("schema_version", "1.0");

      const productBrief = {
        product_name: "Cà Phê Hòa Tan G7 3in1 Hộp 50 Gói",
        category: "F&B / Cà phê / Hòa tan",
        key_selling_points: ["Vị đậm mạnh Robusta Buôn Ma Thuột", "Tiện lợi pha chế nhanh 3in1", "Năng lượng tức thì"],
        price_or_promotion: { price: 135000, currency: "VND", promotion: "Mua 3 Tặng 1" },
        target_market: "Trung Quốc (Cross-border)",
        required_claims: ["Cà phê số 1 Việt Nam", "Đậm vị Robusta nguyên bản"],
        restricted_or_forbidden_claims: ["Không claim chữa bệnh", "Không so sánh trực tiếp đối thủ"]
      };

      const brandKit = {
        brand_colors: { primary: "#E60000", secondary: "#000000", accent: ["#FFD700"], palette: [] },
        tone_of_voice: { description: "Năng động, Trẻ trung", attributes: [], do: ["Dùng từ mạnh mẽ"], dont: ["Không sến súa"] }
      };

      const audienceBrief = {
        target_customer: "Dân văn phòng, Sinh viên (18-34)",
        language: "Tiếng Trung (Simplified)",
        platform: "Douyin, Tmall, Taobao",
        market: "Tier 1 & Tier 2 Cities (China)"
      };

      const marketSignal = {
        trend: "Lối sống nhanh, Livestream commerce bùng nổ",
        seasonal_moment: "China 9.9 Shopping Festival",
        consumer_pain_point: "Mệt mỏi buổi sáng",
        search_keyword: ["Cà phê hòa tan đậm vị", "Cà phê Việt Nam"],
        competitor_angle: "Nestle tập trung sự êm dịu, G7 đánh mạnh độ đậm đà",
        campaign_objective: "Tăng Brand Awareness & Sales"
      };

      formData.append("product_brief", JSON.stringify(productBrief));
      formData.append("brand_kit", JSON.stringify(brandKit));
      formData.append("audience_brief", JSON.stringify(audienceBrief));
      formData.append("market_signal", JSON.stringify(marketSignal));

      // Append mock files
      const mockLogo = new Blob(["mock-logo-data"], { type: "image/png" });
      const mockPhoto = new Blob(["mock-photo-data"], { type: "image/jpeg" });
      
      formData.append("logo", mockLogo, "logo.png");
      formData.append("product_photos", mockPhoto, "photo1.jpg");
      
      const response = await fetch("http://localhost:8000/api/v1/research/run", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        console.error("API Error", await response.text());
      } else {
        const data = await response.json();
        console.log("Research Result:", data);
      }
    } catch (error) {
      console.error("Fetch failed", error);
    } finally {
      setIsFetching(false);
      setHasFetched(true);
    }
  };

  const SectionHeader = ({ icon: Icon, title }: { icon: any, title: string }) => (
    <div className="flex items-center gap-2 border-b border-foreground/10 pb-2 mb-4">
      <Icon className="h-4 w-4 text-[#35ea52]" />
      <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase">
        {title}
      </h3>
    </div>
  );

  const FormField = ({ label, defaultValue, placeholder = "", isTextarea = false }: any) => (
    <div className="space-y-1.5">
      <label className="text-[10px] font-mono text-foreground/50 uppercase tracking-wider">{label}</label>
      {isTextarea ? (
        <Textarea defaultValue={defaultValue} placeholder={placeholder} className="bg-foreground/[0.02] border-foreground/10 text-xs font-mono min-h-[80px]" />
      ) : (
        <Input defaultValue={defaultValue} placeholder={placeholder} className="h-9 bg-foreground/[0.02] border-foreground/10 text-xs font-mono" />
      )}
    </div>
  );

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">NHẬP SẢN PHẨM (INPUT DTO v2)</h2>
        <p className="text-sm font-mono text-foreground/40">
          Cung cấp dữ liệu theo chuẩn JSON định dạng mới (nested objects) cho hệ thống AI phân tích.
        </p>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto pr-2 pb-8">
        {/* Toggle Mode */}
        <div className="flex border border-foreground/10 p-1 bg-foreground/[0.02] w-fit">
          <button
            onClick={() => setInputMode("link")}
            className={`px-4 py-2 text-xs font-mono tracking-widest flex items-center gap-2 transition-colors ${
              inputMode === "link" ? "bg-foreground text-background font-bold" : "text-foreground/50 hover:text-foreground"
            }`}
          >
            <Link2 className="h-3.5 w-3.5" />
            LẤY TỪ ĐƯỜNG DẪN
          </button>
          <button
            onClick={() => setInputMode("manual")}
            className={`px-4 py-2 text-xs font-mono tracking-widest flex items-center gap-2 transition-colors ${
              inputMode === "manual" ? "bg-foreground text-background font-bold" : "text-foreground/50 hover:text-foreground"
            }`}
          >
            <Edit3 className="h-3.5 w-3.5" />
            NHẬP THỦ CÔNG
          </button>
        </div>

        {/* Link Mode Fetcher */}
        {inputMode === "link" && (
          <div className="space-y-3 p-4 border border-foreground/10 bg-background/50">
            <label className="text-xs font-mono text-foreground/60 tracking-wider">
              ĐƯỜNG DẪN SẢN PHẨM (Sẽ tự động trích xuất theo chuẩn JSON)
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Link2 className="absolute left-3 top-2.5 h-4 w-4 text-foreground/30" />
                <Input
                  placeholder="https://taobao.com/item..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="pl-9 h-10 font-mono text-sm bg-transparent border-foreground/15 focus:border-foreground/40"
                />
              </div>
              <button
                type="button"
                onClick={handleFetch}
                disabled={isFetching || !url}
                className="px-6 h-10 border border-foreground/30 bg-foreground/10 text-foreground hover:bg-foreground/20 text-xs font-mono transition-colors whitespace-nowrap flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isFetching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                TRÍCH XUẤT DỮ LIỆU
              </button>
            </div>
          </div>
        )}

        {/* The Form (Shows automatically in manual mode, or after fetch in link mode) */}
        {(inputMode === "manual" || hasFetched) && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
            
            {/* 1. Product Brief */}
            <div className="p-5 border border-foreground/10 bg-background/50 space-y-4">
              <SectionHeader icon={Briefcase} title="1. Product Brief" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField label="Product Name" defaultValue="Cà Phê Hòa Tan G7 3in1 Hộp 50 Gói" />
                <FormField label="Category" defaultValue="F&B / Cà phê / Hòa tan" />
                <div className="md:col-span-2">
                  <FormField label="Key Selling Points (CSV)" defaultValue="Vị đậm mạnh Robusta Buôn Ma Thuột, Tiện lợi pha chế nhanh 3in1, Năng lượng tức thì" />
                </div>
                <FormField label="Price (VND)" defaultValue="135000" />
                <FormField label="Promotion" defaultValue="Mua 3 Tặng 1 (Sự kiện 9.9)" />
                <FormField label="Target Market" defaultValue="Trung Quốc (Cross-border)" />
                <FormField label="Required Claims (CSV)" defaultValue="Cà phê số 1 Việt Nam, Đậm vị Robusta nguyên bản" />
                <div className="md:col-span-2">
                  <FormField label="Restricted/Forbidden Claims (CSV)" defaultValue="Không claim có tác dụng chữa bệnh, Không so sánh trực tiếp với đối thủ (Nestle)" />
                </div>
              </div>
            </div>

            {/* 2. Brand Kit */}
            <div className="p-5 border border-foreground/10 bg-background/50 space-y-4">
              <SectionHeader icon={Palette} title="2. Brand Kit" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField label="Logo Path" defaultValue="https://assets.trungnguyen.com/logo-g7.png" />
                <FormField label="Brand Colors (Primary / Secondary / Accent)" defaultValue="#E60000 / #000000 / #FFD700" />
                <div className="md:col-span-2">
                  <FormField label="Tone of Voice (Description)" defaultValue="Năng động, Trẻ trung, Trực diện, Tự hào bản sắc" />
                </div>
                <FormField label="Tone of Voice: DO (CSV)" defaultValue="Dùng từ mạnh mẽ, Tập trung vào cảm giác tỉnh táo" />
                <FormField label="Tone of Voice: DON'T (CSV)" defaultValue="Không dùng từ sến súa, Không dài dòng" />
                <div className="md:col-span-2">
                  <FormField label="Product Photos / Existing Visuals (URLs)" isTextarea defaultValue="https://assets.trungnguyen.com/g7-box-50.png&#10;https://assets.trungnguyen.com/g7-sachet.png" />
                </div>
              </div>
            </div>

            {/* 3. Audience Brief */}
            <div className="p-5 border border-foreground/10 bg-background/50 space-y-4">
              <SectionHeader icon={Users} title="3. Audience Brief" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField label="Target Customer" defaultValue="Dân văn phòng, Sinh viên (18-34 tuổi)" />
                <FormField label="Language" defaultValue="Tiếng Trung (Simplified)" />
                <FormField label="Platform" defaultValue="Douyin, Tmall, Taobao" />
                <FormField label="Market" defaultValue="Tier 1 & Tier 2 Cities (China)" />
              </div>
            </div>

            {/* 4. Market Signal */}
            <div className="p-5 border border-foreground/10 bg-background/50 space-y-4">
              <SectionHeader icon={TrendingUp} title="4. Market Signal" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField label="Trend" defaultValue="Lối sống nhanh, Livestream commerce bùng nổ" />
                <FormField label="Seasonal Moment" defaultValue="China 9.9 Shopping Festival" />
                <FormField label="Consumer Pain Point" defaultValue="Mệt mỏi, uể oải buổi sáng cần tỉnh táo nhanh chóng" />
                <FormField label="Search Keyword" defaultValue="Cà phê hòa tan đậm vị, Cà phê Việt Nam, Quà đặc sản" />
                <FormField label="Competitor Angle" defaultValue="Nestle tập trung vào sự êm dịu, G7 cần đánh mạnh vào độ đậm đà" />
                <FormField label="Campaign Objective" defaultValue="Tăng độ nhận diện (Brand Awareness) & Thúc đẩy chuyển đổi (Sales)" />
              </div>
            </div>

            {/* 5. Past Campaign Data (Optional) */}
            <div className="p-5 border border-foreground/10 bg-background/50 space-y-4 opacity-80 hover:opacity-100 transition-opacity">
              <div className="flex justify-between items-center border-b border-foreground/10 pb-2 mb-4">
                <div className="flex items-center gap-2">
                  <History className="h-4 w-4 text-[#35ea52]" />
                  <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase">
                    5. Past Campaign Data (Optional)
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-foreground/50 uppercase tracking-widest">ENABLED</span>
                  <input type="checkbox" defaultChecked className="w-3 h-3 accent-[#35ea52]" />
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <FormField label="CTR (%)" defaultValue="2.4" />
                <FormField label="CVR (%)" defaultValue="1.1" />
                <FormField label="ROAS" defaultValue="3.2" />
                <FormField label="Add To Cart Rate (%)" defaultValue="4.5" />
                <FormField label="Watch Time (Seconds)" defaultValue="4.5" />
                <FormField label="Units Sold" defaultValue="15000" />
                <FormField label="Revenue (VND)" defaultValue="2025000000" />
                <div className="col-span-2 md:col-span-4 mt-2">
                  <FormField label="Comments (CSV)" isTextarea defaultValue="Khách thích mua gói lớn làm quà, Tỷ lệ bỏ giỏ hàng cao ở bước phí ship, Cà phê thơm ngon đậm vị" />
                </div>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
};
