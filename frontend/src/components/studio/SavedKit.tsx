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

import { useMemo } from "react";
import { Download, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { GraphCanvas } from "@/components/studio/GraphCanvas";
import { mediaUrl, type SavedResult } from "@/lib/studio-draft";
import type { NodeKind, NodeState, Platform, StudioNode } from "@/types/studio";

interface SavedKitProps {
  result: SavedResult;
  campaignName: string | null;
  platforms: Platform[];
  /** Hands the screen back to the brief so a fresh run can be proposed. */
  onRebuild: () => void;
}

export function SavedKit({
  result,
  campaignName,
  platforms,
  onRebuild,
}: SavedKitProps) {
  // The backend hands back file paths; the canvas wants absolute URLs and the
  // enums the live stream uses, so the translation happens once here.
  const nodes = useMemo<StudioNode[]>(
    () =>
      result.nodes.map((node) => ({
        id: node.id,
        kind: node.kind as NodeKind,
        deps: node.deps,
        state: node.state as NodeState,
        elapsed_sec: node.elapsed_sec,
        payload: node.payload.url
          ? { ...node.payload, url: mediaUrl(node.payload.url) }
          : node.payload,
        updated_at: node.updated_at,
      })),
    [result.nodes]
  );

  return (
    <div className="studio-panel flex h-full min-h-[560px] flex-1 flex-col overflow-hidden">
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
            className="border-border/70 text-muted-foreground hover:border-primary/50 hover:text-foreground inline-flex h-9 items-center gap-1.5 rounded-none border px-3 text-[13px] transition-colors"
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
            className="h-9 gap-1.5 text-[13px] rounded-none"
          >
            <RefreshCw aria-hidden className="size-3.5" />
            Dựng lại
          </Button>
        </div>
      </div>

      {/* The graph, not a contact sheet. Every picture here came from a named
          step with named inputs, and that structure is the product's argument —
          a grid of thumbnails is what any folder viewer would show. */}
      <div className="min-h-0 flex-1 flex flex-col h-full w-full">
        <GraphCanvas
          nodes={nodes}
          platforms={platforms}
          campaignId={result.campaign_id}
          awaiting={false}
        />
      </div>
    </div>
  );
}
