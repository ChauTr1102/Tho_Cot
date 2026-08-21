"use client";

import * as React from "react";
import Image from "next/image";
import { Check, ChevronDown, Monitor, Smartphone } from "lucide-react";
import { ShopeePdpPreview } from "./shopee-pdp-preview";
import { TiktokPdpPreview } from "./tiktok-pdp-preview";

interface ProductPdpPreviewProps {
  productName: string;
  images: string[];
  price?: { amount: number; currency: string; unit: string } | null;
  promotion?: string | null;
  description: string;
  bullets: string[];
  angle: string;
}

export function ProductPdpPreview(props: ProductPdpPreviewProps) {
  const [platform, setPlatform] = React.useState<"tiktok" | "shopee">("tiktok");
  const [viewport, setViewport] = React.useState<"mobile" | "desktop">("desktop");
  const [isPlatformMenuOpen, setIsPlatformMenuOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const platforms = [
    { id: "tiktok" as const, label: "TikTok Shop", logo: "/platform-logos/tiktok-shop.svg", accent: "#FE2C55" },
    { id: "shopee" as const, label: "Shopee Việt Nam", logo: "/platform-logos/shopee.svg", accent: "#ee4d2d" },
  ];
  const selectedPlatform = platforms.find((item) => item.id === platform)!;

  React.useEffect(() => {
    if (!isPlatformMenuOpen) return;
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setIsPlatformMenuOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsPlatformMenuOpen(false);
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isPlatformMenuOpen]);

  return (
    <div className="space-y-3">
      <div className="flex flex-col justify-between gap-3 rounded-sm border border-neutral-200 bg-neutral-50 p-2.5 sm:flex-row sm:items-center">
        <div><p className="text-[9px] font-semibold uppercase tracking-wider text-neutral-400">Nền tảng xem trước</p><p className="mt-0.5 text-xs font-medium text-neutral-700">Trang chi tiết sản phẩm</p></div>
        <div className="flex items-center gap-2 self-stretch sm:self-auto">
          <div className="flex h-10 flex-1 border border-neutral-300 bg-white p-1 sm:flex-none" role="group" aria-label="Chọn kiểu thiết bị">
            {(["mobile", "desktop"] as const).map((mode) => {
              const active = viewport === mode;
              const Icon = mode === "mobile" ? Smartphone : Monitor;
              return <button key={mode} type="button" onClick={() => setViewport(mode)} aria-pressed={active} aria-label={mode === "mobile" ? "Xem bản di động" : "Xem bản máy tính"} className={`flex flex-1 items-center justify-center gap-1.5 px-2.5 text-[10px] font-semibold transition-colors sm:flex-none ${active ? "bg-neutral-900 text-white" : "text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900"}`}><Icon className="h-3.5 w-3.5" /><span className="hidden md:inline">{mode === "mobile" ? "Di động" : "Máy tính"}</span></button>;
            })}
          </div>
        <div ref={menuRef} className="relative min-w-0 flex-1 shrink-0 sm:flex-none">
          <button
            type="button"
            aria-label="Chọn nền tảng"
            aria-haspopup="listbox"
            aria-expanded={isPlatformMenuOpen}
            onClick={() => setIsPlatformMenuOpen((open) => !open)}
            className="group flex h-10 w-full min-w-40 items-center gap-2 border border-neutral-300 bg-white px-3 text-left text-xs font-semibold text-neutral-800 shadow-sm outline-none transition-colors hover:border-neutral-400 focus-visible:ring-2 focus-visible:ring-neutral-900/15 sm:min-w-44"
          >
            <span className="flex h-6 w-6 items-center justify-center bg-neutral-50">
              <Image src={selectedPlatform.logo} alt="" width={18} height={18} className="h-[18px] w-[18px] object-contain" />
            </span>
            <span className="flex-1">{selectedPlatform.label}</span>
            <ChevronDown className={`h-3.5 w-3.5 text-neutral-400 transition-transform ${isPlatformMenuOpen ? "rotate-180" : ""}`} />
          </button>

          {isPlatformMenuOpen ? (
            <div role="listbox" aria-label="Nền tảng xem trước" className="absolute right-0 top-[calc(100%+6px)] z-50 min-w-full overflow-hidden border border-neutral-200 bg-white p-1 shadow-[0_12px_32px_rgba(0,0,0,0.16)]">
              {platforms.map((item) => {
                const selected = item.id === platform;
                return (
                  <button
                    key={item.id}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    onClick={() => { setPlatform(item.id); setIsPlatformMenuOpen(false); }}
                    className={`flex w-full items-center gap-2.5 px-2.5 py-2 text-left text-xs transition-colors ${selected ? "bg-neutral-100 font-semibold text-neutral-900" : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900"}`}
                  >
                    <span className="flex h-7 w-7 items-center justify-center border border-neutral-200 bg-white">
                      <Image src={item.logo} alt="" width={19} height={19} className="h-[19px] w-[19px] object-contain" />
                    </span>
                    <span className="flex-1 whitespace-nowrap">{item.label}</span>
                    {selected ? <Check className="h-3.5 w-3.5" style={{ color: item.accent }} /> : <span className="h-3.5 w-3.5" />}
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>
        </div>
      </div>
      <div className={viewport === "mobile" ? "mx-auto w-full max-w-[420px]" : "w-full"}>
        {platform === "shopee" ? <ShopeePdpPreview {...props} viewMode={viewport} /> : <TiktokPdpPreview {...props} viewMode={viewport} />}
      </div>
    </div>
  );
}
