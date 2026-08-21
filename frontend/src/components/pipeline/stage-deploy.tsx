"use client";

import * as React from "react";
import { AgentLoading } from "./agent-loading";
import { Rocket, Store, Video, CheckCircle2, Loader2, ExternalLink } from "lucide-react";

export const StageDeploy: React.FC = () => {
  const [isProcessing, setIsProcessing] = React.useState(true);
  const [deployStatus, setDeployStatus] = React.useState<Record<string, "idle" | "deploying" | "success">>({
    tiktok: "idle",
    shopee: "idle",
    all: "idle"
  });

  React.useEffect(() => {
    const timer = setTimeout(() => setIsProcessing(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleDeploy = (platform: "tiktok" | "shopee" | "all") => {
    setDeployStatus(prev => ({ ...prev, [platform]: "deploying" }));
    
    // Nếu deploy ALL, set trạng thái cho các nền tảng con luôn
    if (platform === "all") {
      setDeployStatus(prev => ({ ...prev, tiktok: "deploying", shopee: "deploying" }));
    }

    setTimeout(() => {
      setDeployStatus(prev => ({ ...prev, [platform]: "success" }));
      if (platform === "all") {
        setDeployStatus(prev => ({ ...prev, tiktok: "success", shopee: "success" }));
      }
    }, 3000);
  };

  const steps = [
    "Connecting to deployment platforms...",
    "Publishing assets...",
    "Finalizing campaign rollout..."
  ];

  if (isProcessing) {
    return (
      <div className="h-full flex flex-col justify-center max-w-xl mx-auto w-full">
        <AgentLoading agentName="DEPLOY_AGENT" steps={steps} isComplete={false} />
      </div>
    );
  }

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">TRIỂN KHAI CHIẾN DỊCH</h2>
        <p className="text-sm font-mono text-foreground/40">
          Đẩy trực tiếp các tài sản quảng cáo và thiết lập chiến dịch lên các nền tảng thương mại thông qua API.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-8 pr-2 pb-8">
        
        {/* Global Deploy Action */}
        <div className="border border-[#35ea52]/30 bg-[#35ea52]/[0.02] p-6 flex flex-col items-center justify-center text-center space-y-4">
          <div className="h-16 w-16 bg-[#35ea52]/10 rounded-full flex items-center justify-center">
            <Rocket className="h-8 w-8 text-[#35ea52]" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-mono font-bold text-foreground">ONE-CLICK DEPLOYMENT</h3>
            <p className="text-xs font-mono text-foreground/50 max-w-md mx-auto">
              Kích hoạt toàn bộ chiến dịch trên tất cả các nền tảng cùng lúc. Agent sẽ tự động upload video, cấu hình banner và set nội dung SEO.
            </p>
          </div>
          
          <button 
            onClick={() => handleDeploy("all")}
            disabled={deployStatus.all !== "idle"}
            className={`px-8 py-3 flex items-center gap-2 font-mono font-bold text-xs transition-all ${
              deployStatus.all === "success" 
                ? "bg-[#35ea52]/20 text-[#35ea52] border border-[#35ea52]/30"
                : "bg-[#35ea52] text-black hover:bg-[#35ea52]/80"
            }`}
          >
            {deployStatus.all === "deploying" ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> ĐANG TRIỂN KHAI...</>
            ) : deployStatus.all === "success" ? (
              <><CheckCircle2 className="h-4 w-4" /> ĐÃ TRIỂN KHAI THÀNH CÔNG</>
            ) : (
              <><Rocket className="h-4 w-4" /> TRIỂN KHAI TOÀN BỘ CHIẾN DỊCH</>
            )}
          </button>
        </div>

        {/* Individual Platforms */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-foreground/70 tracking-widest uppercase border-b border-foreground/10 pb-2">
            Triển khai từng nền tảng
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Douyin / TikTok */}
            <div className="border border-foreground/10 bg-background p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 bg-foreground/[0.05] flex items-center justify-center rounded-sm">
                    <Video className="h-5 w-5 text-foreground" />
                  </div>
                  <div>
                    <h4 className="text-sm font-mono font-bold text-foreground">Douyin / TikTok Shop</h4>
                    <p className="text-[10px] font-mono text-foreground/50">2 Videos • 2 Captions</p>
                  </div>
                </div>
                {deployStatus.tiktok === "success" && (
                  <span className="flex items-center gap-1 text-[10px] font-mono text-[#35ea52] font-bold bg-[#35ea52]/10 px-2 py-1">
                    <CheckCircle2 className="h-3 w-3" /> LIVE
                  </span>
                )}
              </div>
              
              <div className="pt-2 border-t border-foreground/5 flex items-center justify-between">
                <button 
                  onClick={() => handleDeploy("tiktok")}
                  disabled={deployStatus.tiktok !== "idle"}
                  className="px-4 py-2 border border-foreground/20 text-xs font-mono text-foreground hover:bg-foreground/5 transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  {deployStatus.tiktok === "deploying" ? (
                    <><Loader2 className="h-3.5 w-3.5 animate-spin" /> ĐANG ĐẨY...</>
                  ) : deployStatus.tiktok === "success" ? (
                    "ĐÃ ĐĂNG LÊN DOUYIN"
                  ) : (
                    "ĐĂNG LÊN DOUYIN"
                  )}
                </button>
                {deployStatus.tiktok === "success" && (
                  <button className="text-[10px] font-mono text-foreground/40 hover:text-[#35ea52] flex items-center gap-1 transition-colors">
                    <ExternalLink className="h-3 w-3" /> Xem Campaign
                  </button>
                )}
              </div>
            </div>

            {/* Tmall / Taobao */}
            <div className="border border-foreground/10 bg-background p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 bg-foreground/[0.05] flex items-center justify-center rounded-sm">
                    <Store className="h-5 w-5 text-orange-500" />
                  </div>
                  <div>
                    <h4 className="text-sm font-mono font-bold text-foreground">Taobao / Tmall</h4>
                    <p className="text-[10px] font-mono text-foreground/50">4 Banners • Product SEO Copy</p>
                  </div>
                </div>
                {deployStatus.shopee === "success" && (
                  <span className="flex items-center gap-1 text-[10px] font-mono text-[#35ea52] font-bold bg-[#35ea52]/10 px-2 py-1">
                    <CheckCircle2 className="h-3 w-3" /> LIVE
                  </span>
                )}
              </div>
              
              <div className="pt-2 border-t border-foreground/5 flex items-center justify-between">
                <button 
                  onClick={() => handleDeploy("shopee")}
                  disabled={deployStatus.shopee !== "idle"}
                  className="px-4 py-2 border border-foreground/20 text-xs font-mono text-foreground hover:bg-foreground/5 transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  {deployStatus.shopee === "deploying" ? (
                    <><Loader2 className="h-3.5 w-3.5 animate-spin" /> ĐANG ĐẨY...</>
                  ) : deployStatus.shopee === "success" ? (
                    "ĐÃ ĐĂNG LÊN TMALL"
                  ) : (
                    "ĐĂNG LÊN TMALL"
                  )}
                </button>
                {deployStatus.shopee === "success" && (
                  <button className="text-[10px] font-mono text-foreground/40 hover:text-[#35ea52] flex items-center gap-1 transition-colors">
                    <ExternalLink className="h-3 w-3" /> Xem Gian Hàng
                  </button>
                )}
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};
