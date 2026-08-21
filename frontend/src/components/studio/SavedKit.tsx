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
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export function SavedKit({
  result,
  campaignName,
  platforms,
  onRebuild,
  sidebarOpen,
  onToggleSidebar,
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

  const savedMeta = useMemo(() => ({
    campaignName: campaignName ?? "Bộ kit đã dựng",
    images: result.images,
    videos: result.videos,
    bytes: result.bytes,
    zipUrl: mediaUrl(`/api/studio/${encodeURIComponent(result.campaign_id)}/zip`),
    onRebuild,
  }), [campaignName, result, onRebuild]);

  return (
    <div className="flex h-full min-h-[560px] flex-1 flex-col overflow-hidden w-full relative">
      <GraphCanvas
        nodes={nodes}
        platforms={platforms}
        campaignId={result.campaign_id}
        awaiting={false}
        savedMeta={savedMeta}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={onToggleSidebar}
      />
    </div>
  );
}
