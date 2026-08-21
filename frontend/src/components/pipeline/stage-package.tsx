"use client";

import * as React from "react";
import { CheckCircle2, Download, FileArchive, Loader2 } from "lucide-react";

export const StagePackage: React.FC = () => {
  const [status, setStatus] = React.useState<"idle" | "downloading" | "downloaded">("idle");

  const handleDownload = () => {
    setStatus("downloading");
    setTimeout(() => setStatus("downloaded"), 1500);
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-4 border border-foreground/10 bg-foreground/[0.02]">
      <div className="h-10 w-10 border border-[#35ea52]/30 bg-[#35ea52]/10 flex items-center justify-center shrink-0">
        <FileArchive className="h-5 w-5 text-[#35ea52]" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-mono font-bold text-foreground truncate">G7_Campaign_China99_FullPack.zip</p>
        <p className="text-[10px] font-mono text-foreground/40 mt-1">Toàn bộ tài sản chiến dịch · 34.0 MB</p>
      </div>
      <button type="button" onClick={handleDownload} disabled={status !== "idle"} className={`h-10 px-5 inline-flex items-center justify-center gap-2 text-xs font-mono font-bold shrink-0 transition-colors ${status === "downloaded" ? "border border-[#35ea52]/30 bg-[#35ea52]/10 text-[#35ea52]" : "bg-[#35ea52] text-black hover:bg-[#35ea52]/85 disabled:opacity-60"}`}>
        {status === "downloading" ? <><Loader2 className="h-4 w-4 animate-spin" /> ĐANG TẠO ZIP...</> : status === "downloaded" ? <><CheckCircle2 className="h-4 w-4" /> ĐÃ TẢI ZIP</> : <><Download className="h-4 w-4" /> TẢI FILE ZIP</>}
      </button>
    </div>
  );
};
