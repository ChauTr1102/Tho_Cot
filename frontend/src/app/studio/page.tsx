"use client";

/**
 * The Asset Studio screen.
 *
 * A seller picks one of their products and the marketplaces they sell it on,
 * presses Run, and gets back a launch-ready kit of images and video per
 * marketplace. The run takes 6–12 minutes, so the screen's whole job is to
 * make that wait legible: what is being built, how far along it is, which of
 * the three routes each asset took, and what just happened.
 *
 * Layout: brief rail left, live run stage right. This component owns the run
 * lifecycle (`campaignId`, the wall clock, the POST) and hands everything else
 * down. Task 13 changes exactly one JSX element here — the canvas child.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { BriefPanel } from "@/components/studio/BriefPanel";
import { GraphCanvasPlaceholder } from "@/components/studio/GraphCanvasPlaceholder";
import { OriginLegend } from "@/components/studio/OriginBadge";
import { RunStage } from "@/components/studio/RunStage";
import { StudioHeader } from "@/components/studio/StudioHeader";
import { DEMO_BRANDS, estimateKit } from "@/lib/studio-catalog";
import { startStudioRun, useRunClock, useStudioStream } from "@/lib/studio-events";
import type { Platform } from "@/types/studio";

export default function StudioPage() {
  const [brandDir, setBrandDir] = useState<string>(DEMO_BRANDS[0].dir);
  const [platforms, setPlatforms] = useState<Platform[]>([
    "tiktok_shop",
    "shopee",
  ]);

  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [stoppedAt, setStoppedAt] = useState<number | null>(null);

  const stream = useStudioStream(campaignId);
  const elapsedSec = useRunClock(startedAt, stoppedAt);

  const brand = useMemo(
    () => DEMO_BRANDS.find((item) => item.dir === brandDir) ?? null,
    [brandDir]
  );
  const plannedOrigins = useMemo(
    () => estimateKit(platforms).origins,
    [platforms]
  );

  const finished = stream.status === "done" || stream.status === "disconnected";
  const running = campaignId !== null && !finished;

  // The clock stops the moment the stream reaches a terminal state, so the
  // final figure is the run's real duration rather than time-since-page-load.
  useEffect(() => {
    if (finished && startedAt !== null && stoppedAt === null) {
      setStoppedAt(Date.now());
    }
  }, [finished, startedAt, stoppedAt]);

  const handleRun = useCallback(async () => {
    if (platforms.length === 0) return;

    setStarting(true);
    setCampaignId(null);
    setStoppedAt(null);

    try {
      const id = await startStudioRun({ brand_dir: brandDir, platforms });
      setStartedAt(Date.now());
      setCampaignId(id);
      toast.success("Studio đã bắt đầu chạy", {
        description: `Chiến dịch ${id} · ước tính 6–12 phút`,
      });
    } catch (error) {
      setStartedAt(null);
      toast.error("Không khởi tạo được lượt chạy", {
        description:
          error instanceof Error
            ? error.message
            : "Backend studio chưa phản hồi.",
      });
    } finally {
      setStarting(false);
    }
  }, [brandDir, platforms]);

  return (
    <div className="studio-backdrop flex min-h-screen flex-col">
      <StudioHeader
        status={stream.status}
        campaignId={campaignId}
        brandName={brand?.name ?? null}
      />

      <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 pb-14 sm:px-6">
        {/* Page head. One kicker on the page, at the top, as the brand
            signature — sub-sections get plain titles rather than eyebrows. */}
        <div className="flex flex-col gap-5 py-5 lg:flex-row lg:items-end lg:justify-between lg:gap-12 lg:py-6">
          <div className="max-w-2xl">
            <p className="text-[11px] font-semibold tracking-[0.22em] text-primary uppercase">
              Asset Studio
            </p>
            <h1 className="mt-2 text-[27px] leading-[1.08] font-semibold tracking-[-0.025em] text-balance sm:text-[31px] xl:text-[35px]">
              Từ ảnh sản phẩm thật
              <br />
              <span className="text-primary">đến kit sẵn đăng bán</span>
            </h1>
            <p className="mt-2.5 max-w-xl text-[14px] leading-relaxed text-muted-foreground text-pretty">
              Chọn sản phẩm và sàn mục tiêu. Studio dựng đủ ảnh và video đúng
              chuẩn từng sàn, giữ nguyên sản phẩm thật — 6–12 phút, hiện rõ từng
              bước.
            </p>
          </div>

          {/* The three routes, explained before any asset appears. This is the
              studio's commercial judgement, not a legend for a colour key. */}
          <OriginLegend className="w-full max-w-sm shrink-0 lg:w-[22rem]" />
        </div>

        <div className="grid items-start gap-4 lg:grid-cols-[minmax(300px,340px)_minmax(0,1fr)]">
          <BriefPanel
            brandDir={brandDir}
            onBrandChange={setBrandDir}
            platforms={platforms}
            onPlatformsChange={setPlatforms}
            onRun={handleRun}
            running={running}
            starting={starting}
            campaignId={campaignId}
          />

          <RunStage
            status={stream.status}
            progress={stream.progress}
            elapsedSec={elapsedSec}
            nodes={stream.nodes}
            activity={stream.activity}
            error={stream.error}
            plannedOrigins={plannedOrigins}
            onRetry={stream.reconnect}
          >
            {/* ─── TASK 13: swap this element for <GraphCanvas /> ─────────── */}
            <GraphCanvasPlaceholder
              nodes={stream.nodes}
              platforms={platforms}
              awaiting={running && stream.nodes.length === 0}
            />
          </RunStage>
        </div>
      </main>
    </div>
  );
}
