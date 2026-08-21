"use client";

/**
 * What the canvas shows before there is a graph to show.
 *
 * Two states, both real rather than decorative:
 *
 *   Nothing running — the kit manifest. It lists exactly what will be produced
 *   for each selected marketplace, with the route each slot is planned to
 *   take. An empty state that teaches the interface is worth more than a
 *   spinner, and this one doubles as the answer to "what am I waiting for".
 *
 *   Run pressed, no `graph` event yet — a skeleton of the columns that are
 *   about to appear, so the canvas does not pop into existence from nothing.
 *
 * (Previously `GraphCanvasPlaceholder.tsx`, whose node board is now the React
 * Flow canvas in `GraphCanvas.tsx`.)
 */

import { Film, Image as ImageIcon } from "lucide-react";

import { OriginBadge } from "@/components/studio/OriginBadge";
import { KITS } from "@/lib/studio-catalog";
import { cn } from "@/lib/utils";
import type { Platform } from "@/types/studio";

/* ──────────────────────────────────────────────────────────────────────────
 * Waiting for the first event
 * ────────────────────────────────────────────────────────────────────────── */

export function AwaitingGraph() {
  return (
    <div className="studio-panel h-[clamp(440px,64vh,760px)] overflow-hidden p-4">
      <p className="text-[12.5px] text-muted-foreground">
        Đang chờ sơ đồ graph từ backend…
      </p>
      <div className="mt-3.5 flex items-start gap-6">
        {[3, 4, 3, 2].map((count, column) => (
          <div key={column} className="flex w-[190px] shrink-0 flex-col gap-4">
            {Array.from({ length: count }).map((_, row) => (
              <div
                key={row}
                className="h-[104px] rounded-none border border-border bg-muted/30"
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Kit manifest — what the run will hand back
 * ────────────────────────────────────────────────────────────────────────── */

export function KitManifest({ platforms }: { platforms: Platform[] }) {
  if (platforms.length === 0) {
    return (
      <div className="studio-panel grid min-h-[300px] place-items-center px-6 py-10">
        <p className="max-w-sm text-center text-[13px] leading-relaxed text-muted-foreground">
          Chọn ít nhất một sàn ở cột trái để xem trước bộ kit studio sẽ dựng.
        </p>
      </div>
    );
  }

  return (
    <div className="studio-panel overflow-hidden">
      <div className="flex items-baseline justify-between gap-3 border-b border-border px-4 py-3">
        <h3 className="font-display text-[14px] font-semibold tracking-tight">
          Bộ kit sẽ nhận được
        </h3>
        <span className="text-[11.5px] text-muted-foreground">
          Tuyến bên phải là dự kiến — kiểm kho ảnh có thể đổi
        </span>
      </div>

      <div
        className={cn(
          "grid",
          platforms.length > 1 ? "md:grid-cols-2 md:divide-x" : "",
          "divide-y divide-border md:divide-y-0"
        )}
      >
        {platforms.map((platform) => {
          const kit = KITS[platform];
          if (!kit) return null;
          return (
            <div key={platform} className="min-w-0 divide-border px-4 py-3.5">
              <div className="flex items-baseline gap-2">
                <h4 className="font-display text-[13.5px] font-semibold tracking-tight">
                  {kit.name}
                </h4>
                <span className="truncate text-[11.5px] text-muted-foreground">
                  {kit.note}
                </span>
              </div>

              <ul className="mt-2.5 space-y-1.5">
                {kit.images.map((slot) => (
                  <li key={slot.id} className="flex items-center gap-2.5">
                    <ImageIcon
                      aria-hidden
                      className="size-3.5 shrink-0 text-muted-foreground"
                    />
                    <span className="min-w-0 flex-1 truncate text-[12.5px]">
                      {slot.label}
                      {slot.rule ? (
                        <span className="text-muted-foreground">
                          {" "}
                          · {slot.rule}
                        </span>
                      ) : null}
                    </span>
                    <span className="studio-nums w-8 shrink-0 text-right font-mono text-[11px] text-muted-foreground">
                      {slot.ratio}
                    </span>
                    {/* Fixed column so REUSE and GENERATE share a left edge. */}
                    <OriginBadge
                      origin={slot.prefer}
                      size="xs"
                      className="w-[76px]"
                    />
                  </li>
                ))}

                {kit.videos.map((video) => (
                  <li key={video.id} className="flex items-center gap-2.5">
                    <Film
                      aria-hidden
                      className="size-3.5 shrink-0 text-muted-foreground"
                    />
                    <span className="min-w-0 flex-1 truncate text-[12.5px]">
                      {video.label}
                      <span className="text-muted-foreground">
                        {" "}
                        · {video.shots} cảnh
                        {video.voiceover ? " · có lồng tiếng" : ""}
                        {video.cutdowns.length > 0
                          ? ` · bản cắt ${video.cutdowns.join(", ")}`
                          : ""}
                      </span>
                    </span>
                    <span className="studio-nums w-8 shrink-0 text-right font-mono text-[11px] text-muted-foreground">
                      {video.ratio}
                    </span>
                    {/* Video has no origin route — hold the badge column open
                        so the ratios stay on one axis down the whole list. */}
                    <span aria-hidden className="w-[76px] shrink-0" />
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
