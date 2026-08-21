"use client";

import * as React from "react";
import Image from "next/image";
import { Check, ChevronDown, Film, Monitor, ShoppingBag, Smartphone } from "lucide-react";
import { PlatformVideoPlayer } from "./platform-video-player";
import { IphonePreviewFrame } from "./iphone-preview-frame";
import { ShopeePdpPreview } from "./shopee-pdp-preview";
import { TiktokPdpPreview } from "./tiktok-pdp-preview";

interface ProductPdpPreviewProps {
  productName: string;
  category?: string;
  images: string[];
  tiktokImages?: string[];
  shopeeImages?: string[];
  videos?: string[];
  price?: { amount: number; currency: string; unit: string } | null;
  promotion?: string | null;
  description: string;
  bullets: string[];
  angle: string;
}

export function ProductPdpPreview(props: ProductPdpPreviewProps) {
  const [platform, setPlatform] = React.useState<"tiktok" | "shopee">("tiktok");
  const [viewport, setViewport] = React.useState<"mobile" | "desktop">("desktop");
  const [previewType, setPreviewType] = React.useState<"listing" | "video">("listing");
  const [isPlatformMenuOpen, setIsPlatformMenuOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const platforms = [
    { id: "tiktok" as const, label: "TikTok Shop", logo: "/platform-logos/tiktok-shop.svg", accent: "#FE2C55" },
    { id: "shopee" as const, label: "Shopee", logo: "/platform-logos/shopee.svg", accent: "#ee4d2d" },
  ];
  const selectedPlatform = platforms.find((item) => item.id === platform)!;
  const platformImages = platform === "shopee" ? props.shopeeImages : props.tiktokImages;

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
      <div className="rounded-sm border border-neutral-200 bg-neutral-50 p-2">
        <div className="flex w-full flex-wrap items-center justify-end gap-2 sm:flex-nowrap">
          <div className="flex h-9 min-w-0 flex-1 border border-neutral-300 bg-white p-1 sm:flex-none" role="group" aria-label="Chọn nội dung xem trước">
            {(["listing", "video"] as const).map((type) => {
              const active = previewType === type;
              const Icon = type === "listing" ? ShoppingBag : Film;
              const disabled = type === "video" && !props.videos?.[0];
              return <button key={type} type="button" disabled={disabled} onClick={() => setPreviewType(type)} aria-pressed={active} className={`flex min-w-max flex-1 items-center justify-center gap-1.5 whitespace-nowrap px-2 text-[10px] font-semibold transition-colors ${active ? "bg-neutral-900 text-white" : "text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900"} disabled:cursor-not-allowed disabled:opacity-35`}><Icon className="h-3.5 w-3.5 shrink-0" />{type === "listing" ? "Sản phẩm" : "Video"}</button>;
            })}
          </div>
          <div className="flex h-9 min-w-0 flex-1 border border-neutral-300 bg-white p-1 sm:flex-none" role="group" aria-label="Chọn kiểu thiết bị">
            {(["mobile", "desktop"] as const).map((mode) => {
              const active = viewport === mode;
              const Icon = mode === "mobile" ? Smartphone : Monitor;
              return <button key={mode} type="button" onClick={() => setViewport(mode)} aria-pressed={active} aria-label={mode === "mobile" ? "Xem bản di động" : "Xem bản máy tính"} className={`flex min-w-max flex-1 items-center justify-center gap-1.5 whitespace-nowrap px-2 text-[10px] font-semibold transition-colors ${active ? "bg-neutral-900 text-white" : "text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900"}`}><Icon className="h-3.5 w-3.5 shrink-0" /><span>{mode === "mobile" ? "Di động" : "Máy tính"}</span></button>;
            })}
          </div>
        <div ref={menuRef} className="relative min-w-0 flex-[1_1_176px] sm:w-44 sm:flex-none">
          <button
            type="button"
            aria-label="Chọn nền tảng"
            aria-haspopup="listbox"
            aria-expanded={isPlatformMenuOpen}
            onClick={() => setIsPlatformMenuOpen((open) => !open)}
            className="group flex h-9 w-full min-w-0 items-center gap-2 border border-neutral-300 bg-white px-2.5 text-left text-[11px] font-semibold text-neutral-800 shadow-sm outline-none transition-colors hover:border-neutral-400 focus-visible:ring-2 focus-visible:ring-neutral-900/15"
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
      {previewType === "video" && props.videos?.[0] ? viewport === "mobile" ? <div className="mx-auto w-full max-w-[420px]"><IphonePreviewFrame><div className="h-full w-full bg-black"><PlatformVideoPlayer src={props.videos[0]} poster={platformImages?.[0] ?? props.images[0]} title={props.productName} platform={platform} fit="cover" /></div></IphonePreviewFrame></div> : <div className="mx-auto w-full max-w-[360px] overflow-hidden rounded-xl bg-black shadow-xl"><div className="aspect-[9/16]"><PlatformVideoPlayer src={props.videos[0]} poster={platformImages?.[0] ?? props.images[0]} title={props.productName} platform={platform} /></div></div> : <div className={viewport === "mobile" ? "mx-auto w-full max-w-[420px]" : "w-full"}>
        {platform === "shopee" ? <ShopeePdpPreview {...props} images={platformImages?.length ? platformImages : props.images} viewMode={viewport} /> : <TiktokPdpPreview {...props} images={platformImages?.length ? platformImages : props.images} viewMode={viewport} />}
      </div>}
    </div>
  );
}
