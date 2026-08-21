"use client";

import * as React from "react";
import { CheckCircle2, Loader2, Rocket } from "lucide-react";

type Platform = "tiktok" | "shopee" | "taobao" | "tmall";
type DeployState = "idle" | "deploying" | "success";

const platforms: Array<{ id: Platform; name: string; description: string; logo: string }> = [
  { id: "tiktok", name: "TikTok Shop", description: "Video, caption và thông tin sản phẩm", logo: "/platform-logos/tiktok-shop.svg" },
  { id: "shopee", name: "Shopee", description: "Ảnh gian hàng và nội dung bán hàng", logo: "/platform-logos/shopee.svg" },
  { id: "taobao", name: "Taobao", description: "Trang sản phẩm và nội dung bán hàng", logo: "/platform-logos/taobao.svg" },
  { id: "tmall", name: "Tmall", description: "Tài sản gian hàng và nội dung thương hiệu", logo: "/platform-logos/tmall.svg" },
];

export const StageDeploy: React.FC = () => {
  const [status, setStatus] = React.useState<Record<Platform, DeployState>>({ tiktok: "idle", shopee: "idle", taobao: "idle", tmall: "idle" });

  const deploy = (targets: Platform[]) => {
    setStatus((current) => ({ ...current, ...Object.fromEntries(targets.map((id) => [id, "deploying"])) }));
    setTimeout(() => setStatus((current) => ({ ...current, ...Object.fromEntries(targets.map((id) => [id, "success"])) })), 2000);
  };

  const isBusy = Object.values(status).some((value) => value === "deploying");
  const allLive = Object.values(status).every((value) => value === "success");

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {platforms.map((platform) => (
          <article key={platform.id} className="p-4 border border-foreground/10 bg-background flex items-center gap-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={platform.logo} alt={`${platform.name} logo`} className="h-11 w-11 object-contain shrink-0" />
            <div className="min-w-0 flex-1"><h3 className="text-sm font-mono font-bold text-foreground">{platform.name}</h3><p className="text-[10px] font-mono text-foreground/40 mt-1">{platform.description}</p></div>
            <button type="button" onClick={() => deploy([platform.id])} disabled={status[platform.id] !== "idle" || isBusy} className="h-9 px-3 border border-foreground/20 text-[10px] font-mono font-bold text-foreground hover:border-[#35ea52]/50 disabled:opacity-60 shrink-0">
              {status[platform.id] === "deploying" ? <Loader2 className="h-4 w-4 animate-spin" /> : status[platform.id] === "success" ? <span className="inline-flex items-center gap-1 text-[#35ea52]"><CheckCircle2 className="h-3.5 w-3.5" /> ĐÃ ĐĂNG</span> : "ĐĂNG LÊN"}
            </button>
          </article>
        ))}
      </div>
      <button type="button" onClick={() => deploy(["tiktok", "shopee", "taobao", "tmall"])} disabled={isBusy || allLive} className="h-10 px-5 bg-[#35ea52] text-black text-xs font-mono font-bold inline-flex items-center justify-center gap-2 hover:bg-[#35ea52]/85 disabled:opacity-60">
        {isBusy ? <><Loader2 className="h-4 w-4 animate-spin" /> ĐANG TRIỂN KHAI...</> : allLive ? <><CheckCircle2 className="h-4 w-4" /> ĐÃ ĐĂNG TRÊN TẤT CẢ NỀN TẢNG</> : <><Rocket className="h-4 w-4" /> ĐĂNG LÊN TẤT CẢ NỀN TẢNG</>}
      </button>
    </div>
  );
};
