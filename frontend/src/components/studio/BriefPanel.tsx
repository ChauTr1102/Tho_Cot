"use client";

/**
 * The brief: confirm the campaign, pick the marketplaces, say how it should
 * feel, run.
 *
 * There is no product picker. The studio is the stage after research, so the
 * product was chosen and briefed upstream and arrives selected — normally
 * because the user pressed Tiếp tục on the pipeline screen, which deep-links
 * here with the campaign id. What is left is the cost of the action, stated
 * immediately above it: a run takes 6–12 minutes, so the panel closes with the
 * time and the exact asset count before the user commits to the wait.
 *
 * The platform picker is a native checkbox under the styling, so keyboard
 * navigation, focus rings and screen reader semantics come from the platform
 * rather than being re-invented.
 */

import { Check, Clock, Play, ShoppingBag, Store } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ALL_PLATFORMS, KITS, estimateKit } from "@/lib/studio-catalog";
import {
  DIRECTION_PRESETS,
  type ResearchCampaign,
} from "@/lib/studio-draft";
import type { Platform } from "@/types/studio";

const PLATFORM_ICONS: Record<Platform, LucideIcon> = {
  tiktok_shop: ShoppingBag,
  shopee: Store,
};

/** `2026-08-21 12:23:48.328695` as something a person reads at a glance. */
function formatWhen(value: string): string {
  const parsed = new Date(value.replace(" ", "T"));
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

/** Upstream statuses, said in the words the pipeline screen uses. */
const STATUS_TEXT: Record<string, string> = {
  draft: "chưa chạy nghiên cứu",
  researching: "đang nghiên cứu…",
  failed: "nghiên cứu lỗi",
};

interface BriefPanelProps {
  platforms: Platform[];
  onPlatformsChange: (platforms: Platform[]) => void;
  onRun: () => void;
  /** Campaigns research has worked on. Empty until the fetch lands. */
  campaigns: ResearchCampaign[];
  /** Which one this run is for; null only before the fetch lands. */
  selectedCampaign: string | null;
  onCampaignChange: (id: string) => void;
  /**
   * True when the campaign was named by whoever opened this screen — the
   * pipeline walking a specific campaign, or a `?campaign=` deep link. The
   * list then states which campaign is being built rather than offering a
   * choice: someone two stages into one campaign has no reason to switch, and
   * every reason not to do it by accident. Two campaigns can carry the same
   * product name, so a mis-click is silent and expensive.
   */
  campaignPinned: boolean;
  /** Free text: what the user wants this campaign to feel like. */
  direction: string;
  onDirectionChange: (value: string) => void;
  /** True from the moment Run is pressed until the run reaches a terminal state. */
  running: boolean;
  /** True only while `POST /studio/run` is in flight. */
  starting: boolean;
  campaignId: string | null;
}

export function BriefPanel({
  platforms,
  onPlatformsChange,
  onRun,
  campaigns,
  selectedCampaign,
  onCampaignChange,
  campaignPinned,
  direction,
  onDirectionChange,
  running,
  starting,
  campaignId,
}: BriefPanelProps) {
  const estimate = estimateKit(platforms);
  const locked = running || starting;
  const noPlatform = platforms.length === 0;
  const readyCount = campaigns.filter((c) => c.status === "researched").length;
  const noCampaign = selectedCampaign === null;

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
    // `min-w-0` on the rail as well as on the fieldset inside it. In a column
    // flex container the main axis is vertical, so a child's `min-width: auto`
    // never resolves to zero horizontally and any child with a wide min-content
    // — a <fieldset>, which has one by UA rule — pushes past the rail, where
    // `overflow-hidden` cuts it off instead of wrapping it.
    <aside className="studio-panel flex min-w-0 flex-col overflow-hidden lg:sticky lg:top-[4.5rem] lg:max-h-[calc(100vh-5.5rem)]">
      <div className="shrink-0 border-b border-border px-4 py-3">
        <h2 className="font-display text-[15px] font-semibold tracking-tight">
          Brief chiến dịch
        </h2>
        <p className="mt-0.5 text-[12.5px] text-muted-foreground">
          Brief, plan và ảnh gốc lấy từ bước nghiên cứu. Kho ảnh không bị ghi đè.
        </p>
      </div>

      {/* ── Campaign ──────────────────────────────────────────────────────── */}
      {/* The studio is downstream, so there is no product picker: the campaign
          arrives from research, already briefed. Normally exactly one is
          selected — the one the user pressed Next on — and this list is just
          confirmation of what is about to be built. */}
      {/* A section, not a fieldset: these are buttons rather than a radio group,
          and a <legend> is laid out in the fieldset's border gap — the two-column
          header below overflowed it and collided with the platform list. */}
      <section
        className={cn(
          "min-h-0 flex-1 overflow-y-auto border-b border-border px-4 py-2.5",
          locked && "opacity-60"
        )}
      >
        <div className="mb-2 flex items-baseline justify-between gap-2">
          <h3 className="text-[12px] font-semibold text-foreground/80">Chiến dịch</h3>
          {campaignPinned ? (
            <span className="text-muted-foreground/60 text-[11px]">
              từ bước nghiên cứu
            </span>
          ) : readyCount > 0 ? (
            <span className="text-muted-foreground/60 text-[11px]">
              {readyCount} đã nghiên cứu
            </span>
          ) : null}
        </div>

        {campaigns.length > 0 ? (
          <div className="flex flex-col gap-1.5">
            {campaigns.map((campaign) => {
              const ready = campaign.status === "researched";
              const active = selectedCampaign === campaign.id;
              return (
                <button
                  key={campaign.id}
                  type="button"
                  // Not-yet-researched campaigns stay visible but unselectable:
                  // seeing one greyed out explains why it is absent, hiding it
                  // reads as the campaign having been lost.
                  disabled={locked || !ready || campaignPinned}
                  onClick={() => onCampaignChange(campaign.id)}
                  data-selected={active}
                  className={cn(
                    "studio-option grid grid-cols-[auto_minmax(0,1fr)] items-start gap-2.5 rounded-lg px-2.5 py-2 text-left",
                    campaignPinned
                      ? "cursor-default"
                      : ready
                        ? "cursor-pointer"
                        : "cursor-not-allowed opacity-45",
                    locked && !campaignPinned && "cursor-not-allowed"
                  )}
                >
                  <span
                    aria-hidden
                    className={cn(
                      "mt-[3px] grid size-4 shrink-0 place-items-center rounded-full border",
                      active
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border"
                    )}
                  >
                    {active ? <Check className="size-2.5" strokeWidth={3.5} /> : null}
                  </span>
                  <span className="min-w-0 leading-tight">
                    <span className="block truncate text-[13px] font-medium">
                      {campaign.name}
                    </span>
                    <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
                      {ready
                        ? campaignPinned || !campaign.updated_at
                          ? "brief và plan đã sẵn sàng"
                          : // Product names repeat — the same product researched
                            // twice gives two identical rows — so an unpinned
                            // list has to say which is which.
                            `đã nghiên cứu · ${formatWhen(campaign.updated_at)}`
                        : STATUS_TEXT[campaign.status] ?? campaign.status}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="py-2 text-[12.5px] leading-relaxed text-muted-foreground">
            Chưa có chiến dịch nào nghiên cứu xong. Chạy bước{" "}
            <span className="text-foreground/75">Nghiên cứu</span> trước, rồi bấm
            Tiếp tục để quay lại đây.
          </p>
        )}
      </section>

      {/* ── Platforms ─────────────────────────────────────────────────────── */}
      {/* A <section> with a labelled group, not a <fieldset>. Overriding the
          fieldset's intrinsic `min-inline-size: min-content` with `min-w-0` was
          tried twice and the selection tick kept getting clipped at the rail's
          edge; removing the element removes the quirk instead of arguing with
          it. `disabled` moves onto each checkbox, which is where it is read
          anyway. */}
      <section
        className={cn(
          "min-w-0 shrink-0 border-b border-border px-4 py-2.5",
          locked && "opacity-60"
        )}
      >
        <h3
          id="studio-platforms-label"
          className="mb-2 text-[12px] font-semibold text-foreground/80"
        >
          Sàn mục tiêu
        </h3>

        <div role="group" aria-labelledby="studio-platforms-label" className="grid min-w-0 gap-1.5">
          {ALL_PLATFORMS.map((platform) => {
            const kit = KITS[platform];
            const Icon = PLATFORM_ICONS[platform];
            const selected = platforms.includes(platform);
            return (
              <label
                key={platform}
                data-selected={selected}
                className={cn(
                  // `grid-cols-[auto_minmax(0,1fr)_auto]`, not flex. A flex
                  // item's `min-width: auto` has to be defeated on every nested
                  // level to let a row shrink, and three separate attempts at
                  // that still left the selection tick clipped at the rail's
                  // edge. `minmax(0, 1fr)` states outright that the middle
                  // track may shrink to nothing, so the row cannot outgrow the
                  // panel no matter what its contents measure.
                  "studio-option grid cursor-pointer grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2.5 rounded-lg px-2.5 py-2",
                  locked && "cursor-not-allowed"
                )}
              >
                <input
                  type="checkbox"
                  checked={selected}
                  disabled={locked}
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
                <span className="min-w-0 leading-tight">
                  <span className="flex min-w-0 items-baseline gap-2">
                    {/* `truncate` sets overflow and white-space; it does not set
                        `min-width: 0`, and a flex item without that will not
                        shrink below its content. Without this the marketplace
                        name held the row open and pushed the selection tick past
                        the rail, where `overflow-hidden` cut it off. */}
                    <span className="min-w-0 truncate text-[13px] font-medium">
                      {kit.name}
                    </span>
                    {/* The counts are the reason to read this row, so they keep
                        their width and the name gives way instead. */}
                    <span className="studio-nums shrink-0 font-mono text-[11px] text-muted-foreground">
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
      </section>

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

        {/* The steer. Everything above this describes the product; this
            describes the campaign, and it outranks the director's own reading
            of the brief. Presets exist because an empty box invites an empty
            answer, not because the list is exhaustive — the field is free text
            and the register is written for whatever is in it. */}
        <div className="mt-4">
          <div className="mb-1.5 flex items-baseline justify-between gap-2">
            <span className="text-[13px] font-medium">Muốn chiến dịch ra sao?</span>
            <span className="text-muted-foreground/60 text-[11px]">tuỳ chọn</span>
          </div>
          <textarea
            value={direction}
            rows={2}
            disabled={locked}
            onChange={(event) => onDirectionChange(event.target.value)}
            placeholder="dễ thương, pastel · điện ảnh tối giản · sale tưng bừng chữ to…"
            className="border-border/70 bg-background/50 placeholder:text-muted-foreground/45 focus:border-primary/60 focus:ring-primary/20 w-full resize-none rounded-md border px-2.5 py-2 text-[13px] leading-relaxed outline-none focus:ring-2 disabled:opacity-50"
          />
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {DIRECTION_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                disabled={locked}
                onClick={() => onDirectionChange(preset.value)}
                className="border-border/60 text-muted-foreground hover:border-primary/50 hover:text-foreground rounded-full border px-2.5 py-1 text-[11.5px] transition-colors disabled:opacity-50"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        <Button
          type="button"
          size="lg"
          onClick={onRun}
          disabled={locked || noPlatform || noCampaign}
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
              {starting ? "Đang đọc brief…" : "Đang dựng kit…"}
            </>
          ) : (
            <>
              <Play aria-hidden className="size-4" strokeWidth={2.5} />
              Đề xuất chiến dịch
            </>
          )}
        </Button>

        <p
          className="mt-2 min-h-4 text-center text-[11.5px] text-muted-foreground"
          aria-live="polite"
        >
          {noCampaign ? (
            "Chọn một chiến dịch đã nghiên cứu xong."
          ) : noPlatform ? (
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
