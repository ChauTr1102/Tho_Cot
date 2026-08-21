"use client";

/**
 * The brief: pick a product, pick the marketplaces, run.
 *
 * Two decisions and one action, in that order, with the cost of the action
 * stated immediately above it. A run takes 6–12 minutes, so the panel closes
 * with the time it will take and exactly how many assets come back, before the
 * user commits to the wait.
 *
 * Both pickers are native form controls under the styling (radio for the brand,
 * checkbox for the platforms), so keyboard navigation, focus rings and screen
 * reader semantics come from the platform rather than being re-invented.
 */

import { Check, Clock, Play, ShoppingBag, Store } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  ALL_PLATFORMS,
  DEMO_BRANDS,
  KITS,
  estimateKit,
} from "@/lib/studio-catalog";
import type { Platform } from "@/types/studio";

const PLATFORM_ICONS: Record<Platform, LucideIcon> = {
  tiktok_shop: ShoppingBag,
  shopee: Store,
};

interface BriefPanelProps {
  brandDir: string;
  onBrandChange: (dir: string) => void;
  platforms: Platform[];
  onPlatformsChange: (platforms: Platform[]) => void;
  onRun: () => void;
  /** True from the moment Run is pressed until the run reaches a terminal state. */
  running: boolean;
  /** True only while `POST /studio/run` is in flight. */
  starting: boolean;
  campaignId: string | null;
}

