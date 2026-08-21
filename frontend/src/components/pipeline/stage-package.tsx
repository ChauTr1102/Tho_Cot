"use client";

import * as React from "react";
import { CheckCircle2, Download, Loader2 } from "lucide-react";

export const StagePackage: React.FC = () => {
  const [status, setStatus] = React.useState<"idle" | "downloading" | "downloaded">("idle");

  const handleDownload = () => {
    setStatus("downloading");
    setTimeout(() => setStatus("downloaded"), 1500);
  };

  return (
    <div className="flex flex-1 items-center justify-end gap-4">
      <p className="text-sm font-mono font-bold text-foreground">34.0 MB</p>
      <button type="button" onClick={handleDownload} disabled={status !== "idle"} className={`h-10 px-5 inline-flex items-center justify-center gap-2 text-xs font-mono font-bold shrink-0 transition-colors ${status === "downloaded" ? "border border-[#35ea52]/30 bg-[#35ea52]/10 text-[#35ea52]" : "bg-[#35ea52] text-black hover:bg-[#35ea52]/85 disabled:opacity-60"}`}>
        {status === "downloading" ? <><Loader2 className="h-4 w-4 animate-spin" /> ĐANG TẠO ZIP...</> : status === "downloaded" ? <><CheckCircle2 className="h-4 w-4" /> ĐÃ TẢI ZIP</> : <><Download className="h-4 w-4" /> TẢI FILE ZIP</>}
      </button>
    </div>
  );
};
