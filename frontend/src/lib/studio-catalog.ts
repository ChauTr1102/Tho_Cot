/**
 * The demo catalogue the studio screen is briefed from.
 *
 * Two tables, both mirrors of backend data:
 *
 *  - `DEMO_BRANDS` — the six directories under `sample_data/`. Each is a real
 *    brand with real product photography in `assets/`; that photography is what
 *    makes REUSE and REMIX possible, so the photo count is shown in the picker.
 *  - `KITS` — a mirror of `backend/app/services/studio/platforms.py`. The screen
 *    uses it to describe the deliverable *before* a run starts, which is how a
 *    6–12 minute wait is made legible: the user reads what they are waiting for
 *    rather than watching an indeterminate spinner.
 *
 * When `platforms.py` changes, change this file with it. It is presentation
 * data only — nothing here is sent to the backend except `brand_dir`.
 */

import type { AssetOrigin, ImageKind, Platform } from "@/types/studio";

export interface DemoBrand {
  /** Directory name under `sample_data/` — the only field the backend needs. */
  dir: string;
  name: string;
  /** Short category line, Vietnamese. */
  category: string;
  /** Two-character mark for the picker tile. */
  monogram: string;
  /** Product photos in `assets/`, i.e. how much real material REUSE can draw on. */
  photos: number;
}

export const DEMO_BRANDS: readonly DemoBrand[] = [
  {
    dir: "01_cosrx_snail_essence",
    name: "COSRX Advanced Snail 96",
    category: "Dưỡng da · tinh chất ốc sên 96%",
    monogram: "CX",
    photos: 2,
  },
  {
    dir: "02_oatside_barista",
    name: "Oatside Barista Blend",
    category: "F&B · sữa yến mạch pha chế",
    monogram: "OS",
    photos: 2,
  },
  {
    dir: "03_anker_powerbank",
    name: "Anker Nano Power Bank",
    category: "Điện tử · sạc dự phòng 10.000mAh",
    monogram: "AK",
    photos: 2,
  },
  {
    dir: "04_cocoon_ca_phe_dak_lak",
    name: "Cocoon Cà phê Đắk Lắk",
    category: "Thuần chay · tẩy da chết cơ thể",
    monogram: "CC",
    photos: 2,
  },
  {
    dir: "05_trung_nguyen_g7",
    name: "Trung Nguyên G7 3in1",
    category: "F&B · cà phê hoà tan xuất khẩu",
    monogram: "G7",
    photos: 2,
  },
  {
    dir: "06_marou_chocolate",
    name: "Marou Tiền Giang 70%",
    category: "F&B · socola bean-to-bar",
    monogram: "MR",
    photos: 2,
  },
] as const;

export interface KitImageSlot {
  id: string;
  /** Vietnamese label shown to the seller. */
  label: string;
  kind: ImageKind;
  ratio: string;
  /** The route the worksheet will try first; the real one arrives over SSE. */
  prefer: AssetOrigin;
  /** Marketplace rule this slot must satisfy, if any. */
  rule?: string;
}

export interface KitVideoSlot {
  id: string;
  label: string;
  ratio: string;
  shots: number;
  cutdowns: string[];
  voiceover: boolean;
}

export interface KitSpec {
  platform: Platform;
  name: string;
  /** One line on what this marketplace's kit is for. */
  note: string;
  images: KitImageSlot[];
  videos: KitVideoSlot[];
}

export const KITS: Record<Platform, KitSpec> = {
  tiktok_shop: {
    platform: "tiktok_shop",
    name: "TikTok Shop",
    note: "Hook trong 3 giây đầu, chừa vùng UI của sàn",
    images: [
      {
        id: "tiktok_cover",
        label: "Ảnh bìa video",
        kind: "marketplace_thumbnail",
        ratio: "9:16",
        prefer: "generate",
      },
      {
        id: "tiktok_product",
        label: "Ảnh sản phẩm",
        kind: "product_hero_image",
        ratio: "1:1",
        prefer: "reuse",
      },
    ],
    videos: [
      {
        id: "tiktok_master",
        label: "Video dọc 9:16",
        ratio: "9:16",
        shots: 4,
        cutdowns: ["15s"],
        voiceover: true,
      },
    ],
  },
  shopee: {
    platform: "shopee",
    name: "Shopee",
    note: "Ảnh chính nền trắng, tối thiểu 1000×1000",
    images: [
      {
        id: "shopee_main",
        label: "Ảnh chính",
        kind: "product_hero_image",
        ratio: "1:1",
        prefer: "reuse",
        rule: "Nền trắng tuyệt đối",
      },
      {
        id: "shopee_sku",
        label: "Ảnh chi tiết SKU",
        kind: "sku_detail_image",
        ratio: "1:1",
        prefer: "reuse",
      },
      {
        id: "shopee_collection",
        label: "Ảnh bộ sưu tập",
        kind: "campaign_collection_image",
        ratio: "1:1",
        prefer: "remix",
      },
      {
        id: "shopee_banner",
        label: "Banner khuyến mãi",
        kind: "promotion_banner",
        ratio: "2:1",
        prefer: "remix",
      },
    ],
    videos: [
      {
        id: "shopee_square",
        label: "Video vuông 1:1",
        ratio: "1:1",
        shots: 2,
        cutdowns: [],
        voiceover: false,
      },
    ],
  },
};

export const ALL_PLATFORMS: readonly Platform[] = ["tiktok_shop", "shopee"];

export interface KitEstimate {
  images: number;
  videos: number;
  cutdowns: number;
  /** Planned route mix, before the inventory step revises it. */
  origins: Record<AssetOrigin, number>;
}

/**
 * What the selected platforms will produce.
 *
 * Shown at the point of commitment so the seller knows the size of the job
 * before they spend ten minutes on it.
 */
export function estimateKit(platforms: readonly Platform[]): KitEstimate {
  const estimate: KitEstimate = {
    images: 0,
    videos: 0,
    cutdowns: 0,
    origins: { reuse: 0, remix: 0, generate: 0 },
  };

  for (const platform of platforms) {
    const kit = KITS[platform];
    if (!kit) continue;
    estimate.images += kit.images.length;
    estimate.videos += kit.videos.length;
    for (const slot of kit.images) estimate.origins[slot.prefer] += 1;
    for (const video of kit.videos) estimate.cutdowns += video.cutdowns.length;
  }

  return estimate;
}
