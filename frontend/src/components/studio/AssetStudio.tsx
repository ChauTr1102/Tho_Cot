"use client";

/**
 * The Asset Studio, as a component rather than a page.
 *
 * It runs in two places and must behave identically in both: at `/studio` as a
 * full screen, and inside the campaign pipeline as stage 03, where it replaced
 * a mock that faked a three-and-a-half-second agent and then printed hardcoded
 * creative routes. One state machine, two mounts — a second copy would drift
 * within a day, and the half nobody demos would be the half that rots.
 *
 * `campaignId` is how the pipeline says which campaign this is. Standalone, the
 * page reads it from `?campaign=`; embedded, the pipeline passes the campaign
 * the user has been walking through. Either way the studio never asks a person
 * to re-pick a product that was chosen and briefed upstream.
 *
 * `embedded` controls the chrome, not the behaviour. On its own route the
 * studio paints its own dark backdrop and masthead; inside the pipeline it
 * drops both and inherits the surrounding theme, because its components are
 * written against `--foreground` / `--primary` / `--border` rather than against
 * hardcoded colours. That is why the same graph can read as lime-on-black in one
 * place and ink-on-ivory in the other with no second stylesheet.
 */

// The stylesheets travel with the component, not with the route.
//
// Both used to be imported by `app/studio/layout.tsx`, which loads them for
// `/studio` and for nothing else. The moment this component was also mounted
// inside the campaign pipeline, that route got the markup and none of the CSS:
// React Flow lost its absolute positioning, so the minimap rendered inline as a
// black slab in the top-left corner and the nodes scattered unstyled, and every
// `.studio-*` rule — including the backdrop this component asks for — simply
// did not exist. Whatever mounts `AssetStudio` now gets its styling with it.
//
// Order is load-bearing: React Flow's own theme first, `studio.css` second,
// because the latter re-skins the former.
import "@xyflow/react/dist/style.css";
import "@/app/studio/studio.css";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { BriefPanel } from "@/components/studio/BriefPanel";
import { DraftPanel } from "@/components/studio/DraftPanel";
import { GraphCanvas } from "@/components/studio/GraphCanvas";
import { RunStage } from "@/components/studio/RunStage";
import { SavedKit } from "@/components/studio/SavedKit";
import { ThinkingPanel } from "@/components/studio/ThinkingPanel";
import { StudioHeader } from "@/components/studio/StudioHeader";
import { estimateKit } from "@/lib/studio-catalog";
import { useRunClock, useStudioStream } from "@/lib/studio-events";
import { api, ApiError } from "@/lib/api";
import {
  approveDraft,
  fetchSavedResult,
  listResearchCampaigns,
  requestDraft,
  type Draft,
  type GraphNodeSpecLite,
  type ResearchCampaign,
  type SavedResult,
} from "@/lib/studio-draft";
import type { NodeKind, StudioAssetDTOResponse, StudioNode } from "@/types/studio";
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

interface AssetStudioProps {
  /** The campaign to build for. Null lets the studio choose the first
      researched one, which is what a bare visit to /studio should do. */
  campaignId?: string | null;
  /** True when rendered inside the pipeline: no backdrop, no masthead. */
  embedded?: boolean;
  /**
   * Called with the real generated assets (CampaignOutputDTO shape, real
   * `/media/...` paths — not mock URLs) once a run finishes. The pipeline
   * uses this to feed real data into the QA gate / final report instead of
   * always falling back to buildMockCampaignOutput.
   */
  onAssetsReady?: (assets: StudioAssetDTOResponse) => void;
}

