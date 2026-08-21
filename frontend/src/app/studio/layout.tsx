import type { Metadata } from "next";
import type { ReactNode } from "react";

// React Flow's own theme first, then the studio's overrides on top of it. The
// order of these two imports is the order they land in the bundle, and
// `studio.css` re-skins React Flow, so it has to come second.
import "@xyflow/react/dist/style.css";
import "./studio.css";

/**
 * Metadata holder for the studio route.
 *
 * `page.tsx` is a client component (it owns the EventSource), so it cannot
 * export metadata itself. This layout carries the tab title, which is the only
 * label a judge sees while a ten-minute run is parked on a second monitor.
 *
 * It also carries the route's stylesheets — see the header of `studio.css` for
 * why the studio's design tokens live beside the route rather than in
 * `app/globals.css`.
 */
export const metadata: Metadata = {
  title: "Asset Studio — Thợ Cốt",
  description:
    "Dựng bộ ảnh và video sẵn đăng bán cho TikTok Shop và Shopee từ ảnh sản phẩm thật của thương hiệu.",
};

export default function StudioLayout({ children }: { children: ReactNode }) {
  return children;
}
