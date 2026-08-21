/**
 * The REUSE / REMIX / GENERATE badge.
 *
 * This is the studio's commercial argument compressed into one chip. Every
 * asset is produced by one of three routes, and which route was chosen is a
 * judgement about risk, not a technical detail:
 *
 *   REUSE     the brand's own photograph, cropped only. Used where the shopper
 *             inspects the product and an invented pixel is a liability — a
 *             Shopee main image, an SKU detail. Gold, the trust colour.
 *   REMIX     image-to-image from a real photo: new scene, added text, same
 *             product. Lime.
 *   GENERATE  synthesised, anchored to the product photo and the hero image.
 *             Lime, lighter weight — the least evidence behind it.
 *
 * Colour alone never carries the meaning: each route has its own icon and its
 * own word, so the badge survives a colour-blind viewer and a greyscale print
 * of the pitch deck.
 */

import { Camera, Layers, Sparkles, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import type { AssetOrigin } from "@/types/studio";

interface OriginMeta {
  label: string;
  icon: LucideIcon;
  /** Border, fill and text in one string; all three are needed together. */
  className: string;
  /** One-line explanation, used by the legend on the studio header. */
  description: string;
}

export const ORIGIN_META: Record<AssetOrigin, OriginMeta> = {
  reuse: {
    label: "REUSE",
    icon: Camera,
    className: "border-gold/40 bg-gold/12 text-gold",
    description: "Ảnh thật của thương hiệu, chỉ cắt và nắn khung.",
  },
  remix: {
    label: "REMIX",
    icon: Layers,
    className: "border-primary/45 bg-primary/12 text-primary",
    description: "Image-to-image từ ảnh thật — đổi bối cảnh, thêm chữ.",
  },
  generate: {
    label: "GENERATE",
    icon: Sparkles,
    className: "border-primary/28 bg-primary/6 text-primary/85",
    description: "Dựng mới, neo theo ảnh sản phẩm và ảnh hero.",
  },
};

export const ORIGIN_ORDER: readonly AssetOrigin[] = [
  "reuse",
  "remix",
  "generate",
];

interface OriginBadgeProps {
  origin: AssetOrigin;
  /** `xs` for dense node chips, `sm` for the gallery and the legend. */
  size?: "xs" | "sm";
  /** Hide the word and keep the icon — only for spaces that cannot fit it. */
  iconOnly?: boolean;
  className?: string;
}

export function OriginBadge({
  origin,
  size = "sm",
  iconOnly = false,
  className,
}: OriginBadgeProps) {
  const meta = ORIGIN_META[origin];
  if (!meta) return null;
  const Icon = meta.icon;

  return (
    <span
      title={meta.description}
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded-none border font-semibold uppercase",
        "tracking-[0.09em] whitespace-nowrap",
        size === "xs"
          ? "h-[18px] px-1.5 text-[9.5px]"
          : "h-[22px] px-2 text-[10.5px]",
        meta.className,
        className
      )}
    >
      <Icon
        aria-hidden
        className={size === "xs" ? "size-2.5" : "size-3"}
        strokeWidth={2.25}
      />
      {iconOnly ? <span className="sr-only">{meta.label}</span> : meta.label}
    </span>
  );
}

/**
 * The three routes explained side by side.
 *
 * Sits in the page header rather than buried in a gallery tooltip: a judge
 * should meet the idea before they meet the assets it produced.
 */
export function OriginLegend({ className }: { className?: string }) {
  return (
    <dl className={cn("space-y-2", className)}>
      {ORIGIN_ORDER.map((origin) => (
        <div key={origin} className="flex items-start gap-3">
          {/* Fixed width so the three descriptions share one left edge — the
              badge words are different lengths and a ragged column reads as
              an accident. */}
          <dt className="mt-px w-[92px] shrink-0">
            <OriginBadge origin={origin} />
          </dt>
          <dd className="text-[12.5px] leading-snug text-muted-foreground">
            {ORIGIN_META[origin].description}
          </dd>
        </div>
      ))}
    </dl>
  );
}
