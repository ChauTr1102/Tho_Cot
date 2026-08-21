"use client";

import * as React from "react";
import { AgentLoading } from "./agent-loading";
import { Package, Download, FileVideo, FileImage, FileText, CheckCircle2, Loader2 } from "lucide-react";

export const StagePackage: React.FC = () => {
  const [isProcessing, setIsProcessing] = React.useState(true);
  const [isDownloading, setIsDownloading] = React.useState(false);
  const [isDownloaded, setIsDownloaded] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setIsProcessing(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleDownload = () => {
    setIsDownloading(true);
    setTimeout(() => {
      setIsDownloading(false);
      setIsDownloaded(true);
    }, 2500);
  };

  const steps = [
    "Assembling final assets...",
    "Generating export package...",
    "Preparing delivery..."
  ];

  if (isProcessing) {
    return (
      <div className="h-full flex flex-col justify-center max-w-xl mx-auto w-full">
        <AgentLoading agentName="PACKAGE_AGENT" steps={steps} isComplete={false} />
      </div>
    );
  }

  const files = [
    { name: "G7_Douyin_15s_PainPoint.mp4", type: "video", size: "12.4 MB" },
    { name: "G7_Douyin_15s_Aesthetic.mp4", type: "video", size: "14.1 MB" },
    { name: "G7_Tmall_Banner_Hero.jpg", type: "image", size: "2.1 MB" },
    { name: "G7_Tmall_Banner_Detail.jpg", type: "image", size: "1.8 MB" },
    { name: "G7_Tmall_Banner_Promo.jpg", type: "image", size: "2.4 MB" },
    { name: "G7_Commerce_Copy_Douyin.txt", type: "text", size: "12 KB" },
    { name: "G7_Commerce_Copy_Tmall.txt", type: "text", size: "18 KB" },
    { name: "G7_Campaign_Strategy_Doc.pdf", type: "text", size: "1.2 MB" },
  ];

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">ĐÓNG GÓI CHIẾN DỊCH</h2>
        <p className="text-sm font-mono text-foreground/40">
          Tất cả tài sản đã được tự động đặt tên theo chuẩn hệ thống và nén lại thành một file ZIP duy nhất.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-8 pr-2 pb-8">
        
        {/* Package Summary */}
        <div className="flex flex-col md:flex-row gap-6 items-center p-6 border border-foreground/10 bg-background/50">
          <div className="h-24 w-24 border-2 border-dashed border-[#35ea52]/50 bg-[#35ea52]/5 flex items-center justify-center shrink-0">
            <Package className="h-10 w-10 text-[#35ea52]" />
          </div>
          <div className="flex-1 space-y-2 text-center md:text-left">
            <h3 className="text-lg font-mono font-bold text-foreground">G7_Campaign_China99_FullPack.zip</h3>
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs font-mono text-foreground/50">
              <span>Size: 34.0 MB</span>
              <span>•</span>
              <span>8 Files Included</span>
              <span>•</span>
              <span>Auto-standardized Naming</span>
            </div>
          </div>
          <div className="shrink-0 w-full md:w-auto">
            <button 
              onClick={handleDownload}
              disabled={isDownloading || isDownloaded}
              className={`w-full md:w-auto px-8 py-3 flex items-center justify-center gap-2 font-mono font-bold text-xs transition-all ${
                isDownloaded 
                  ? "bg-[#35ea52]/20 text-[#35ea52] border border-[#35ea52]/30 cursor-not-allowed"
                  : "bg-[#35ea52] text-black hover:bg-[#35ea52]/80"
              }`}
            >
              {isDownloading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> ĐANG TẠO ZIP...</>
              ) : isDownloaded ? (
                <><CheckCircle2 className="h-4 w-4" /> ĐÃ TẢI XUỐNG</>
              ) : (
                <><Download className="h-4 w-4" /> TẢI XUỐNG (.ZIP)</>
              )}
            </button>
          </div>
        </div>

        {/* File List */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-bold text-foreground/70 tracking-widest uppercase border-b border-foreground/10 pb-2">
            Nội dung gói tài sản
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {files.map((file, i) => (
              <div key={i} className="flex items-center gap-3 p-3 border border-foreground/10 bg-foreground/[0.02] hover:bg-foreground/[0.05] transition-colors">
                <div className="h-8 w-8 bg-background flex items-center justify-center border border-foreground/10 shrink-0">
                  {file.type === "video" && <FileVideo className="h-4 w-4 text-[#35ea52]" />}
                  {file.type === "image" && <FileImage className="h-4 w-4 text-blue-400" />}
                  {file.type === "text" && <FileText className="h-4 w-4 text-foreground/50" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-mono text-foreground font-bold truncate">{file.name}</p>
                </div>
                <span className="text-[10px] font-mono text-foreground/40 shrink-0">{file.size}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
