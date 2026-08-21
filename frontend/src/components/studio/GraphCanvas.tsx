"use client";

/**
 * The studio's live dependency graph, as a canvas you can move around in.
 *
 * The screen it replaces was correct and unreadable: fixed columns, a chip per
 * node, and the actual pictures hidden in a gallery below. What a judge needs
 * to see is a board filling in with real photographs — a Shopee main image
 * cropped from the brand's own shot appearing in a tenth of a second, three
 * columns away from a video clip that will take another three minutes — and
 * that only works if the results land on the nodes.
 *
 * Design decisions that are load-bearing:
 *
 *   **Layout runs once.** The `graph` event carries the whole DAG before any
 *   node starts, so the board is arranged up front and never re-arranged. A
 *   run emits an event every few seconds for ten minutes; re-laying out on any
 *   of them would yank the canvas out from under whoever is reading it.
 *
 *   **A node event touches one node.** Both sync effects rebuild their array
 *   but reuse the previous object for every entry that did not change, so
 *   React Flow re-renders exactly the box that moved and React bails out of
 *   the rest.
 *
 *   **User position always wins.** Dragged nodes are remembered, and nothing
 *   short of the explicit "Sắp xếp lại" button moves a node the user placed.
 */

import {
  Background,
  BackgroundVariant,
  MiniMap,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  useViewport,
  type EdgeTypes,
  type NodeTypes,
} from "@xyflow/react";
import {
  Download,
  Fullscreen,
  LayoutGrid,
  Map as MapIcon,
  Maximize,
  Minimize,
  Minus,
  PanelLeft,
  PanelLeftClose,
  Plus,
  RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import {
  GraphCanvasProvider,
  GraphNode,
  type GraphCanvasServices,
  type GraphFlowNode,
} from "@/components/studio/GraphNode";
import { GraphEdge, type GraphFlowEdge } from "@/components/studio/GraphEdge";
import { MediaViewer } from "@/components/studio/MediaViewer";
import {
  computeDeadBranch,
  layoutGraph,
  nodeHeight,
  nodeWidth,
  type Point,
} from "@/components/studio/graph-layout";
import { AwaitingGraph, KitManifest } from "@/components/studio/KitManifest";
import { rerunStudioNode, useRerunSupport } from "@/lib/studio-events";
import { cn } from "@/lib/utils";
import type { NodeState, Platform, RerunSupport, StudioNode } from "@/types/studio";

const nodeTypes: NodeTypes = { studio: GraphNode };
const edgeTypes: EdgeTypes = { studio: GraphEdge };

/** States a dependency is satisfied by — a degraded node still produced a file. */
const SUCCESS_STATES: ReadonlySet<NodeState> = new Set<NodeState>([
  "done",
  "degraded",
]);
const TERMINAL_STATES: ReadonlySet<NodeState> = new Set<NodeState>([
  "done",
  "degraded",
  "failed",
]);

const ORIGIN: Point = { x: 0, y: 0 };

/**
 * Breathing room around the board when framing it. Tight on purpose: a
 * six-column graph in a laptop-sized panel is already zoomed to about half,
 * and every percent of padding comes straight off how big the pictures are.
 */
const FIT_PADDING = 0.05;

export interface SavedKitMeta {
  campaignName: string | null;
  images: number;
  videos: number;
  bytes: number;
  zipUrl: string;
  onRebuild: () => void;
}

interface GraphCanvasProps {
  nodes: StudioNode[];
  platforms: Platform[];
  campaignId: string | null;
  /** True once Run was pressed but no `graph` event has arrived yet. */
  awaiting: boolean;
  savedMeta?: SavedKitMeta;
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export function GraphCanvas({
  nodes,
  platforms,
  campaignId,
  awaiting,
  savedMeta,
  sidebarOpen,
  onToggleSidebar,
}: GraphCanvasProps) {
  if (nodes.length === 0) {
    return awaiting ? <AwaitingGraph /> : <KitManifest platforms={platforms} />;
  }
  return (
    <ReactFlowProvider>
      <Board
        nodes={nodes}
        campaignId={campaignId}
        savedMeta={savedMeta}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={onToggleSidebar}
      />
    </ReactFlowProvider>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * The board
 * ────────────────────────────────────────────────────────────────────────── */

function Board({
  nodes,
  campaignId,
  savedMeta,
  sidebarOpen,
  onToggleSidebar,
}: {
  nodes: StudioNode[];
  campaignId: string | null;
  savedMeta?: SavedKitMeta;
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}) {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState<GraphFlowNode>([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState<GraphFlowEdge>([]);
  const [viewing, setViewing] = useState<StudioNode | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [showMiniMap, setShowMiniMap] = useState(true);

  const { fitView, zoomIn, zoomOut } = useReactFlow();
  /** The canvas shell, watched for resizes so the board can re-frame itself. */
  const shellRef = useRef<HTMLDivElement | null>(null);

  /** Where auto-layout put each node. Recomputed only when the DAG changes. */
  const layoutRef = useRef<Map<string, Point>>(new Map());
  /** Where the *user* put each node. Never overwritten except on demand. */
  const pinnedRef = useRef<Map<string, Point>>(new Map());
  const fittedRef = useRef(false);

  const deadSet = useMemo(() => computeDeadBranch(nodes), [nodes]);

  /* -- a new run starts from a clean board ------------------------------- */
  useEffect(() => {
    pinnedRef.current = new Map();
    layoutRef.current = new Map();
    fittedRef.current = false;
  }, [campaignId]);

  /* -- nodes ------------------------------------------------------------- */
  useEffect(() => {
    setRfNodes((previous) => {
      const previousById = new Map(previous.map((item) => [item.id, item]));
      const sameGraph =
        previous.length === nodes.length &&
        nodes.every((node) => previousById.has(node.id));

      if (!sameGraph) layoutRef.current = layoutGraph(nodes);
      const layout = layoutRef.current;

      let changed = !sameGraph;
      const next = nodes.map((node) => {
        const existing = previousById.get(node.id);
        const dead = deadSet.has(node.id);

        // The single most important line in this file: an unchanged node keeps
        // its exact object, so React Flow and React both skip it entirely.
        if (existing && existing.data.node === node && existing.data.dead === dead) {
          return existing;
        }
        changed = true;

        const position =
          existing?.position ??
          pinnedRef.current.get(node.id) ??
          layout.get(node.id) ??
          ORIGIN;

        const base: GraphFlowNode = existing ?? {
          id: node.id,
          type: "studio",
          position,
          // Declared rather than measured, so `fitView` can frame the board
          // on the same frame it appears rather than one paint later.
          width: nodeWidth(node.kind),
          height: nodeHeight(node.kind),
          data: { node, dead },
        };

        return { ...base, position, data: { node, dead } };
      });

      return changed ? next : previous;
    });
  }, [nodes, deadSet, setRfNodes]);

  /* -- edges ------------------------------------------------------------- */
  useEffect(() => {
    const byId = new Map(nodes.map((node) => [node.id, node]));

    setRfEdges((previous) => {
      const previousById = new Map(previous.map((edge) => [edge.id, edge]));
      const next: GraphFlowEdge[] = [];
      let changed = false;

      for (const node of nodes) {
        for (const dep of node.deps) {
          const source = byId.get(dep);
          if (!source) continue;

          const id = `${dep}~${node.id}`;
          const dead = deadSet.has(node.id) || source.state === "failed";
          // Animated strictly while the downstream node works, so the number
          // of moving edges is the number of things actually happening.
          const active =
            !dead && (node.state === "running" || node.state === "retry");
          const settled =
            !dead &&
            SUCCESS_STATES.has(source.state) &&
            TERMINAL_STATES.has(node.state);

          const existing = previousById.get(id);
          if (
            existing?.data &&
            existing.data.active === active &&
            existing.data.dead === dead &&
            existing.data.settled === settled
          ) {
            next.push(existing);
            continue;
          }

          changed = true;
          next.push({
            id,
            source: dep,
            target: node.id,
            type: "studio",
            data: { active, dead, settled },
          });
        }
      }

      if (!changed && next.length === previous.length) return previous;
      return next;
    });
  }, [nodes, deadSet, setRfEdges]);

  /* -- frame the graph the first time it exists -------------------------- */
  useEffect(() => {
    if (fittedRef.current || rfNodes.length === 0) return;
    fittedRef.current = true;
    const frame = requestAnimationFrame(() => {
      void fitView({ padding: FIT_PADDING, duration: 0 });
    });
    return () => cancelAnimationFrame(frame);
  }, [rfNodes.length, fitView]);

  /* -- re-fit whenever the shell is actually resized ---------------------- */
  // Not just on the `expanded` toggle. Embedded in the pipeline the canvas is
  // measured while its ancestors are still settling — a stage heading and an
  // outer border coming and going each change the box — and React Flow keeps
  // whatever zoom it computed against the wrong size. That is what left the
  // board sitting at 119% with its top row cut off instead of framed.
  useEffect(() => {
    const shell = shellRef.current;
    if (!shell || typeof ResizeObserver === "undefined") return;
    let frame = 0;
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() =>
        fitView({ padding: FIT_PADDING, duration: 0 })
      );
    });
    observer.observe(shell);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [fitView]);

  /* -- re-fit when the shell changes size -------------------------------- */
  useEffect(() => {
    if (!fittedRef.current) return;
    const timer = setTimeout(() => {
      void fitView({ padding: FIT_PADDING, duration: 220 });
    }, 90);
    return () => clearTimeout(timer);
  }, [expanded, fitView]);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setExpanded(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [expanded]);

  /* -- services handed to every node ------------------------------------- */
  const probedSupport = useRerunSupport(campaignId);
  const [forcedSupport, setForcedSupport] = useState<RerunSupport | null>(null);
  const rerunSupport = forcedSupport ?? probedSupport;

  const campaignRef = useRef(campaignId);
  campaignRef.current = campaignId;

  const onRerun = useCallback(async (nodeId: string, prompt: string) => {
    const id = campaignRef.current;
    if (!id) return false;
    try {
      await rerunStudioNode(id, nodeId, prompt ? { prompt } : {});
      toast.success("Đã gửi yêu cầu dựng lại", {
        description: `${nodeId} — kết quả sẽ hiện ngay trên node`,
      });
      return true;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Backend không phản hồi.";
      // A 404/405 means the endpoint is not deployed. Say so once, then stop
      // offering the control rather than inviting the same failure again.
      if (message.includes("chưa có endpoint")) setForcedSupport("unavailable");
      toast.error("Không dựng lại được node", { description: message });
      return false;
    }
  }, []);

  const onOpenMedia = useCallback((node: StudioNode) => setViewing(node), []);

  const services = useMemo<GraphCanvasServices>(
    () => ({
      rerunSupport,
      onRerun,
      onOpenMedia,
      canRerun: campaignId !== null,
    }),
    [rerunSupport, onRerun, onOpenMedia, campaignId]
  );

  /* -- interactions ------------------------------------------------------ */
  const onNodeDragStop = useCallback(
    (_event: unknown, node: GraphFlowNode) => {
      pinnedRef.current.set(node.id, { ...node.position });
    },
    []
  );

  const relayout = useCallback(() => {
    pinnedRef.current = new Map();
    const layout = layoutGraph(nodes);
    layoutRef.current = layout;
    setRfNodes((previous) =>
      previous.map((item) => ({
        ...item,
        position: layout.get(item.id) ?? item.position,
      }))
    );
    setTimeout(() => void fitView({ padding: FIT_PADDING, duration: 300 }), 40);
  }, [nodes, setRfNodes, fitView]);

  const counts = useMemo(() => {
    let running = 0;
    let finished = 0;
    for (const node of nodes) {
      if (node.state === "running" || node.state === "retry") running += 1;
      if (TERMINAL_STATES.has(node.state)) finished += 1;
    }
    return { running, finished, total: nodes.length };
  }, [nodes]);

  return (
    <div
      ref={shellRef}
      className={cn(
        "studio-panel flex min-w-0 flex-1 flex-col overflow-hidden h-full w-full min-h-[500px]",
        // Sixteen to twenty-five nodes will not be legible in a letterbox, so
        // the canvas takes most of the fold and the full-screen control takes
        // the rest — that is the one that makes the board properly readable.
        expanded ? "fixed inset-3 z-50 h-auto" : ""
      )}
    >
      {/* Workbench Header Bar (outside canvas) */}
      <header className="flex shrink-0 items-center justify-between border-b border-border bg-background px-3.5 py-2">
        <div className="flex items-center gap-2.5 min-w-0">
          {onToggleSidebar && (
            <button
              type="button"
              onClick={onToggleSidebar}
              title={sidebarOpen ? "Thu gọn Inspector" : "Mở Inspector"}
              className={cn(
                "flex items-center gap-1.5 h-7 px-2 rounded-none border text-[11.5px] font-medium transition-colors shrink-0",
                sidebarOpen
                  ? "border-border bg-foreground/[0.03] text-muted-foreground hover:text-foreground"
                  : "border-primary/50 bg-primary/10 text-primary hover:bg-primary/20"
              )}
            >
              {sidebarOpen ? <PanelLeftClose className="size-3.5" /> : <PanelLeft className="size-3.5" />}
              <span className="hidden sm:inline">Inspector</span>
            </button>
          )}

          <div className="flex items-baseline gap-2 min-w-0">
            <h2 className="font-display text-[13.5px] font-semibold tracking-tight text-foreground truncate">
              {savedMeta ? savedMeta.campaignName : "Sơ đồ dựng kit"}
            </h2>
            <span className="studio-nums font-mono text-[11.5px] text-muted-foreground shrink-0">
              {savedMeta
                ? `${savedMeta.images} ảnh · ${savedMeta.videos} video · ${(savedMeta.bytes / 1e6).toFixed(0)} MB`
                : `${counts.finished}/${counts.total} node`}
              {counts.running > 0 ? (
                <span className="text-primary ml-2 inline-flex items-center gap-1">
                  <span className="size-1.5 rounded-full bg-primary animate-pulse" />
                  {counts.running} đang chạy
                </span>
              ) : null}
            </span>
          </div>
        </div>

        {savedMeta ? (
          <div className="flex items-center gap-2 shrink-0">
            <a
              href={savedMeta.zipUrl}
              className="border-border/80 text-foreground hover:border-primary/50 hover:text-primary inline-flex h-7 items-center gap-1.5 rounded-none border px-2.5 text-[12px] font-medium transition-colors"
            >
              <Download aria-hidden className="size-3.5" />
              Tải .zip
            </a>
            <button
              type="button"
              onClick={savedMeta.onRebuild}
              className="border-border/80 text-muted-foreground hover:border-primary/50 hover:text-foreground inline-flex h-7 items-center gap-1.5 rounded-none border px-2.5 text-[12px] font-medium transition-colors"
            >
              <RefreshCw aria-hidden className="size-3.5" />
              Dựng lại
            </button>
          </div>
        ) : null}
      </header>

      <div className="studio-flow relative min-h-0 flex-1 h-full w-full">
        <GraphCanvasProvider value={services}>
          <ReactFlow<GraphFlowNode, GraphFlowEdge>
            style={{ width: "100%", height: "100%" }}
            nodes={rfNodes}
            edges={rfEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeDragStop={onNodeDragStop}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            minZoom={0.2}
            maxZoom={1.75}
            nodesConnectable={false}
            nodesDraggable
            elementsSelectable
            deleteKeyCode={null}
            multiSelectionKeyCode={null}
            zoomOnScroll
            zoomOnPinch
            panOnDrag
            selectionOnDrag={false}
            proOptions={{ hideAttribution: true }}
            fitView
            fitViewOptions={{ padding: FIT_PADDING }}
          >
            <Background color="#E5E7EB" variant={BackgroundVariant.Lines} />
            {showMiniMap && (
              <MiniMap
                className="studio-minimap"
                zoomable
                pannable
                position="bottom-right"
                style={{ width: 148, height: 104 }}
                maskColor="color-mix(in srgb, var(--background) 78%, transparent)"
                nodeColor={miniMapColor}
                nodeStrokeWidth={0}
              />
            )}

            {/* Top-Right: Vertical Floating Tool Dock */}
            <Panel position="top-right" className="m-3">
              <div className="flex flex-col items-center rounded-none border border-border bg-background/90 p-1 gap-1 backdrop-blur-md shadow-md">
                <ToolButton onClick={() => void zoomIn()} label="Phóng to">
                  <Plus aria-hidden className="size-[13px]" />
                </ToolButton>
                <ZoomReadout />
                <ToolButton onClick={() => void zoomOut()} label="Thu nhỏ">
                  <Minus aria-hidden className="size-[13px]" />
                </ToolButton>
                
                <span aria-hidden className="my-0.5 h-px w-4 bg-border" />
                
                <ToolButton
                  onClick={() => void fitView({ padding: FIT_PADDING, duration: 300 })}
                  label="Vừa khung hình"
                >
                  <Maximize aria-hidden className="size-[13px]" />
                </ToolButton>
                <ToolButton onClick={relayout} label="Sắp xếp lại">
                  <LayoutGrid aria-hidden className="size-[13px]" />
                </ToolButton>
                <ToolButton
                  onClick={() => setShowMiniMap((v) => !v)}
                  label={showMiniMap ? "Ẩn bản đồ thu nhỏ" : "Hiện bản đồ thu nhỏ"}
                >
                  <MapIcon aria-hidden className={cn("size-[13px]", showMiniMap && "text-primary")} />
                </ToolButton>
                
                <span aria-hidden className="my-0.5 h-px w-4 bg-border" />
                
                <ToolButton
                  onClick={() => setExpanded((value) => !value)}
                  label={expanded ? "Thu lại" : "Toàn màn hình"}
                >
                  {expanded ? (
                    <Minimize aria-hidden className="size-[13px]" />
                  ) : (
                    <Fullscreen aria-hidden className="size-[13px]" />
                  )}
                </ToolButton>
              </div>
            </Panel>

            {/* Bottom-Left: Subtle State Legend Chip */}
            <Panel position="bottom-left" className="m-3 hidden md:block">
              <div className="rounded-none border border-border bg-background/90 px-2.5 py-1 backdrop-blur-md shadow-sm">
                <StateLegend />
              </div>
            </Panel>
          </ReactFlow>
        </GraphCanvasProvider>
      </div>

      <MediaViewer node={viewing} onClose={() => setViewing(null)} />
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Chrome
 * ────────────────────────────────────────────────────────────────────────── */

function ToolButton({
  onClick,
  label,
  children,
}: {
  onClick: () => void;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      className={cn(
        "grid size-[24px] place-items-center rounded-none border border-border/70",
        "text-muted-foreground transition-colors",
        "hover:border-primary/45 hover:text-primary",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      )}
    >
      {children}
      <span className="sr-only">{label}</span>
    </button>
  );
}

/**
 * Isolated so the viewport's per-frame updates during a pan re-render three
 * characters of text and not a board of twenty-five nodes.
 */
function ZoomReadout() {
  const { zoom } = useViewport();
  return (
    <span className="studio-nums w-[38px] text-center font-mono text-[11px] text-muted-foreground">
      {Math.round(zoom * 100)}%
    </span>
  );
}

const LEGEND: { label: string; className: string }[] = [
  { label: "Chờ", className: "bg-muted-foreground/45" },
  { label: "Đang chạy", className: "bg-primary" },
  { label: "Xong", className: "bg-primary/60" },
  { label: "Dự phòng", className: "bg-gold" },
  { label: "Lỗi", className: "bg-destructive" },
];

function StateLegend() {
  return (
    <div className="flex items-center gap-x-3">
      {LEGEND.map((entry) => (
        <span key={entry.label} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className={cn("size-[6px] rounded-full", entry.className)}
          />
          <span className="text-[10.5px] text-muted-foreground">
            {entry.label}
          </span>
        </span>
      ))}
    </div>
  );
}

function miniMapColor(node: GraphFlowNode): string {
  if (node.data.dead) return "var(--muted)";
  switch (node.data.node.state) {
    case "running":
    case "done":
      return "var(--primary)";
    case "retry":
    case "degraded":
      return "var(--gold)";
    case "failed":
      return "var(--destructive)";
    default:
      return "var(--muted-foreground)";
  }
}
