"use client";

import * as React from "react";
import { FolderKanban, Play, Image as ImageIcon, Video, Package } from "lucide-react";

export const StageFinalOutput: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">TÀI SẢN CHIẾN DỊCH</h2>
        <p className="text-sm font-mono text-foreground/40">
          Hiển thị dữ liệu Short-form Video Asset & Product Collection Image Set.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-8 pr-2 pb-8">
        
        {/* Summary Card */}
        <div className="border border-[#35ea52]/30 bg-[#35ea52]/[0.02] p-5 flex items-start gap-4">
          <FolderKanban className="h-8 w-8 text-[#35ea52] shrink-0" />
          <div className="space-y-2">
            <h3 className="text-[14px] font-mono font-bold text-foreground tracking-widest">CHIẾN DỊCH: CÀ PHÊ G7 - CHINA 9.9</h3>
            <p className="text-sm font-mono text-foreground/70 leading-relaxed max-w-2xl">
              Tài sản chiến dịch đã được render hoàn chỉnh. Các tài sản có thể được tải xuống trực tiếp hoặc chuyển sang luồng Deploy.
            </p>
            <div className="flex gap-2 mt-2">
              <span className="px-2 py-0.5 border border-[#35ea52]/30 text-[#35ea52] text-[11px] font-mono">2 VIDEO</span>
              <span className="px-2 py-0.5 border border-[#35ea52]/30 text-[#35ea52] text-[11px] font-mono">5 HÌNH ẢNH</span>
            </div>
          </div>
        </div>

        {/* 3. Short-form Video Asset */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <Video className="h-4 w-4" />
            3. Short-form Video Asset
          </h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            
            <div className="border border-foreground/10 bg-background p-3 space-y-3 relative group">
              <div className="absolute top-0 right-0 px-2 py-0.5 bg-foreground text-black text-[10px] font-mono font-bold">15-30s | 9:16</div>
              <div className="aspect-[9/16] bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center relative overflow-hidden group-hover:bg-foreground/[0.05] transition-colors cursor-pointer">
                <div className="absolute inset-0 dot-grid opacity-50" />
                <Play className="h-8 w-8 text-[#35ea52] relative z-10 opacity-70 group-hover:opacity-100 transition-opacity" />
              </div>
              <div>
                <p className="text-sm font-mono font-bold text-foreground truncate" title="G7_Douyin_PainPoint_v1.mp4">G7_Douyin_PainPoint_v1.mp4</p>
                <p className="text-[11px] font-mono text-foreground/40">generated_video_urls [0]</p>
              </div>
            </div>

            <div className="border border-foreground/10 bg-background p-3 space-y-3 relative group">
              <div className="absolute top-0 right-0 px-2 py-0.5 bg-foreground text-black text-[10px] font-mono font-bold">15-30s | 9:16</div>
              <div className="aspect-[9/16] bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center relative overflow-hidden group-hover:bg-foreground/[0.05] transition-colors cursor-pointer">
                <div className="absolute inset-0 dot-grid opacity-50" />
                <Play className="h-8 w-8 text-[#35ea52] relative z-10 opacity-70 group-hover:opacity-100 transition-opacity" />
              </div>
              <div>
                <p className="text-sm font-mono font-bold text-foreground truncate" title="G7_Douyin_PainPoint_v2.mp4">G7_Douyin_PainPoint_v2.mp4</p>
                <p className="text-[11px] font-mono text-foreground/40">generated_video_urls [1]</p>
              </div>
            </div>

            <div className="border border-foreground/10 bg-background p-3 space-y-3 relative group opacity-60">
              <div className="absolute top-0 right-0 px-2 py-0.5 bg-foreground/20 text-foreground text-[10px] font-mono font-bold">1:1 CUT</div>
              <div className="aspect-square bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 dot-grid opacity-20" />
                <Play className="h-6 w-6 text-foreground/30 relative z-10" />
              </div>
              <div>
                <p className="text-sm font-mono font-bold text-foreground">Bản cắt khung vuông</p>
                <p className="text-[11px] font-mono text-foreground/40">additional_cuts [0]</p>
              </div>
            </div>

          </div>
        </div>

        {/* 4. Product Collection Image Set */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <Package className="h-4 w-4" />
            4. Product Collection Image Set
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            
            <div className="border border-foreground/10 bg-background p-3 space-y-2">
              <div className="aspect-square bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center cursor-pointer hover:bg-foreground/[0.05]">
                <ImageIcon className="h-6 w-6 text-foreground/40" />
              </div>
              <div>
                <span className="text-[9px] text-[#35ea52] uppercase font-bold tracking-widest block mb-0.5">Hero Image</span>
                <p className="text-[11px] font-mono text-foreground truncate">hero_front_50.jpg</p>
              </div>
            </div>

            <div className="border border-foreground/10 bg-background p-3 space-y-2">
              <div className="aspect-square bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center cursor-pointer hover:bg-foreground/[0.05]">
                <ImageIcon className="h-6 w-6 text-foreground/40" />
              </div>
              <div>
                <span className="text-[9px] text-[#35ea52] uppercase font-bold tracking-widest block mb-0.5">SKU Detail</span>
                <p className="text-[11px] font-mono text-foreground truncate">detail_nutrition.jpg</p>
              </div>
            </div>

            <div className="border border-foreground/10 bg-background p-3 space-y-2">
              <div className="aspect-square bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center cursor-pointer hover:bg-foreground/[0.05]">
                <ImageIcon className="h-6 w-6 text-foreground/40" />
              </div>
              <div>
                <span className="text-[9px] text-[#35ea52] uppercase font-bold tracking-widest block mb-0.5">Collection</span>
                <p className="text-[11px] font-mono text-foreground truncate">collection_99_sale.jpg</p>
              </div>
            </div>

            <div className="border border-foreground/10 bg-background p-3 space-y-2">
              <div className="aspect-square bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center cursor-pointer hover:bg-foreground/[0.05]">
                <ImageIcon className="h-6 w-6 text-foreground/40" />
              </div>
              <div>
                <span className="text-[9px] text-[#35ea52] uppercase font-bold tracking-widest block mb-0.5">Thumbnail</span>
                <p className="text-[11px] font-mono text-foreground truncate">tmall_thumb_1.jpg</p>
              </div>
            </div>

            <div className="border border-[#35ea52]/30 bg-[#35ea52]/[0.02] p-3 space-y-2 col-span-2 md:col-span-1">
              <div className="aspect-[3/1] md:aspect-square bg-foreground/[0.02] border border-foreground/5 flex items-center justify-center cursor-pointer hover:bg-foreground/[0.05]">
                <ImageIcon className="h-6 w-6 text-[#35ea52]/60" />
              </div>
              <div>
                <span className="text-[9px] text-[#35ea52] uppercase font-bold tracking-widest block mb-0.5">Promo Banner (Opt)</span>
                <p className="text-[11px] font-mono text-foreground truncate">banner_buy3get1.jpg</p>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};
