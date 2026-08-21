"use client";

import * as React from "react";
import Image from "next/image";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Heart,
  ImageOff,
  MessageCircle,
  Minus,
  MoreHorizontal,
  Plus,
  Search,
  ShieldCheck,
  ShoppingCart,
  Star,
  Truck,
} from "lucide-react";

interface ShopeePdpPreviewProps {
  productName: string;
  images: string[];
  price?: { amount: number; currency: string; unit: string } | null;
  promotion?: string | null;
  description: string;
  bullets: string[];
  angle: string;
  viewMode?: "mobile" | "desktop";
}

const RATING = 4.9;
const REVIEW_COUNT = 328;
const SOLD_COUNT = 2100;
const ORIGINAL_PRICE_MULTIPLIER = 1.45;

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

export function ShopeePdpPreview({
  productName,
  images,
  price,
  promotion,
  description,
  bullets,
  angle,
  viewMode = "desktop",
}: ShopeePdpPreviewProps) {
  const [selectedImage, setSelectedImage] = React.useState(0);
  const [quantity, setQuantity] = React.useState(1);
  const activeImage = images.length ? images[Math.min(selectedImage, images.length - 1)] : null;
  const originalPrice = price ? Math.round(price.amount * ORIGINAL_PRICE_MULTIPLIER) : 0;
  const discount = price ? Math.round((1 - 1 / ORIGINAL_PRICE_MULTIPLIER) * 100) : 0;

  if (viewMode === "mobile") {
    return (
      <div className="relative mx-auto min-h-[740px] overflow-hidden rounded-[26px] border-[6px] border-neutral-900 bg-[#f5f5f5] font-sans text-[#222] shadow-2xl">
        <div className="flex h-7 items-center justify-between bg-white px-4 text-[9px] font-semibold"><span>9:41</span><span>●●● &nbsp; Wi-Fi &nbsp; ▰</span></div>
        <div className="absolute left-1/2 top-2 h-3 w-20 -translate-x-1/2 rounded-full bg-neutral-900" />
        <header className="absolute inset-x-0 top-7 z-10 flex h-12 items-center justify-between px-3 text-white">
          <button type="button" aria-label="Quay lại" className="flex h-8 w-8 items-center justify-center rounded-full bg-black/35"><ArrowLeft className="h-5 w-5" /></button>
          <div className="flex gap-2"><button type="button" aria-label="Giỏ hàng" className="flex h-8 w-8 items-center justify-center rounded-full bg-black/35"><ShoppingCart className="h-5 w-5" /></button><button type="button" aria-label="Thêm" className="flex h-8 w-8 items-center justify-center rounded-full bg-black/35"><MoreHorizontal className="h-5 w-5" /></button></div>
        </header>
        <div className="relative aspect-square bg-white">
          {activeImage ? <Image src={activeImage} alt={productName} fill unoptimized className="object-cover" /> : <div className="flex h-full items-center justify-center"><ImageOff className="h-9 w-9 text-neutral-300" /></div>}
          <span className="absolute bottom-3 right-3 rounded-full bg-black/50 px-2 py-1 text-[9px] text-white">1/{Math.max(images.length, 1)}</span>
        </div>
        <section className="border-b-2 border-[#f3f3f3] bg-white p-4">
          {price ? <><div className="flex items-end gap-2"><span className="text-2xl font-medium text-[#ee4d2d]">{formatCurrency(price.amount, price.currency)}</span><span className="pb-0.5 text-[10px] text-neutral-400 line-through">{formatCurrency(originalPrice, price.currency)}</span><span className="mb-0.5 bg-[#ee4d2d] px-1.5 py-0.5 text-[9px] font-bold text-white">-{discount}%</span></div>{promotion ? <div className="mt-2 inline-block bg-[#fff0ed] px-2 py-1 text-[9px] font-medium text-[#ee4d2d]">{promotion}</div> : null}</> : null}
          <h1 className="mt-2 text-sm leading-5"><span className="mr-1.5 bg-[#ee4d2d] px-1 py-0.5 align-middle text-[8px] font-bold text-white">YÊU THÍCH</span>{productName}</h1>
          <div className="mt-3 flex items-center justify-between text-[10px] text-neutral-500"><span className="flex items-center gap-1 text-[#ee4d2d]">{RATING} <Star className="h-3 w-3 fill-current" /><span className="text-neutral-400">· {SOLD_COUNT.toLocaleString("vi-VN")} đã bán</span></span><span className="flex items-center gap-1"><Heart className="h-4 w-4" /> 186</span></div>
        </section>
        <section className="mt-2 bg-white p-4 text-[10px]">
          <div className="flex items-center gap-2"><span className="font-medium text-[#ee4d2d]">Voucher của Shop</span><span className="bg-[#fff0ed] px-2 py-1 text-[#ee4d2d]">Giảm 20K</span><span className="bg-[#fff0ed] px-2 py-1 text-[#ee4d2d]">Freeship</span><ChevronRight className="ml-auto h-4 w-4 text-neutral-300" /></div>
          <div className="mt-4 flex items-start gap-2"><Truck className="h-4 w-4 text-[#00bfa5]" /><div><b className="font-medium">Miễn phí vận chuyển</b><p className="mt-1 text-neutral-500">Nhận hàng trong 2–4 ngày</p></div><ChevronRight className="ml-auto h-4 w-4 text-neutral-300" /></div>
        </section>
        <section className="mt-2 bg-white p-4"><div className="flex items-center justify-between"><b className="text-xs">Chọn phân loại</b><ChevronRight className="h-4 w-4 text-neutral-400" /></div><div className="mt-2 flex gap-2 overflow-hidden">{bullets.slice(0, 2).map((bullet, index) => <span key={bullet} className={`max-w-[48%] truncate border px-2.5 py-1.5 text-[9px] ${index === 0 ? "border-[#ee4d2d] bg-[#fff8f6] text-[#ee4d2d]" : "border-neutral-200"}`}>{bullet}</span>)}</div></section>
        <section className="mt-2 bg-white p-4 pb-24"><div className="flex items-center justify-between"><b className="text-xs">Mô tả sản phẩm</b><ChevronRight className="h-4 w-4 text-neutral-400" /></div><p className="mt-2 line-clamp-3 text-[10px] leading-5 text-neutral-600">{description}</p><div className="mt-3 flex items-center gap-2 border-t border-neutral-100 pt-3 text-[10px]"><ShieldCheck className="h-4 w-4 text-[#ee4d2d]" /> Đảm bảo Shopee · Trả hàng miễn phí 15 ngày</div></section>
        <div className="absolute inset-x-0 bottom-0 flex h-16 border-t border-neutral-200 bg-white"><button type="button" className="flex w-14 flex-col items-center justify-center border-r border-neutral-100 text-[8px] text-[#00bfa5]"><MessageCircle className="h-5 w-5" />Chat</button><button type="button" className="flex w-14 flex-col items-center justify-center text-[8px] text-[#ee4d2d]"><ShoppingCart className="h-5 w-5" />Giỏ hàng</button><button type="button" className="flex flex-1 items-center justify-center bg-[#ffb432] text-xs font-medium text-white">Thêm Vào Giỏ Hàng</button><button type="button" className="flex flex-1 items-center justify-center bg-[#ee4d2d] text-xs font-medium text-white">Mua Ngay</button></div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-sm bg-[#f5f5f5] font-sans text-[#222] shadow-sm">
      <header className="bg-gradient-to-b from-[#f53d2d] to-[#f63] text-white">
        <div className="flex items-center justify-between px-4 pt-2 text-[9px] text-white/90">
          <span>Kênh Người Bán &nbsp;|&nbsp; Trở thành Người bán Shopee</span>
          <span>Thông Báo &nbsp; Trợ Giúp &nbsp; Đăng Ký &nbsp;|&nbsp; Đăng Nhập</span>
        </div>
        <div className="flex items-center gap-4 px-4 pb-3 pt-2.5">
          <div className="flex shrink-0 items-center gap-1.5 text-xl font-medium tracking-tight">
            <span className="flex h-8 w-8 items-center justify-center rounded-sm border-2 border-white text-lg font-bold">S</span>
            Shopee
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex h-9 bg-white p-0.5 shadow-sm">
              <div className="flex flex-1 items-center px-3 text-[10px] text-neutral-400">Shopee bao ship 0Đ - Đăng ký ngay!</div>
              <button type="button" aria-label="Tìm kiếm" className="flex w-12 items-center justify-center bg-[#fb5533] text-white">
                <Search className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-1 hidden gap-3 truncate text-[8px] text-white/90 sm:flex">
              <span>Săn Sale Mỗi Ngày</span><span>Hàng Chính Hãng</span><span>Freeship 0Đ</span><span>Voucher Giảm Giá</span>
            </div>
          </div>
          <ShoppingCart className="h-6 w-6 shrink-0" />
        </div>
      </header>

      <div className="p-3 sm:p-4">
        <nav className="mb-3 flex items-center gap-1 text-[9px] text-[#0055aa]">
          <span>Shopee</span><ChevronRight className="h-3 w-3" /><span>{"Bách Hóa Online"}</span>
          <ChevronRight className="h-3 w-3" /><span className="truncate text-neutral-500">{productName}</span>
        </nav>

        <section className="grid gap-5 bg-white p-3 sm:grid-cols-[minmax(0,.88fr)_minmax(0,1.12fr)] sm:p-4">
          <div className="min-w-0">
            <div className="relative flex aspect-square items-center justify-center overflow-hidden bg-[#faf8f0]">
              {activeImage ? (
                <Image src={activeImage} alt={productName} fill unoptimized className="object-cover" />
              ) : (
                <div className="flex flex-col items-center gap-2 text-neutral-300"><ImageOff className="h-9 w-9" /><span className="text-[10px]">Chưa có hình ảnh</span></div>
              )}
              {promotion ? <span className="absolute left-2 top-2 bg-[#f63] px-2 py-1 text-[9px] font-bold text-white">{promotion}</span> : null}
            </div>
            {images.length > 1 ? (
              <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
                {images.slice(0, 5).map((image, index) => (
                  <button key={`${image}-${index}`} type="button" onClick={() => setSelectedImage(index)} aria-label={`Xem ảnh ${index + 1}`} className={`relative h-14 w-14 shrink-0 overflow-hidden border-2 ${selectedImage === index ? "border-[#ee4d2d]" : "border-transparent"}`}>
                    <Image src={image} alt={`${productName} ${index + 1}`} fill unoptimized className="object-cover" />
                  </button>
                ))}
              </div>
            ) : null}
            <div className="mt-3 flex items-center justify-center gap-5 text-[10px]">
              <span>Chia sẻ: <b className="text-blue-500">●</b> <b className="text-sky-500">●</b> <b className="text-red-500">●</b></span>
              <span className="inline-flex items-center gap-1 border-l border-neutral-200 pl-5"><Heart className="h-4 w-4 text-[#ee4d2d]" /> Đã thích (186)</span>
            </div>
          </div>

          <div className="min-w-0">
            <h1 className="text-base font-medium leading-snug sm:text-lg"><span className="mr-2 bg-[#ee4d2d] px-1.5 py-0.5 align-middle text-[9px] font-bold text-white">YÊU THÍCH</span>{productName}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-[10px] text-neutral-500">
              <span className="inline-flex items-center gap-1 border-b border-[#ee4d2d] text-[#ee4d2d]">{RATING} <Star className="h-3 w-3 fill-current" /></span>
              <span><b className="font-medium text-neutral-800 underline">{REVIEW_COUNT}</b> Đánh Giá</span>
              <span><b className="font-medium text-neutral-800">{SOLD_COUNT.toLocaleString("vi-VN")}+</b> Đã Bán</span>
            </div>

            <div className="mt-4 bg-[#fafafa] p-4">
              {price ? <div className="flex flex-wrap items-center gap-2"><span className="text-xs text-neutral-400 line-through">{formatCurrency(originalPrice, price.currency)}</span><span className="text-2xl font-medium text-[#ee4d2d]">{formatCurrency(price.amount, price.currency)}</span><span className="bg-[#ee4d2d] px-1.5 py-0.5 text-[9px] font-bold text-white">{discount}% GIẢM</span></div> : <span className="text-xl font-medium text-[#ee4d2d]">Liên hệ</span>}
              {promotion ? <div className="mt-2 flex items-center gap-2 text-[10px]"><span className="text-neutral-500">Deal Sốc</span><span className="bg-[#fff0ed] px-2 py-1 font-medium text-[#ee4d2d]">{promotion}</span></div> : null}
            </div>

            <div className="mt-4 grid grid-cols-[82px_1fr] gap-y-4 text-[10px]">
              <span className="text-neutral-500">Vận Chuyển</span>
              <div><p className="flex items-center gap-2"><Truck className="h-4 w-4 text-[#00bfa5]" /> Miễn phí vận chuyển</p><p className="mt-1 pl-6 text-neutral-500">Vận chuyển tới Việt Nam <ChevronDown className="inline h-3 w-3" /></p></div>
              <span className="text-neutral-500">Đảm Bảo Shopee</span>
              <p className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-[#ee4d2d]" /> Trả hàng miễn phí 15 ngày · Chính hãng 100%</p>
              {bullets.length ? <><span className="text-neutral-500">Phân Loại</span><div className="flex flex-wrap gap-2">{bullets.slice(0, 3).map((bullet, index) => <button type="button" key={bullet} className={`px-2.5 py-1.5 border ${index === 0 ? "border-[#ee4d2d] text-[#ee4d2d]" : "border-neutral-300"}`}>{bullet}</button>)}</div></> : null}
              <span className="self-center text-neutral-500">Số Lượng</span>
              <div className="flex items-center gap-3"><div className="inline-flex border border-neutral-300"><button type="button" onClick={() => setQuantity((value) => Math.max(1, value - 1))} aria-label="Giảm số lượng" className="flex h-7 w-7 items-center justify-center"><Minus className="h-3 w-3" /></button><span className="flex h-7 w-9 items-center justify-center border-x border-neutral-300">{quantity}</span><button type="button" onClick={() => setQuantity((value) => value + 1)} aria-label="Tăng số lượng" className="flex h-7 w-7 items-center justify-center"><Plus className="h-3 w-3" /></button></div><span className="text-neutral-400">có sẵn 126 sản phẩm</span></div>
            </div>

            <div className="mt-5 flex gap-2">
              <button type="button" className="flex h-10 flex-1 items-center justify-center gap-2 border border-[#ee4d2d] bg-[#fff5f3] px-3 text-xs text-[#ee4d2d]"><ShoppingCart className="h-4 w-4" /> Thêm Vào Giỏ Hàng</button>
              <button type="button" className="h-10 flex-1 bg-[#ee4d2d] px-3 text-xs text-white">Mua Ngay</button>
            </div>
          </div>
        </section>

        <section className="mt-4 bg-white p-4">
          <h2 className="bg-[#fafafa] px-3 py-2.5 text-sm font-medium uppercase">Chi tiết sản phẩm</h2>
          <dl className="mt-4 grid grid-cols-[120px_1fr] gap-y-2 text-[10px]"><dt className="text-neutral-400">Danh Mục</dt><dd className="text-[#0055aa]">Shopee &gt; Bách Hóa Online &gt; {productName}</dd><dt className="text-neutral-400">Thương hiệu</dt><dd>Thương hiệu chính hãng</dd><dt className="text-neutral-400">Xuất xứ</dt><dd>Việt Nam</dd><dt className="text-neutral-400">Kho hàng</dt><dd>126</dd></dl>
          <h2 className="mt-6 bg-[#fafafa] px-3 py-2.5 text-sm font-medium uppercase">Mô tả sản phẩm</h2>
          <div className="mt-4 space-y-3 text-[11px] leading-6 text-neutral-700"><p>{description}</p><p className="italic text-neutral-500">Góc chiến dịch: {angle}</p><ul>{bullets.map((bullet) => <li key={bullet}>• {bullet}</li>)}</ul></div>
        </section>

        <section className="mt-4 bg-white p-4">
          <h2 className="text-sm font-medium uppercase">Đánh giá sản phẩm</h2>
          <div className="mt-3 flex flex-col gap-4 border border-[#f9edea] bg-[#fff8f6] p-4 sm:flex-row sm:items-center">
            <div className="shrink-0 text-center text-[#ee4d2d]"><b className="text-2xl">{RATING}</b> trên 5<div className="mt-1 flex text-[#ee4d2d]">★★★★★</div></div>
            <div className="flex flex-wrap gap-2 text-[10px]"><span className="border border-[#ee4d2d] bg-white px-3 py-1.5 text-[#ee4d2d]">Tất Cả</span><span className="border border-neutral-200 bg-white px-3 py-1.5">5 Sao (256)</span><span className="border border-neutral-200 bg-white px-3 py-1.5">Có Hình Ảnh (92)</span><span className="border border-neutral-200 bg-white px-3 py-1.5">Có Bình Luận (184)</span></div>
          </div>
        </section>
      </div>
    </div>
  );
}