export function BriefPanel({
  brandDir,
  onBrandChange,
  platforms,
  onPlatformsChange,
  onRun,
  running,
  starting,
  campaignId,
}: BriefPanelProps) {
  const estimate = estimateKit(platforms);
  const locked = running || starting;
  const noPlatform = platforms.length === 0;

  // Selection is rebuilt from ALL_PLATFORMS so the array always carries the
  // canonical order, whatever order the user clicked in.
  const togglePlatform = (platform: Platform) => {
    const next = platforms.includes(platform)
      ? platforms.filter((item) => item !== platform)
      : ALL_PLATFORMS.filter(
          (item) => item === platform || platforms.includes(item)
        );
    onPlatformsChange([...next]);
  };

  return (
    // Sticky with a capped height on desktop: the Run button and the platform
    // toggles stay on screen and the brand list absorbs any overflow. The
    // primary action of a control panel must never be below the fold.
    <aside className="studio-panel flex flex-col overflow-hidden lg:sticky lg:top-[4.5rem] lg:max-h-[calc(100vh-5.5rem)]">
      <div className="shrink-0 border-b border-border px-4 py-3">
        <h2 className="font-display text-[15px] font-semibold tracking-tight">
          Brief chiến dịch
        </h2>
        <p className="mt-0.5 text-[12.5px] text-muted-foreground">
          Ảnh gốc lấy từ <span className="font-mono">sample_data/</span>, kho ảnh
          không bị ghi đè.
        </p>
      </div>

      {/* ── Brand ─────────────────────────────────────────────────────────── */}
      <fieldset
        disabled={locked}
        className="min-h-0 flex-1 overflow-y-auto border-b border-border px-4 py-2.5 disabled:opacity-60"
      >
        <legend className="mb-2 text-[12px] font-semibold text-foreground/80">
          Sản phẩm
        </legend>

        <div role="radiogroup" className="space-y-1">
          {DEMO_BRANDS.map((brand) => {
            const selected = brand.dir === brandDir;
            return (
              <label
                key={brand.dir}
                data-selected={selected}
                className={cn(
                  "studio-option flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-1",
                  locked && "cursor-not-allowed"
                )}
              >
                <input
                  type="radio"
                  name="studio-brand"
                  value={brand.dir}
                  checked={selected}
                  onChange={() => onBrandChange(brand.dir)}
                  className="sr-only"
                />
                <span
                  aria-hidden
                  className={cn(
                    "grid size-7 shrink-0 place-items-center rounded-lg font-display text-[11px] font-bold tracking-tight transition-colors",
                    selected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {brand.monogram}
                </span>
                <span className="min-w-0 flex-1 leading-tight">
                  <span className="block truncate text-[13px] font-medium">
                    {brand.name}
                  </span>
                  <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
                    {brand.category}
                  </span>
                </span>
                <span
                  aria-hidden
                  className={cn(
                    "grid size-4 shrink-0 place-items-center rounded-full border",
                    selected
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border"
                  )}
                >
                  {selected ? <Check className="size-2.5" strokeWidth={3.5} /> : null}
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      {/* ── Platforms ─────────────────────────────────────────────────────── */}
      <fieldset
        disabled={locked}
        className="shrink-0 border-b border-border px-4 py-2.5 disabled:opacity-60"
      >
        <legend className="mb-2 text-[12px] font-semibold text-foreground/80">
          Sàn mục tiêu
        </legend>

        <div className="grid gap-1.5">
          {ALL_PLATFORMS.map((platform) => {
            const kit = KITS[platform];
            const Icon = PLATFORM_ICONS[platform];
            const selected = platforms.includes(platform);
            return (
              <label
                key={platform}
                data-selected={selected}
                className={cn(
                  "studio-option flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2",
                  locked && "cursor-not-allowed"
                )}
              >
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => togglePlatform(platform)}
                  className="sr-only"
                />
                <span
                  aria-hidden
                  className={cn(
                    "grid size-8 shrink-0 place-items-center rounded-[9px] transition-colors",
                    selected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  <Icon className="size-4" strokeWidth={2.25} />
                </span>
                <span className="min-w-0 flex-1 leading-tight">
                  <span className="flex items-baseline gap-2">
                    <span className="text-[13px] font-medium">{kit.name}</span>
                    <span className="studio-nums font-mono text-[11px] text-muted-foreground">
                      {kit.images.length} ảnh · {kit.videos.length} video
                    </span>
                  </span>
                  <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
                    {kit.note}
                  </span>
                </span>
                <span
                  aria-hidden
                  className={cn(
                    "grid size-4 shrink-0 place-items-center rounded-[5px] border",
                    selected
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border"
                  )}
                >
                  {selected ? <Check className="size-2.5" strokeWidth={3.5} /> : null}
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      {/* ── Cost of the action, stated before the action ──────────────────── */}
      <div className="shrink-0 px-4 py-3">
        <div className="flex items-baseline justify-between gap-3">
          <span className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <Clock aria-hidden className="size-3.5" />
            Thời gian
          </span>
          <span className="studio-nums font-mono text-[12px] text-foreground/85">
            6–12 phút
          </span>
        </div>
        <div className="mt-1 flex items-baseline justify-between gap-3">
          <span className="text-[12px] text-muted-foreground">Sẽ nhận</span>
          <span className="studio-nums truncate font-mono text-[12px] text-foreground/85">
            {estimate.images} ảnh · {estimate.videos} video
            {estimate.cutdowns > 0 ? ` · ${estimate.cutdowns} bản cắt` : ""}
          </span>
        </div>

        {/* The planned route mix is deliberately not repeated here: the route
            ledger on the run stage owns that number, and two live counts of
            the same thing is one too many. */}

        <Button
          type="button"
          size="lg"
          onClick={onRun}
          disabled={locked || noPlatform}
          // `.btn-cta` paints the coral gradient over the primary fill; the
          // default variant's near-black `text-primary-foreground` is kept on
          // purpose — white on this orange only reaches 2.8:1.
          className="btn-cta mt-3 h-11 w-full gap-2 text-[15px] disabled:shadow-none"
        >
          {locked ? (
            <>
              <span
                aria-hidden
                className="studio-live-dot relative size-1.5 rounded-full bg-current"
              />
              {starting ? "Đang khởi tạo…" : "Đang dựng kit…"}
            </>
          ) : (
            <>
              <Play aria-hidden className="size-4" strokeWidth={2.5} />
              Chạy studio
            </>
          )}
        </Button>

        <p
          className="mt-2 min-h-4 text-center text-[11.5px] text-muted-foreground"
          aria-live="polite"
        >
          {noPlatform ? (
            "Chọn ít nhất một sàn để chạy."
          ) : campaignId ? (
            <span className="font-mono">{campaignId}</span>
          ) : (
            "Ảnh và video được lưu về máy, không giữ link tạm của BytePlus."
          )}
        </p>
      </div>
    </aside>
  );
}
