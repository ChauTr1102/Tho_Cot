import type { Metadata } from "next";
import type { ReactNode } from "react";

/**
 * Metadata holder for the studio route.
 *
 * `page.tsx` is a client component (it owns the EventSource), so it cannot
 * export metadata itself. This layout carries the tab title, which is the only
 * label a judge sees while a ten-minute run is parked on a second monitor.
 */
export const metadata: Metadata = {
  title: "Asset Studio — Thợ Cốt",
  description:
    "Dựng bộ ảnh và video sẵn đăng bán cho TikTok Shop và Shopee từ ảnh sản phẩm thật của thương hiệu.",
};

export default function StudioLayout({ children }: { children: ReactNode }) {
  return children;
}