export function AssetStudio({
  campaignId: requestedCampaign = null,
  embedded = false,
  onAssetsReady,
}: AssetStudioProps) {
  const [platforms, setPlatforms] = useState<Platform[]>([
    "tiktok_shop",
    "shopee",
  ]);

  const [campaigns, setCampaigns] = useState<ResearchCampaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(null);
  const [direction, setDirection] = useState("");
  const [draft, setDraft] = useState<Draft | null>(null);
  const [draftId, setDraftId] = useState<string | null>(null);
  const [draftGraph, setDraftGraph] = useState<GraphNodeSpecLite[]>([]);
  const [approving, setApproving] = useState(false);

  // What this campaign already has on disk, and whether to show it. A judge
  // opening a finished campaign should see the kit, not a form; `showSaved`
  // goes false only when someone deliberately asks to rebuild.
  const [savedResult, setSavedResult] = useState<SavedResult | null>(null);
  const [showSaved, setShowSaved] = useState(true);

  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [stoppedAt, setStoppedAt] = useState<number | null>(null);

  // The studio's inbox. Fetched once; a research run that finishes while this
  // screen is open is rare enough that polling would cost more than it buys.
  //
  // `?campaign=` is how the pipeline screen hands work over: pressing Tiếp tục
  // after research lands here with the campaign already chosen, so the user
  // never re-picks something they just finished briefing. Read from
  // `location.search` rather than `useSearchParams` so the page keeps rendering
  // without a Suspense boundary. Falling back to the first ready campaign keeps
  // a direct visit to /studio useful.
  useEffect(() => {
    let cancelled = false;
    const requested = requestedCampaign;
    listResearchCampaigns()
      .then((rows) => {
        if (cancelled) return;
        setCampaigns(rows);
        const asked = requested
          ? rows.find((row) => row.id === requested)
          : undefined;
        if (asked) {
          // Named a campaign that exists. Select it only if research finished;
          // otherwise select nothing and let the rail show it greyed with its
          // real status. Quietly substituting a different campaign would build
          // the wrong product under a URL that named the right one.
          if (asked.status === "researched") setSelectedCampaign(asked.id);
          return;
        }
        const ready = rows.find((row) => row.status === "researched");
        if (ready) setSelectedCampaign(ready.id);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [requestedCampaign]);

  // Re-asked whenever the selection changes, and again after a run finishes, so
  // the kit that just rendered becomes the kit that opens next time.
  useEffect(() => {
    if (!selectedCampaign) {
      setSavedResult(null);
      return;
    }
    let cancelled = false;
    setShowSaved(true);
    fetchSavedResult(selectedCampaign)
      .then((result) => {
        if (!cancelled) setSavedResult(result?.built ? result : null);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [selectedCampaign]);

  // Named by whoever opened this screen? Then this studio is for that campaign
  // and no other. Offering the rest is only useful on a bare visit to /studio.
  const campaignPinned = Boolean(requestedCampaign);
  const visibleCampaigns = useMemo(
    () =>
      campaignPinned
        ? campaigns.filter((row) => row.id === requestedCampaign)
        : campaigns,
    [campaignPinned, campaigns, requestedCampaign]
  );

  const stream = useStudioStream(campaignId);
  const elapsedSec = useRunClock(startedAt, stoppedAt);

  const campaign = useMemo(
    () => campaigns.find((item) => item.id === selectedCampaign) ?? null,
    [campaigns, selectedCampaign]
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

  // Once a run reaches a terminal state, pull the real generated assets
  // (CampaignOutputDTO shape, real /media/... paths) so the caller can feed
  // them into the QA gate / final report instead of relying on mock data.
  // `finished` also covers "disconnected", so a page that was left open
  // through a completed run still picks the result up once reconnected.
  useEffect(() => {
    if (!finished || !campaignId || !onAssetsReady) return;
    let cancelled = false;
    api
      .getStudioAssets(campaignId)
      .then((res) => {
        if (!cancelled && res.data) onAssetsReady(res.data);
      })
      .catch((error: unknown) => {
        // Assets not being ready yet (e.g. a run that errored before
        // producing anything) is expected, not exceptional — the caller
        // simply keeps whatever fallback it already has.
        if (!(error instanceof ApiError)) {
          console.warn("studio.assets_fetch_failed", error);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [finished, campaignId, onAssetsReady]);

  // Propose, then approve. The director reads the brief and writes a register
  // for whatever the user asked for; nothing renders until a person says yes.
  const handlePropose = useCallback(async () => {
    if (platforms.length === 0 || !selectedCampaign) return;

    setStarting(true);
    setCampaignId(null);
    setStoppedAt(null);
    setDraft(null);

    try {
      // The campaign carries its own brief, plan and photos — everything the
      // director needs is already on file, so this call sends an id and a mood.
      const result = await requestDraft({
        campaign_id: selectedCampaign,
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
  }, [direction, platforms, selectedCampaign]);

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
    <div
      className={
        embedded
          ? // Inherits the surrounding theme. Every rule in `studio.css` reads
            // tokens rather than hex, so the same graph renders on ivory inside
            // the pipeline and on near-black at /studio with no second
            // stylesheet — provided the stylesheets load at all, which is the
            // bug this was previously mistaken for.
            "flex flex-col"
          : "studio-backdrop studio-theme-dark flex min-h-screen flex-col"
      }
    >
      {embedded ? null : (
        <StudioHeader
          status={stream.status}
          campaignId={campaignId}
          brandName={campaign?.name ?? null}
        />
      )}

      {/* No page head. The masthead already names the product and the campaign,
          and a title block plus a route legend cost about 200px of the fold —
          on a laptop that was the difference between a graph readable at 33%
          and one readable at 50%. The three routes are still explained, by the
          route ledger under the stage, where they carry live counts instead of
          a static description. */}
      <main
        className={
          embedded
            ? "w-full px-3 pt-3 pb-4"
            : "mx-auto w-full max-w-[1760px] flex-1 px-4 pt-4 pb-10 sm:px-6"
        }
      >
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
              platforms={platforms}
              onPlatformsChange={setPlatforms}
              onRun={handlePropose}
              campaigns={visibleCampaigns}
              selectedCampaign={selectedCampaign}
              onCampaignChange={setSelectedCampaign}
              campaignPinned={campaignPinned}
              direction={direction}
              onDirectionChange={setDirection}
              running={running}
              starting={starting}
              campaignId={campaignId}
            />
          )}

          {/* While the director is writing there is no graph to draw and no run
              to report, so the stage gives its whole area to saying what is
              being decided. Ninety seconds of empty canvas reads as broken. */}
          {savedResult && showSaved && !campaignId && !draft && !starting ? (
            <SavedKit
              result={savedResult}
              campaignName={campaign?.name ?? null}
              platforms={platforms}
              onRebuild={() => setShowSaved(false)}
            />
          ) : starting ? (
            <ThinkingPanel
              direction={direction}
              campaignName={campaign?.name ?? null}
            />
          ) : (
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
          )}
        </div>
      </main>
    </div>
  );
}
