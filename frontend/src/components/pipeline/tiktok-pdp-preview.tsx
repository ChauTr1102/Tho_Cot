"use client";

import * as React from "react";
import Image from "next/image";
import { ChevronRight, ImageOff, Minus, Plus, ShieldCheck, Star, Truck } from "lucide-react";

interface TiktokPdpPreviewProps {
  productName: string;
  images: string[];
  price?: { amount: number; currency: string; unit: string } | null;
  promotion?: string | null;
  description: string;
  bullets: string[];
  angle: string;
  rating?: number;
  soldCount?: number;
}

// Fixed, visually-plausible placeholder stats — not derived from real analytics.
const DEFAULT_RATING = 4.6;
const DEFAULT_SOLD_COUNT = 2100;
const DEFAULT_REVIEW_COUNT = 328;
const FAKE_ORIGINAL_MULTIPLIER = 1.35; // used only to render a strikethrough "original price" for mock purposes
const RATING_BREAKDOWN = [
  { stars: 5, pct: 78 },
  { stars: 4, pct: 15 },
  { stars: 3, pct: 5 },
  { stars: 2, pct: 1 },
  { stars: 1, pct: 1 },
];

function formatCurrency(amount: number, currency: string) {
  try {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: currency || "VND",
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${amount.toLocaleString("vi-VN")} ${currency}`;
  }
}

export function TiktokPdpPreview({
  productName,
  images,
  price,
  promotion,
  description,
  bullets,
  angle,
  rating = DEFAULT_RATING,
  soldCount = DEFAULT_SOLD_COUNT,
}: TiktokPdpPreviewProps) {
  const [selectedImage, setSelectedImage] = React.useState(0);
  const [quantity, setQuantity] = React.useState(1);
  const hasImages = images.length > 0;
  const activeImage = hasImages ? images[Math.min(selectedImage, images.length - 1)] : null;

  const discountPct = price ? Math.round((1 - 1 / FAKE_ORIGINAL_MULTIPLIER) * 100) : 0;
  const originalAmount = price ? Math.round(price.amount * FAKE_ORIGINAL_MULTIPLIER) : 0;

  const variantChips = bullets.slice(0, 4);

  return (
    <div className="font-mono text-foreground">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-[10px] text-foreground/40 mb-4 flex-wrap">
        <span>Trang chủ</span>
        <ChevronRight className="h-3 w-3" />
        <span>Sản phẩm</span>
        <ChevronRight className="h-3 w-3" />
        <span>TikTok Shop</span>
        <ChevronRight className="h-3 w-3" />
        <span className="text-foreground/70 truncate max-w-[200px]">{productName}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-6">
        {/* Left: Gallery */}
        <div>
          <div className="aspect-square relative border border-foreground/10 bg-foreground/[0.03] overflow-hidden flex items-center justify-center">
            {activeImage ? (
              <Image
                src={activeImage}
                alt={productName}
                fill
                unoptimized
                className="object-cover"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 text-foreground/30">
                <ImageOff className="h-8 w-8" />
                <span className="text-[10px]">Chưa có hình ảnh</span>
              </div>
            )}
            {promotion ? (
              <span className="absolute top-2 left-2 px-2 py-1 bg-[#35ea52] text-black text-[10px] font-bold">
                {promotion}
              </span>
            ) : null}
          </div>
          {hasImages && images.length > 1 ? (
            <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
              {images.map((image, index) => (
                <button
                  key={`${image}-${index}`}
                  type="button"
                  onClick={() => setSelectedImage(index)}
                  className={`relative h-16 w-16 shrink-0 border overflow-hidden ${
                    index === selectedImage ? "border-[#35ea52]" : "border-foreground/10"
                  }`}
                  aria-label={`Xem ảnh ${index + 1}`}
                >
                  <Image src={image} alt={`${productName} ${index + 1}`} fill unoptimized className="object-cover" />
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {/* Right: Info column */}
        <div className="space-y-4 min-w-0">
          <h1 className="text-lg font-display font-bold leading-snug text-foreground">{productName}</h1>

          <div className="flex items-center gap-3 text-[11px] text-foreground/50 flex-wrap">
            <span className="inline-flex items-center gap-1 text-[#35ea52]">
              <Star className="h-3.5 w-3.5 fill-current" /> {rating.toFixed(1)}
            </span>
            <span>({DEFAULT_REVIEW_COUNT} đánh giá)</span>
            <span className="text-foreground/20">|</span>
            <span>Đã bán {soldCount.toLocaleString("vi-VN")}+</span>
          </div>

          {price ? (
            <div className="border border-foreground/10 bg-[#35ea52]/[0.04] p-3 space-y-1.5">
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="text-xl font-bold text-[#35ea52]">{formatCurrency(price.amount, price.currency)}</span>
                <span className="text-xs text-foreground/35 line-through">{formatCurrency(originalAmount, price.currency)}</span>
                <span className="px-1.5 py-0.5 bg-red-500/10 text-red-400 text-[10px] font-bold">-{discountPct}%</span>
              </div>
              <p className="text-[10px] text-foreground/40">Đơn vị: {price.unit}</p>
              {promotion ? <p className="text-[10px] text-[#35ea52]">{promotion}</p> : null}
            </div>
          ) : promotion ? (
            <div className="border border-foreground/10 bg-[#35ea52]/[0.04] p-3">
              <p className="text-xs font-bold text-[#35ea52]">{promotion}</p>
            </div>
          ) : null}

          <div className="flex items-center gap-1.5 text-[10px] text-foreground/45">
            <Truck className="h-3.5 w-3.5 text-[#35ea52]" /> Miễn phí vận chuyển cho đơn từ khu vực nội thành
          </div>

          {variantChips.length ? (
            <div>
              <p className="text-[9px] text-foreground/30 mb-1.5">PHIÊN BẢN / LỢI ÍCH</p>
              <div className="flex flex-wrap gap-2">
                {variantChips.map((chip, index) => (
                  <span
                    key={chip}
                    className={`px-2.5 py-1 border text-[10px] ${
                      index === 0 ? "border-[#35ea52] text-[#35ea52] bg-[#35ea52]/10" : "border-foreground/15 text-foreground/55"
                    }`}
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          <div>
            <p className="text-[9px] text-foreground/30 mb-1.5">SỐ LƯỢNG</p>
            <div className="inline-flex items-center border border-foreground/15">
              <button
                type="button"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="h-7 w-7 flex items-center justify-center hover:bg-foreground/[0.05]"
                aria-label="Giảm số lượng"
              >
                <Minus className="h-3 w-3" />
              </button>
              <span className="h-7 w-9 flex items-center justify-center text-xs border-x border-foreground/15">{quantity}</span>
              <button
                type="button"
                onClick={() => setQuantity((q) => q + 1)}
                className="h-7 w-7 flex items-center justify-center hover:bg-foreground/[0.05]"
                aria-label="Tăng số lượng"
              >
                <Plus className="h-3 w-3" />
              </button>
            </div>
          </div>

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              className="flex-1 h-10 border border-[#35ea52]/40 text-[#35ea52] text-xs font-bold hover:bg-[#35ea52]/10"
            >
              THÊM VÀO GIỎ
            </button>
            <button
              type="button"
              className="flex-1 h-10 bg-[#35ea52] text-black text-xs font-bold hover:bg-[#35ea52]/90"
            >
              MUA NGAY
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-[9px] text-foreground/30 pt-1">
            <ShieldCheck className="h-3.5 w-3.5" /> Bảo đảm hoàn tiền TikTok Shop
          </div>
        </div>
      </div>

      {/* Product description */}
      <div className="mt-8 border-t border-foreground/10 pt-5">
        <p className="text-[10px] text-[#35ea52] mb-3">VỀ SẢN PHẨM NÀY</p>
        <div className="grid grid-cols-1 sm:grid-cols-[160px_minmax(0,1fr)] gap-4">
          <div className="aspect-square relative border border-foreground/10 bg-foreground/[0.03] overflow-hidden flex items-center justify-center">
            {activeImage ? (
              <Image src={activeImage} alt={`${productName} mô tả`} fill unoptimized className="object-cover" />
            ) : (
              <ImageOff className="h-6 w-6 text-foreground/20" />
            )}
          </div>
          <div className="space-y-3 min-w-0">
            <p className="text-xs text-foreground/60 leading-relaxed">{description}</p>
            <p className="text-[10px] text-foreground/35 italic">Góc chiến dịch: {angle}</p>
            <ul className="space-y-1.5">
              {bullets.map((bullet) => (
                <li key={bullet} className="flex gap-2 text-xs text-foreground/60">
                  <span className="text-[#35ea52] shrink-0">✓</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Reviews summary */}
      <div className="mt-8 border-t border-foreground/10 pt-5">
        <p className="text-[10px] text-[#35ea52] mb-3">ĐÁNH GIÁ SẢN PHẨM</p>
        <div className="flex flex-col sm:flex-row gap-5">
          <div className="flex flex-col items-center justify-center shrink-0 sm:w-28">
            <span className="text-2xl font-bold text-foreground">{rating.toFixed(1)}</span>
            <div className="flex gap-0.5 mt-1">
              {Array.from({ length: 5 }).map((_, index) => (
                <Star
                  key={index}
                  className={`h-3 w-3 ${index < Math.round(rating) ? "fill-[#35ea52] text-[#35ea52]" : "text-foreground/15"}`}
                />
              ))}
            </div>
            <span className="text-[9px] text-foreground/35 mt-1">{DEFAULT_REVIEW_COUNT} đánh giá</span>
          </div>
          <div className="flex-1 space-y-1.5 min-w-0">
            {RATING_BREAKDOWN.map((row) => (
              <div key={row.stars} className="flex items-center gap-2 text-[10px] text-foreground/40">
                <span className="w-8 shrink-0">{row.stars} sao</span>
                <div className="flex-1 h-1.5 bg-foreground/[0.06] overflow-hidden">
                  <div className="h-full bg-[#35ea52]" style={{ width: `${row.pct}%` }} />
                </div>
                <span className="w-8 text-right shrink-0">{row.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
