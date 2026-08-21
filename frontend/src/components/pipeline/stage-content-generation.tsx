"use client";

import * as React from "react";
import { AgentLoading } from "./agent-loading";
import { Play, AlignLeft, Sparkles, MessageSquare } from "lucide-react";

export const StageContentGeneration: React.FC = () => {
  const [isProcessing, setIsProcessing] = React.useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => setIsProcessing(false), 3500);
    return () => clearTimeout(timer);
  }, []);

  const steps = [
    "Developing Creative Route A (Pain Point)...",
    "Developing Creative Route B (Aesthetic)...",
    "Drafting Commerce Copy...",
    "Finalizing SEO metadata..."
  ];

  if (isProcessing) {
    return (
      <div className="h-full flex flex-col justify-center max-w-xl mx-auto w-full">
        <AgentLoading agentName="CONTENT_GENERATOR_AGENT" steps={steps} isComplete={false} />
      </div>
    );
  }

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">SÁNG TẠO NỘI DUNG (OUTPUT DTO)</h2>
        <p className="text-sm font-mono text-foreground/40">
          Hiển thị dữ liệu Creative Routes và Commerce Copy.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-8 pr-2 pb-8">
        
        {/* 2. Creative Routes */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            2. Creative Routes
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="border border-foreground/10 p-5 space-y-4 bg-background">
              <div className="flex justify-between items-center border-b border-foreground/5 pb-2">
                <span className="text-xs font-mono font-bold text-[#35ea52]">ROUTE A: Pain Point</span>
                <span className="text-[10px] font-mono text-foreground/40 bg-foreground/5 px-2 py-0.5">Douyin, TikTok</span>
              </div>
              <div className="space-y-3">
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">HOOK IDEA</span>
                  <p className="text-sm font-mono text-foreground">Cảnh báo thức dậy muộn mệt mỏi, ngay lập tức xé gói G7 pha nước nóng khói bốc lên.</p>
                </div>
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">VISUAL DIRECTION</span>
                  <p className="text-sm font-mono text-foreground">Nhịp độ nhanh, màu sắc rực rỡ buổi sáng, ASMR tiếng rót nước, cận cảnh bọt cà phê.</p>
                </div>
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">MESSAGE ANGLE</span>
                  <p className="text-sm font-mono text-foreground/70">"Đừng để sự uể oải cản bước bạn. Nạp năng lượng với G7 vị đậm Việt Nam!"</p>
                </div>
              </div>
            </div>

            <div className="border border-foreground/10 p-5 space-y-4 bg-background">
              <div className="flex justify-between items-center border-b border-foreground/5 pb-2">
                <span className="text-xs font-mono font-bold text-foreground/80">ROUTE B: Cultural Authority</span>
                <span className="text-[10px] font-mono text-foreground/40 bg-foreground/5 px-2 py-0.5">Taobao, Tmall</span>
              </div>
              <div className="space-y-3">
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">HOOK IDEA</span>
                  <p className="text-sm font-mono text-foreground">Đóng gói combo 50 gói siêu lớn, thích hợp làm quà tặng đặc sản Việt Nam cho đối tác, gia đình.</p>
                </div>
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">VISUAL DIRECTION</span>
                  <p className="text-sm font-mono text-foreground">Sang trọng, ánh sáng ấm, tone màu đỏ đen chủ đạo, Typography nhấn mạnh thương hiệu xuất khẩu toàn cầu.</p>
                </div>
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">MESSAGE ANGLE</span>
                  <p className="text-sm font-mono text-foreground/70">"Mang hương vị cà phê Robusta chuẩn Việt đến mọi nhà. Sang trọng, tiện lợi."</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 5. Commerce Copy */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            5. Commerce Copy
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="border border-foreground/10 bg-foreground/[0.02] p-4 space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-foreground/40 block">PRODUCT TITLE (SEO)</span>
                <p className="text-sm font-mono font-bold text-foreground">✨ Cà phê hòa tan 3in1 Trung Nguyên G7 (Hộp 50 gói) - Đậm vị Robusta Việt Nam ✨</p>
              </div>
              
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-foreground/40 block">PROMOTION COPY</span>
                <p className="text-sm font-mono text-red-500 font-bold border border-red-500/20 bg-red-500/5 p-2 inline-block">🔥 SALE CHINA 9.9: MUA 3 TẶNG 1 FREESHIP! 🔥</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-mono text-foreground/40 block">LISTING BULLET POINTS</span>
                <ul className="text-sm font-mono text-foreground/80 space-y-1 list-disc list-inside">
                  <li>Chiết xuất từ 100% hạt Robusta Buôn Ma Thuột.</li>
                  <li>Tiện lợi pha chế chỉ với 1 phút.</li>
                  <li>Hộp lớn 50 gói siêu tiết kiệm.</li>
                  <li>Thương hiệu quốc gia, xuất khẩu hơn 100 nước.</li>
                </ul>
              </div>
            </div>

            <div className="border border-foreground/10 bg-foreground/[0.02] p-4 space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-foreground/40 block">PRODUCT DESCRIPTION</span>
                <p className="text-sm font-mono text-foreground/80 leading-relaxed">
                  Trải nghiệm năng lượng bứt phá mỗi sáng với Cà phê G7 3in1. Sự kết hợp hoàn hảo giữa cà phê đậm đặc, vị béo của kem và ngọt của đường, mang lại một tách cà phê thơm lừng, chuẩn vị Việt ngay tại văn phòng hay ở nhà.
                </p>
              </div>

              <div className="space-y-1 border-t border-foreground/10 pt-3">
                <span className="text-[10px] font-mono text-foreground/40 block">AD CAPTION (Douyin)</span>
                <p className="text-sm font-mono text-foreground/80">
                  Mệt mỏi buổi sáng? 😪 Nạp ngay 1 ly G7 vị đậm Việt Nam để bứt tốc! Chạm góc trái mua ngay combo hời 9.9 nhé! 🛒 #CaPheG7 #TrungNguyen #China99
                </p>
              </div>

              <div className="space-y-1 border-t border-foreground/10 pt-3">
                <span className="text-[10px] font-mono text-foreground/40 block">SHORT HOOK LINES</span>
                <div className="flex flex-wrap gap-2">
                  <span className="px-2 py-1 bg-foreground/10 text-xs font-mono rounded-sm">Chỉ 1 phút cho vị đậm đà!</span>
                  <span className="px-2 py-1 bg-foreground/10 text-xs font-mono rounded-sm">Năng lượng G7, bứt phá ngày dài.</span>
                  <span className="px-2 py-1 bg-foreground/10 text-xs font-mono rounded-sm">Đặc sản Việt Nam.</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
