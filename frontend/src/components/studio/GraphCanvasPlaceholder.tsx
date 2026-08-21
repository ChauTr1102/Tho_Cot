"use client";

/**
 * The canvas region, until Task 13's React Flow graph replaces it.
 *
 * ┌─ FOR TASK 13 ────────────────────────────────────────────────────────────┐
 * │ Replace `<GraphCanvasPlaceholder …/>` in `app/studio/page.tsx` with      │
 * │ `<GraphCanvas nodes={stream.nodes} />`. It is a single JSX element and   │
 * │ nothing else on the screen depends on this file.                        │
 * │                                                                          │
 * │ Reusable pieces already built for you:                                  │
 * │   • `state-styles.ts` → `NODE_STATE_META` (the six state treatments      │
 * │     from the plan's table) and `kindMeta()` (icon + Vietnamese label).   │
 * │   • `OriginBadge` → the REUSE / REMIX / GENERATE chip.                   │
 * │   • `formatElapsed()` in `lib/studio-events.ts` → `42s` / `4m12s`.       │
 * │   • `.studio-live-dot`, `.studio-panel`, `.studio-nums` in globals.css,  │
 * │     all with prefers-reduced-motion fallbacks already wired.             │
 * │ `computeLayers()` below is the same left-to-right dependency layering    │
 * │ the canvas needs; lift it if it helps.                                   │
 * └──────────────────────────────────────────────────────────────────────────┘
 *
 * Two states, both real rather than decorative:
 *
 *   No nodes yet — the kit manifest. It lists exactly what will be produced
 *   for each selected marketplace, with the route each slot is planned to take.
 *   An empty state that teaches the interface is worth more than a spinner, and
 *   this one doubles as the answer to "what am I waiting for".
 *
 *   Nodes present — a compact dependency-layered board of node chips. Enough to
 *   watch a real run, and the direct ancestor of the canvas that supersedes it.
 */

import { Film, Image as ImageIcon } from "lucide-react";

import { OriginBadge } from "@/components/studio/OriginBadge";
import { NODE_STATE_META, kindMeta } from "@/components/studio/state-styles";
import { KITS } from "@/lib/studio-catalog";
import { formatElapsed } from "@/lib/studio-events";
import { cn } from "@/lib/utils";
import type { Platform, StudioNode } from "@/types/studio";

interface GraphCanvasPlaceholderProps {
  nodes: StudioNode[];
  platforms: Platform[];
  /** True once Run was pressed but no `graph` event has arrived yet. */
  awaiting: boolean;
}

export function GraphCanvasPlaceholder({
  nodes,
  platforms,
  awaiting,
}: GraphCanvasPlaceholderProps) {
  if (nodes.length > 0) return <NodeBoard nodes={nodes} />;
  if (awaiting) return <AwaitingGraph />;
  return <KitManifest platforms={platforms} />;
}

/* ──────────────────────────────────────────────────────────────────────────
 * Dependency layering — the same left-to-right ordering Task 13 needs
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * Group nodes into dependency layers: layer 0 has no dependencies, layer n
 * depends on something in layer n-1. Cycles are impossible in a DAG but are
 * guarded anyway, because a malformed `graph` event must not hang the render.
 */
export function computeLayers(nodes: StudioNode[]): StudioNode[][] {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const depth = new Map<string, number>();

  const resolve = (id: string, seen: Set<string>): number => {
    const cached = depth.get(id);
    if (cached !== undefined) return cached;
    if (seen.has(id)) return 0;

    const node = byId.get(id);
    seen.add(id);
    const value =
      !node || node.deps.length === 0
        ? 0
        : 1 +
          Math.max(...node.deps.map((dependency) => resolve(dependency, seen)));
    seen.delete(id);

    depth.set(id, value);
    return value;
  };

  for (const node of nodes) resolve(node.id, new Set<string>());

  const layers: StudioNode[][] = [];
  for (const node of nodes) {
    const index = depth.get(node.id) ?? 0;
    (layers[index] ??= []).push(node);
  }
  return layers.filter(Boolean);
}

function NodeBoard({ nodes }: { nodes: StudioNode[] }) {
  const layers = computeLayers(nodes);

  return (
    <div className="studio-panel min-h-[300px] overflow-x-auto p-4">
      <div className="flex min-w-max items-start gap-3">
        {layers.map((layer, index) => (
          <div key={index} className="flex w-[190px] shrink-0 flex-col gap-2">
            <div className="flex items-center gap-2 px-0.5">
              <span className="studio-nums font-mono text-[11px] text-muted-foreground">
                Lớp {index + 1}
              </span>
              <span aria-hidden className="h-px flex-1 bg-border" />
            </div>
            {layer.map((node) => (
              <NodeChip key={node.id} node={node} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function NodeChip({ node }: { node: StudioNode }) {
  const state = NODE_STATE_META[node.state] ?? NODE_STATE_META.pending;
  const kind = kindMeta(node.kind);
  const Icon = kind.icon;
  const origin = node.payload?.origin;

  return (
    <article
      className={cn(
        "rounded-lg border bg-card/70 px-2.5 py-2 transition-colors",
        state.chip
      )}
    >
      <div className="flex items-center gap-1.5">
        <span
          aria-hidden
          className={cn(
            "relative size-1.5 shrink-0 rounded-full",
            state.dot,
            state.text,
            state.live && "studio-live-dot"
          )}
        />
        <Icon aria-hidden className="size-3 shrink-0 text-muted-foreground" />
        <span className="min-w-0 flex-1 truncate font-mono text-[11px]">
          {node.id}
        </span>
      </div>

      <div className="mt-1.5 flex items-center justify-between gap-2">
        <span className={cn("text-[11px] font-medium", state.text)}>
          {state.label}
          {node.state === "retry" && node.payload?.attempt
            ? ` ${node.payload.attempt}`
            : ""}
        </span>
        {node.elapsed_sec > 0 ? (
          <span className="studio-nums font-mono text-[11px] text-muted-foreground">
            {formatElapsed(node.elapsed_sec)}
          </span>
        ) : null}
      </div>

      {origin ? (
        <div className="mt-1.5">
          <OriginBadge origin={origin} size="xs" />
        </div>
      ) : null}
    </article>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Waiting for the first event
 * ────────────────────────────────────────────────────────────────────────── */

function AwaitingGraph() {
  return (
    <div className="studio-panel min-h-[300px] p-4">
      <p className="text-[12.5px] text-muted-foreground">
        Đang chờ sơ đồ graph từ backend…
      </p>
      <div className="mt-3.5 flex items-start gap-3">
        {[4, 3, 5].map((count, column) => (
          <div key={column} className="flex w-[190px] shrink-0 flex-col gap-2">
            {Array.from({ length: count }).map((_, row) => (
              <div
                key={row}
                className="h-[58px] rounded-lg border border-border bg-muted/35"
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

function KitManifest({ platforms }: { platforms: Platform[] }) {
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
