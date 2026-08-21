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
 * down — including to `GraphCanvas`, which is where the run is actually
 * watched.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { BriefPanel } from "@/components/studio/BriefPanel";
import { DraftPanel } from "@/components/studio/DraftPanel";
import { GraphCanvas } from "@/components/studio/GraphCanvas";
import { OriginLegend } from "@/components/studio/OriginBadge";
import { RunStage } from "@/components/studio/RunStage";
import { StudioHeader } from "@/components/studio/StudioHeader";
import { DEMO_BRANDS, estimateKit } from "@/lib/studio-catalog";
import { useRunClock, useStudioStream } from "@/lib/studio-events";
import {
  approveDraft,
  requestDraft,
  type Draft,
  type GraphNodeSpecLite,
} from "@/lib/studio-draft";
import type { NodeKind, StudioNode } from "@/types/studio";
import type { Platform } from "@/types/studio";

/**
 * The director names node kinds for what they are *for*; the executor names
 * them for what they *do*. The canvas speaks the executor's vocabulary, so a
 * proposal has to be translated before it can be drawn beside a live run.
 */
const DIRECTOR_KIND_TO_NODE_KIND: Record<string, NodeKind> = {
  inventory: "inventory",
  hero: "image",
  image: "image",
  poster: "image",
  keyframe: "keyframe",
  clip: "video",
  voiceover: "compose",
  assemble: "compose",
};

export default function StudioPage() {
  const [brandDir, setBrandDir] = useState<string>(DEMO_BRANDS[0].dir);
  const [platforms, setPlatforms] = useState<Platform[]>([
    "tiktok_shop",
    "shopee",
  ]);

  const [direction, setDirection] = useState("");
  const [draft, setDraft] = useState<Draft | null>(null);
  const [draftId, setDraftId] = useState<string | null>(null);
  const [draftGraph, setDraftGraph] = useState<GraphNodeSpecLite[]>([]);
  const [approving, setApproving] = useState(false);

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

  // The proposal drawn as a graph, greyed out. Every node the run will create
  // exists here before anything is generated, which is the point of approving:
  // you see the shape of the work, not a list of its names.
  const previewNodes = useMemo<StudioNode[]>(
    () =>
      draftGraph.map((node) => ({
        id: node.id,
        kind: DIRECTOR_KIND_TO_NODE_KIND[node.kind] ?? "image",
        deps: node.deps,
        state: "pending",
        elapsed_sec: 0,
        payload: {},
        updated_at: 0,
      })),
    [draftGraph]
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

  // Propose, then approve. The director reads the brief and writes a register
  // for whatever the user asked for; nothing renders until a person says yes.
  const handlePropose = useCallback(async () => {
    if (platforms.length === 0) return;

    setStarting(true);
    setCampaignId(null);
    setStoppedAt(null);
    setDraft(null);

    try {
      const result = await requestDraft({
        brand_dir: brandDir,
        direction,
        with_video: true,
      });
      setDraft(result.draft);
      setDraftId(result.campaignId);
      setDraftGraph(result.graph.nodes);
      toast.success("Đề xuất đã sẵn sàng", {
        description: `Ngôn ngữ hình: ${result.draft.register.name}`,
      });
    } catch (error) {
      toast.error("Không lấy được đề xuất", {
        description:
          error instanceof Error ? error.message : "Backend chưa phản hồi.",
      });
    } finally {
      setStarting(false);
    }
  }, [brandDir, direction, platforms]);

  const handleApprove = useCallback(
    async (edited: Partial<Draft> | undefined) => {
      if (!draftId) return;
      setApproving(true);
      try {
        const id = await approveDraft(draftId, { draft: edited, withVideo: true });
        setStartedAt(Date.now());
        setCampaignId(id);
        setDraft(null);
        toast.success("Đã duyệt — studio bắt đầu dựng", {
          description: `Chiến dịch ${id}`,
        });
      } catch (error) {
        toast.error("Không bắt đầu được", {
          description:
            error instanceof Error ? error.message : "Backend chưa phản hồi.",
        });
      } finally {
        setApproving(false);
      }
    },
    [draftId]
  );

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
          {/* One rail, two states. While a proposal is on the table it takes
              the whole rail — it is the only decision that matters at that
              moment, and leaving the brief editable beside it invites changes
              that the proposal no longer reflects. */}
          {draft ? (
            <DraftPanel
              draft={draft}
              nodeCount={draftGraph.length}
              approving={approving}
              onApprove={handleApprove}
              onDiscard={() => {
                setDraft(null);
                setDraftId(null);
                setDraftGraph([]);
              }}
            />
          ) : (
            <BriefPanel
              brandDir={brandDir}
              onBrandChange={setBrandDir}
              platforms={platforms}
              onPlatformsChange={setPlatforms}
              onRun={handlePropose}
              direction={direction}
              onDirectionChange={setDirection}
              running={running}
              starting={starting}
              campaignId={campaignId}
            />
          )}

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
            {/* The graph, as a canvas: pan, zoom, drag, and every finished
                node showing the picture it produced. Before a run exists it
                falls back to the kit manifest — see `KitManifest.tsx`. */}
            <GraphCanvas
              nodes={campaignId ? stream.nodes : previewNodes}
              platforms={platforms}
              campaignId={campaignId}
              awaiting={running && stream.nodes.length === 0}
            />
          </RunStage>
        </div>
      </main>
    </div>
  );
}
