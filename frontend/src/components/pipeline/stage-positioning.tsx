"use client";

import * as React from "react";
import { AgentLoading } from "./agent-loading";
import { Target, Lightbulb, SplitSquareHorizontal, FileSearch, CheckCircle2, TrendingDown, RefreshCcw } from "lucide-react";

export const StagePositioning: React.FC = () => {
  const [isProcessing, setIsProcessing] = React.useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => setIsProcessing(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  const steps = [
    "Synthesizing 12 evidence points...",
    "Drafting target audience personas...",
    "Defining unique product positioning...",
    "Generating A/B testing hypotheses..."
  ];

  if (isProcessing) {
    return (
      <div className="h-full flex flex-col justify-center max-w-xl mx-auto w-full">
        <AgentLoading agentName="STRATEGY_AGENT" steps={steps} isComplete={false} />
      </div>
    );
  }

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">CHIẾN LƯỢC ĐỊNH VỊ (OUTPUT DTO)</h2>
        <p className="text-sm font-mono text-foreground/40">
          Hiển thị dữ liệu Product Positioning, A/B Testing Plan & Performance Learning.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-8 pr-2 pb-8">
        
        {/* 1. Product Positioning */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2">
            1. Product Positioning
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-foreground/10 p-5 space-y-4 bg-foreground/[0.02]">
              <div className="flex items-center gap-2 text-xs font-mono text-foreground/50 uppercase tracking-widest">
                <Target className="h-3 w-3" />
                <span>Target Audience & Angle</span>
              </div>
              <div className="space-y-3">
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">TARGET AUDIENCE</span>
                  <p className="text-sm font-mono text-foreground">Dân văn phòng, sinh viên (18-34 tuổi) cần tỉnh táo, thích sự tiện lợi.</p>
                </div>
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">MAIN CAMPAIGN ANGLE</span>
                  <p className="text-sm font-mono text-[#35ea52] font-bold">&quot;Vị đậm Việt đúng gu – Mở đầu ngày bứt tốc&quot;</p>
                </div>
              </div>
            </div>

            <div className="border border-foreground/10 p-5 space-y-4 bg-foreground/[0.02]">
              <div className="flex items-center gap-2 text-xs font-mono text-foreground/50 uppercase tracking-widest">
                <Lightbulb className="h-3 w-3" />
                <span>Message & Hierarchy</span>
              </div>
              <div className="space-y-3">
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">KEY SELLING MESSAGE</span>
                  <p className="text-sm font-mono text-foreground/80">Cà phê hòa tan 3in1 Trung Nguyên G7 – vị đậm Robusta Việt Nam, pha nhanh tiện lợi.</p>
                </div>
                <div>
                  <span className="text-[10px] text-foreground/40 block mb-1">PRODUCT BENEFIT HIERARCHY</span>
                  <ul className="text-xs font-mono text-foreground/70 space-y-1 list-disc list-inside">
                    <li>1. Đậm vị mạnh mẽ (Cảm tính)</li>
                    <li>2. Năng lượng tức thì (Lợi ích)</li>
                    <li>3. Tiện lợi 3in1 (Tính năng)</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 6. A/B Testing Plan */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <SplitSquareHorizontal className="h-4 w-4" />
            6. A/B Testing Plan
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-[#35ea52]/30 bg-[#35ea52]/[0.02] p-4 relative">
              <div className="absolute top-0 right-0 px-2 py-0.5 bg-[#35ea52] text-black text-[10px] font-mono font-bold tracking-widest">ROUTE A</div>
              <p className="text-sm font-mono text-foreground font-bold mb-1">Mở đầu &quot;Nỗi đau&quot; (Tiện lợi + Năng lượng)</p>
              <p className="text-xs font-mono text-foreground/50 mb-3">Tập trung vào sự mệt mỏi buổi sáng, giải quyết bằng việc pha nhanh một ly cà phê đậm vị.</p>
            </div>

            <div className="border border-foreground/20 bg-foreground/[0.02] p-4 relative">
              <div className="absolute top-0 right-0 px-2 py-0.5 bg-foreground text-black text-[10px] font-mono font-bold tracking-widest">ROUTE B</div>
              <p className="text-sm font-mono text-foreground font-bold mb-1">Mở đầu &quot;Uy tín & Đặc sản&quot;</p>
              <p className="text-xs font-mono text-foreground/50 mb-3">Chỉ tập trung vào hình ảnh túi 50 gói lớn, nhấn mạnh giá trị văn hóa cà phê Việt Nam uy tín toàn cầu.</p>
            </div>
          </div>
          
          <div className="bg-background/50 p-4 border border-foreground/10 flex flex-col md:flex-row gap-6">
            <div className="flex-1">
              <span className="text-[11px] font-mono text-foreground/50 block mb-1">WHAT TO TEST</span>
              <p className="text-sm font-mono text-foreground">Hiệu quả của thông điệp "Tiện lợi cá nhân" (A) so với "Quà tặng đặc sản" (B).</p>
            </div>
            <div className="flex-1">
              <span className="text-[11px] font-mono text-foreground/50 block mb-1">SUGGESTED SUCCESS METRICS</span>
              <p className="text-sm font-mono text-foreground">View Retention (3s), CTR, Add-to-cart (ATC) Rate.</p>
            </div>
            <div className="flex-1">
              <span className="text-[11px] font-mono text-foreground/50 block mb-1">EXPECTED LEARNING</span>
              <p className="text-sm font-mono text-foreground">Xác định xem khách hàng mua G7 chủ yếu để tự dùng (A) hay làm quà tặng (B) trong sự kiện 9.9.</p>
            </div>
          </div>
        </div>

        {/* 7. Performance Learning */}
        <div className="space-y-4 opacity-90">
          <h3 className="text-xs font-mono font-bold text-foreground/70 tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <RefreshCcw className="h-4 w-4" />
            7. Performance Learning (From Past Data)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="border border-[#35ea52]/20 bg-[#35ea52]/[0.02] p-4">
              <span className="text-[10px] font-mono text-[#35ea52] font-bold block mb-2 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> WHAT TO KEEP</span>
              <ul className="text-xs font-mono text-foreground/80 list-disc list-inside space-y-1">
                <li>Video ASMR pha cà phê</li>
                <li>Gói lớn 50 gói</li>
              </ul>
            </div>
            <div className="border border-yellow-500/20 bg-yellow-500/[0.02] p-4">
              <span className="text-[10px] font-mono text-yellow-500 font-bold block mb-2 flex items-center gap-1"><RefreshCcw className="h-3 w-3" /> WHAT TO CHANGE</span>
              <ul className="text-xs font-mono text-foreground/80 list-disc list-inside space-y-1">
                <li>Tối ưu phí ship để giảm tỷ lệ bỏ giỏ hàng</li>
              </ul>
            </div>
            <div className="border border-red-500/20 bg-red-500/[0.02] p-4">
              <span className="text-[10px] font-mono text-red-500 font-bold block mb-2 flex items-center gap-1"><TrendingDown className="h-3 w-3" /> WHAT TO STOP</span>
              <ul className="text-xs font-mono text-foreground/80 list-disc list-inside space-y-1">
                <li>Dừng chạy ads vào buổi tối muộn</li>
              </ul>
            </div>
            <div className="border border-foreground/20 bg-foreground/[0.02] p-4">
              <span className="text-[10px] font-mono text-foreground/60 font-bold block mb-2 flex items-center gap-1"><Target className="h-3 w-3" /> WHAT TO TEST NEXT</span>
              <ul className="text-xs font-mono text-foreground/80 list-disc list-inside space-y-1">
                <li>Bundle Mua 3 tặng 1</li>
                <li>Livestream chốt deal</li>
              </ul>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
