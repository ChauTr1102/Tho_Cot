"use client";

import * as React from "react";
import Image from "next/image";
import { ArrowLeft, ChevronRight, Heart, ImageOff, Minus, Play, Plus, Search, Share2, ShieldCheck, ShoppingBag, Star, Truck } from "lucide-react";
import { IphonePreviewFrame } from "./iphone-preview-frame";
import { PlatformVideoPlayer } from "./platform-video-player";

interface TiktokPdpPreviewProps {
  productName: string;
  category?: string;
  images: string[];
  videos?: string[];
  price?: { amount: number; currency: string; unit: string } | null;
  promotion?: string | null;
  description: string;
  bullets: string[];
  angle: string;
  rating?: number;
  soldCount?: number;
  viewMode?: "mobile" | "desktop";
}

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
  videos = [],
  price,
  promotion,
  description,
  bullets,
  rating,
  soldCount,
  viewMode = "desktop",
}: TiktokPdpPreviewProps) {
  const [selectedImage, setSelectedImage] = React.useState(0);
  const [showVideo, setShowVideo] = React.useState(videos.length > 0);
  const [quantity, setQuantity] = React.useState(1);
  const hasImages = images.length > 0;
  const activeImage = hasImages ? images[Math.min(selectedImage, images.length - 1)] : null;

  const variantChips = bullets.slice(0, 4);

  if (viewMode === "mobile") {
    return (
      <IphonePreviewFrame bottomBar={<div className="flex h-full items-center gap-2 px-3 pb-1"><button type="button" className="flex h-11 w-12 flex-col items-center justify-center text-[8px]"><ShoppingBag className="h-5 w-5" />Giỏ hàng</button><button type="button" className="h-11 flex-1 border border-[#FE2C55] bg-[#fff4f6] text-[10px] font-bold text-[#FE2C55]">Thêm vào giỏ</button><button type="button" className="h-11 flex-1 bg-[#FE2C55] text-[10px] font-bold text-white">Mua ngay</button></div>}>
        <header className="flex h-12 items-center gap-3 border-b border-neutral-100 bg-white px-3">
          <ArrowLeft className="h-5 w-5" /><div className="flex h-8 flex-1 items-center gap-2 rounded-sm bg-neutral-100 px-3 text-[10px] text-neutral-400"><Search className="h-3.5 w-3.5" /> Tìm kiếm trong TikTok Shop</div><Share2 className="h-5 w-5" /><ShoppingBag className="h-5 w-5" />
        </header>
        <div className="relative aspect-square bg-white">
          {showVideo && videos[0] ? <PlatformVideoPlayer src={videos[0]} poster={activeImage ?? undefined} title={productName} platform="tiktok" /> : activeImage ? <Image src={activeImage} alt={productName} fill unoptimized className="object-cover" /> : <div className="flex h-full items-center justify-center"><ImageOff className="h-8 w-8 text-neutral-300" /></div>}
          {promotion ? <span className="absolute bottom-3 left-3 rounded-sm bg-[#FE2C55] px-2 py-1 text-[9px] font-bold text-white">{promotion}</span> : null}
          {!showVideo ? <span className="absolute bottom-3 right-3 rounded-full bg-black/60 px-2 py-1 text-[9px] text-white">{Math.min(selectedImage + 1, Math.max(images.length, 1))}/{Math.max(images.length, 1)}</span> : null}
        </div>
        {videos.length || images.length > 1 ? <div className="flex gap-2 overflow-x-auto border-b border-neutral-100 bg-white px-3 py-2">{videos[0] ? <button type="button" aria-label="Xem video sản phẩm" onClick={() => setShowVideo(true)} className={`relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-sm border-2 bg-black ${showVideo ? "border-[#FE2C55]" : "border-neutral-200"}`}><Play className="h-4 w-4 fill-white text-white" /></button> : null}{images.slice(0, 6).map((image, index) => <button key={`${image}-${index}`} type="button" aria-label={`Xem ảnh ${index + 1}`} onClick={() => { setSelectedImage(index); setShowVideo(false); }} className={`relative h-11 w-11 shrink-0 overflow-hidden rounded-sm border-2 ${!showVideo && selectedImage === index ? "border-[#FE2C55]" : "border-neutral-200"}`}><Image src={image} alt={`${productName} ${index + 1}`} fill unoptimized className="object-cover" /></button>)}</div> : null}
        <section className="border-b-8 border-[#f5f5f5] bg-white p-4">
          {price ? <div className="flex items-end gap-2"><b className="text-2xl text-[#FE2C55]">{formatCurrency(price.amount, price.currency)}</b></div> : null}
          <h1 className="mt-2 text-sm font-semibold leading-5">{productName}</h1>
          <div className="mt-2 flex items-center justify-between text-[10px] text-neutral-500"><span>{rating !== undefined ? <span className="flex items-center gap-1 text-amber-500"><Star className="h-3 w-3 fill-current" /> {rating.toFixed(1)}{soldCount !== undefined ? <span className="text-neutral-400">· {soldCount.toLocaleString("vi-VN")} đã bán</span> : null}</span> : "Chưa có dữ liệu đánh giá"}</span><Heart className="h-5 w-5 text-neutral-500" /></div>
        </section>
        <section className="border-b-8 border-[#f5f5f5] bg-white p-4 text-[10px]">
          <div className="flex items-center gap-2"><Truck className="h-4 w-4 text-[#FE2C55]" /><span className="font-medium">Chưa có dữ liệu vận chuyển</span><ChevronRight className="ml-auto h-4 w-4 text-neutral-300" /></div>
          <div className="mt-3 flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-[#FE2C55]" /><span>Đổi ý miễn phí · Hoàn tiền đảm bảo</span></div>
        </section>
        <section className="border-b-8 border-[#f5f5f5] bg-white p-4"><div className="flex items-center justify-between"><b className="text-xs">Chọn phân loại</b><ChevronRight className="h-4 w-4 text-neutral-400" /></div><div className="mt-2 flex gap-2 overflow-hidden">{variantChips.slice(0, 2).map((chip, index) => <span key={chip} className={`max-w-[48%] truncate rounded-sm border px-2.5 py-1.5 text-[9px] ${index === 0 ? "border-[#FE2C55] bg-[#fff4f6] text-[#FE2C55]" : "border-neutral-200"}`}>{chip}</span>)}</div></section>
        <section className="bg-white p-4"><h2 className="text-xs font-semibold">Chi tiết sản phẩm</h2><p className="mt-2 text-[10px] leading-5 text-neutral-600">{description}</p></section>
      </IphonePreviewFrame>
    );
  }

  return (
    <div className="font-sans text-neutral-900 bg-white rounded-lg p-1">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-[10px] text-neutral-400 mb-4 flex-wrap">
        <span>Trang chủ</span>
        <ChevronRight className="h-3 w-3" />
        <span>Sản phẩm</span>
        <ChevronRight className="h-3 w-3" />
        <span>TikTok Shop</span>
        <ChevronRight className="h-3 w-3" />
        <span className="text-neutral-600 truncate max-w-[200px]">{productName}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-6">
        {/* Left: Gallery */}
        <div>
          <div className="aspect-square relative rounded-sm border border-neutral-200 bg-neutral-50 overflow-hidden flex items-center justify-center">
            {showVideo && videos[0] ? (
              <PlatformVideoPlayer src={videos[0]} poster={activeImage ?? undefined} title={productName} platform="tiktok" />
            ) : activeImage ? (
              <Image
                src={activeImage}
                alt={productName}
                fill
                unoptimized
                className="object-cover"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 text-neutral-300">
                <ImageOff className="h-8 w-8" />
                <span className="text-[10px]">Chưa có hình ảnh</span>
              </div>
            )}
            {promotion ? (
              <span className="absolute top-2 left-2 px-2 py-1 rounded-sm bg-[#FE2C55] text-white text-[10px] font-bold">
                {promotion}
              </span>
            ) : null}
          </div>
          {videos.length || (hasImages && images.length > 1) ? (
            <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
              {videos[0] ? <button type="button" onClick={() => setShowVideo(true)} className={`relative flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-sm border bg-black ${showVideo ? "border-[#FE2C55]" : "border-neutral-200"}`} aria-label="Xem video sản phẩm"><Play className="h-5 w-5 fill-white text-white" /></button> : null}
              {images.map((image, index) => (
                <button
                  key={`${image}-${index}`}
                  type="button"
                  onClick={() => { setSelectedImage(index); setShowVideo(false); }}
                  className={`relative h-16 w-16 shrink-0 rounded-sm border overflow-hidden ${
                    !showVideo && index === selectedImage ? "border-[#FE2C55]" : "border-neutral-200"
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
          <h1 className="text-lg font-display font-bold leading-snug text-neutral-900">{productName}</h1>

          <div className="flex items-center gap-3 text-[11px] text-neutral-500 flex-wrap">{rating !== undefined ? <span className="inline-flex items-center gap-1 text-amber-500"><Star className="h-3.5 w-3.5 fill-amber-500" /> {rating.toFixed(1)}</span> : <span>Chưa có dữ liệu đánh giá</span>}{soldCount !== undefined ? <><span className="text-neutral-300">|</span><span>Đã bán {soldCount.toLocaleString("vi-VN")}+</span></> : null}</div>

          {price ? (
            <div className="rounded-sm border border-neutral-200 bg-[#FFE2E9]/30 p-3 space-y-1.5">
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="text-xl font-bold text-[#FE2C55]">{formatCurrency(price.amount, price.currency)}</span>
              </div>
              <p className="text-[10px] text-neutral-500">Đơn vị: {price.unit}</p>
              {promotion ? <p className="text-[10px] text-[#FE2C55]">{promotion}</p> : null}
            </div>
          ) : promotion ? (
            <div className="rounded-sm border border-neutral-200 bg-[#FFE2E9]/30 p-3">
              <p className="text-xs font-bold text-[#FE2C55]">{promotion}</p>
            </div>
          ) : null}

          <div className="flex items-center gap-1.5 text-[10px] text-neutral-500">
            <Truck className="h-3.5 w-3.5 text-[#FE2C55]" /> Chưa có dữ liệu vận chuyển
          </div>

          {variantChips.length ? (
            <div>
              <p className="text-[9px] text-neutral-400 mb-1.5">PHIÊN BẢN / LỢI ÍCH</p>
              <div className="flex flex-wrap gap-2">
                {variantChips.map((chip, index) => (
                  <span
                    key={chip}
                    className={`px-2.5 py-1 rounded-sm border text-[10px] ${
                      index === 0 ? "border-[#FE2C55] text-[#FE2C55] bg-[#FFE2E9]/60" : "border-neutral-200 text-neutral-600"
                    }`}
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          <div>
            <p className="text-[9px] text-neutral-400 mb-1.5">SỐ LƯỢNG</p>
            <div className="inline-flex items-center rounded-sm border border-neutral-200">
              <button
                type="button"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="h-7 w-7 flex items-center justify-center hover:bg-neutral-100"
                aria-label="Giảm số lượng"
              >
                <Minus className="h-3 w-3" />
              </button>
              <span className="h-7 w-9 flex items-center justify-center text-xs border-x border-neutral-200">{quantity}</span>
              <button
                type="button"
                onClick={() => setQuantity((q) => q + 1)}
                className="h-7 w-7 flex items-center justify-center hover:bg-neutral-100"
                aria-label="Tăng số lượng"
              >
                <Plus className="h-3 w-3" />
              </button>
            </div>
          </div>

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              className="flex-1 h-10 rounded-sm bg-white border border-neutral-300 text-neutral-900 text-xs font-bold hover:bg-neutral-50"
            >
              THÊM VÀO GIỎ
            </button>
            <button
              type="button"
              className="flex-1 h-10 rounded-sm bg-[#FE2C55] text-white text-xs font-bold hover:bg-[#e0264a]"
            >
              MUA NGAY
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-[9px] text-neutral-400 pt-1">
            <ShieldCheck className="h-3.5 w-3.5" /> Bảo đảm hoàn tiền TikTok Shop
          </div>
        </div>
      </div>

      {/* Product description */}
      <div className="mt-8 border-t border-neutral-200 pt-5">
        <p className="text-[10px] text-[#FE2C55] mb-3">VỀ SẢN PHẨM NÀY</p>
        <div className="grid grid-cols-1 sm:grid-cols-[160px_minmax(0,1fr)] gap-4">
          <div className="aspect-square relative rounded-sm border border-neutral-200 bg-neutral-50 overflow-hidden flex items-center justify-center">
            {activeImage ? (
              <Image src={activeImage} alt={`${productName} mô tả`} fill unoptimized className="object-cover" />
            ) : (
              <ImageOff className="h-6 w-6 text-neutral-300" />
            )}
          </div>
          <div className="space-y-3 min-w-0">
            <p className="text-xs text-neutral-700 leading-relaxed">{description}</p>
            <ul className="space-y-1.5">
              {bullets.map((bullet) => (
                <li key={bullet} className="flex gap-2 text-xs text-neutral-700">
                  <span className="text-[#FE2C55] shrink-0">✓</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {rating !== undefined ? <div className="mt-8 border-t border-neutral-200 pt-5"><p className="text-[10px] text-[#FE2C55] mb-3">ĐÁNH GIÁ SẢN PHẨM</p><span className="inline-flex items-center gap-1 text-sm font-bold text-amber-500"><Star className="h-4 w-4 fill-current" /> {rating.toFixed(1)}</span></div> : null}
    </div>
  );
}
