"use client";

/**
 * A kit that already exists, shown instead of a form.
 *
 * A run takes six to twelve minutes. A judge has about that long for the whole
 * submission, so a campaign that has already been rendered has to open as a
 * result: pictures on screen, playable video, nothing to wait for. Regenerating
 * work that is already on the disk in order to look at it would be the worst
 * minute of the demo.
 *
 * Rebuilding stays one click away and is never automatic. It costs real money
 * and ten minutes, so it is a decision, and the button says what it will do
 * rather than implying a refresh.
 */

import { useState } from "react";
import { Download, Play, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { mediaUrl, type SavedResult } from "@/lib/studio-draft";

const PLATFORM_LABELS: Record<string, string> = {
  tiktok_shop: "TikTok Shop",
  shopee: "Shopee",
};

interface SavedKitProps {
  result: SavedResult;
  campaignName: string | null;
  /** Hands the screen back to the brief so a fresh run can be proposed. */
  onRebuild: () => void;
}

export function SavedKit({ result, campaignName, onRebuild }: SavedKitProps) {
  const [playing, setPlaying] = useState<string | null>(null);

  const videos = result.assets.filter((a) => a.kind === "video");
  const images = result.assets.filter((a) => a.kind === "image");

  return (
    <div className="studio-panel flex flex-col overflow-hidden">
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3.5">
        <div className="min-w-0">
          <h2 className="font-display truncate text-[15px] font-semibold tracking-tight">
            {campaignName ?? "Bộ kit đã dựng"}
          </h2>
          <p className="studio-nums mt-0.5 font-mono text-[12px] text-muted-foreground">
            {result.images} ảnh · {result.videos} video ·{" "}
            {(result.bytes / 1e6).toFixed(0)} MB
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <a
            href={mediaUrl(`/api/studio/${encodeURIComponent(result.campaign_id)}/zip`)}
            className="border-border/70 text-muted-foreground hover:border-primary/50 hover:text-foreground inline-flex h-9 items-center gap-1.5 rounded-md border px-3 text-[13px] transition-colors"
          >
            <Download aria-hidden className="size-3.5" />
            Tải .zip
          </a>
          {/* Not styled as the primary action: the kit on screen is the point,
              and ten minutes of rendering should never be one stray click. */}
          <Button
            type="button"
            variant="outline"
            onClick={onRebuild}
            className="h-9 gap-1.5 text-[13px]"
          >
            <RefreshCw aria-hidden className="size-3.5" />
            Dựng lại
          </Button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
        {videos.length > 0 ? (
          <section className="mb-6">
            <h3 className="mb-2.5 text-[12px] font-semibold text-foreground/80">
              Video
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {videos.map((asset) => (
                <figure
                  key={asset.name}
                  className="studio-option overflow-hidden rounded-lg"
                >
                  {playing === asset.name ? (
                    // Mounted only on demand: three autoplaying 1080p files
                    // would fetch a hundred megabytes before anyone pressed
                    // anything.
                    <video
                      src={mediaUrl(asset.url)}
                      controls
                      autoPlay
                      className="aspect-[9/16] w-full bg-black object-contain"
                    />
                  ) : (
                    <button
                      type="button"
                      onClick={() => setPlaying(asset.name)}
                      className="group relative flex aspect-[9/16] w-full items-center justify-center bg-black/40"
                    >
                      <span className="bg-primary text-primary-foreground grid size-11 place-items-center rounded-full transition-transform group-hover:scale-110">
                        <Play aria-hidden className="size-4 translate-x-[1px]" fill="currentColor" />
                      </span>
                    </button>
                  )}
                  <figcaption className="truncate px-2.5 py-1.5 font-mono text-[11px] text-muted-foreground">
                    {asset.name}
                  </figcaption>
                </figure>
              ))}
            </div>
          </section>
        ) : null}

        <section>
          <h3 className="mb-2.5 text-[12px] font-semibold text-foreground/80">
            Ảnh
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
            {images.map((asset) => (
              <a
                key={asset.name}
                href={mediaUrl(asset.url)}
                target="_blank"
                rel="noreferrer"
                className={cn(
                  "studio-option group block overflow-hidden rounded-lg",
                  "focus-visible:outline-primary focus-visible:outline-2"
                )}
              >
                {/* Plain <img>: these are files on a local mount, not remote
                    assets Next can optimise, and the grid is scrolled once. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={mediaUrl(asset.url)}
                  alt={asset.name}
                  loading="lazy"
                  className="aspect-square w-full bg-black/20 object-cover transition-transform duration-300 group-hover:scale-[1.03]"
                />
                <span className="flex items-baseline justify-between gap-2 px-2.5 py-1.5">
                  <span className="truncate font-mono text-[11px] text-muted-foreground">
                    {asset.name}
                  </span>
                  {asset.platform ? (
                    <span className="text-primary/80 shrink-0 text-[10px]">
                      {PLATFORM_LABELS[asset.platform] ?? asset.platform}
                    </span>
                  ) : null}
                </span>
              </a>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
