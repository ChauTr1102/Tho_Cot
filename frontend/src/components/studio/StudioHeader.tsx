"use client";

/**
 * Top bar for the studio screen.
 *
 * Follows the event site's header — mark and wordmark left, context centre,
 * controls right — with one deliberate change: the site's coral "Tham gia
 * Hackathon" button is replaced by a live connection chip. A second coral CTA
 * up here would compete with the Run button, which is the only action on this
 * screen that matters; a monitoring tool needs to know whether the stream is
 * alive far more than it needs a duplicate button.
 */

import { Globe } from "lucide-react";

import { cn } from "@/lib/utils";
import type { StudioStreamStatus } from "@/types/studio";

interface StreamChipMeta {
  label: string;
  dot: string;
  text: string;
  border: string;
  live: boolean;
}

const STREAM_CHIP: Record<StudioStreamStatus, StreamChipMeta> = {
  idle: {
    label: "Chưa chạy",
    dot: "bg-muted-foreground/60",
    text: "text-muted-foreground",
    border: "border-border",
    live: false,
  },
  connecting: {
    label: "Đang kết nối",
    dot: "bg-gold",
    text: "text-gold",
    border: "border-gold/35",
    live: true,
  },
  reconnecting: {
    label: "Đang nối lại",
    dot: "bg-gold",
    text: "text-gold",
    border: "border-gold/35",
    live: true,
  },
  streaming: {
    label: "Đang nhận sự kiện",
    dot: "bg-primary",
    text: "text-primary",
    border: "border-primary/40",
    live: true,
  },
  done: {
    label: "Hoàn tất",
    dot: "bg-primary",
    text: "text-primary",
    border: "border-primary/40",
    live: false,
  },
  disconnected: {
    label: "Mất kết nối",
    dot: "bg-destructive",
    text: "text-destructive",
    border: "border-destructive/40",
    live: false,
  },
};

interface StudioHeaderProps {
  status: StudioStreamStatus;
  /** Shown centre once a run exists — the thing the screen is about. */
  campaignId: string | null;
  brandName: string | null;
}

export function StudioHeader({
  status,
  campaignId,
  brandName,
}: StudioHeaderProps) {
  const chip = STREAM_CHIP[status] ?? STREAM_CHIP.idle;

  return (
    <header className="sticky top-0 z-30 w-full border-b border-border bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 w-full max-w-[1440px] items-center gap-4 px-4 sm:px-6">
        {/* Mark + wordmark */}
        <div className="flex shrink-0 items-center gap-2.5">
          <span
            aria-hidden
            className="grid size-7 place-items-center rounded-none bg-primary font-display text-[11px] font-bold tracking-tight text-primary-foreground"
          >
            TC
          </span>
          <span className="font-display text-[15px] font-semibold tracking-tight">
            Thợ Cốt
          </span>
          <span aria-hidden className="h-3.5 w-px bg-border" />
          <span className="text-[13px] text-muted-foreground">
            Asset Studio
          </span>
        </div>

        {/* Run context. Empty before the first run rather than filled with a
            placeholder — an empty centre is honest, a fake id is not. */}
        <div className="hidden min-w-0 flex-1 justify-center lg:flex">
          {campaignId ? (
            <div className="flex min-w-0 items-center gap-2 rounded-none border border-border bg-muted/60 py-1 pr-3 pl-2.5">
              {brandName ? (
                <span className="truncate text-[12.5px] text-foreground/90">
                  {brandName}
                </span>
              ) : null}
              <span aria-hidden className="h-3 w-px bg-border" />
              <span className="studio-nums font-mono text-[11.5px] text-muted-foreground">
                {campaignId}
              </span>
            </div>
          ) : null}
        </div>

        <div className="ml-auto flex items-center gap-2 lg:ml-0">
          {/* Locale. VI is the shipped language; EN is disabled rather than
              faked, so the control tells the truth about what exists. */}
          <div className="flex items-center gap-1 rounded-none border border-border bg-muted/50 p-0.5 pl-2">
            <Globe aria-hidden className="size-3.5 text-muted-foreground" />
            <button
              type="button"
              disabled
              title="Bản tiếng Anh đang được chuẩn bị"
              className="rounded-none px-2 py-0.5 text-[11.5px] font-medium text-muted-foreground/60"
            >
              EN
            </button>
            <span
              aria-current="true"
              className="rounded-none bg-primary px-2 py-0.5 text-[11.5px] font-semibold text-primary-foreground"
            >
              VI
            </span>
          </div>

          <div
            role="status"
            className={cn(
              "flex items-center gap-2 rounded-none border bg-muted/40 py-1 pr-2.5 pl-2",
              chip.border
            )}
          >
            <span
              aria-hidden
              className={cn(
                "relative size-1.5 rounded-full",
                chip.dot,
                chip.live && "studio-live-dot",
                chip.text
              )}
            />
            <span className={cn("text-[11.5px] font-medium", chip.text)}>
              {chip.label}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
