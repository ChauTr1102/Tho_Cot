"use client";

/**
 * One box on the canvas.
 *
 * This component is the point of the whole screen. A studio run is six to
 * twelve minutes of nothing visible happening, and what makes that legible —
 * what makes the product's argument legible — is watching a slot cropped from
 * the brand's own photograph land in a tenth of a second while the box next to
 * it is still grinding out a video. So the node shows the picture, not a
 * reference to a picture in a gallery somewhere below the fold.
 *
 * Four things live here, in descending order of how much they matter:
 *
 *   1. The preview. An image node shows its image; a video node shows its
 *      first frame with a play control that opens the clip.
 *   2. The state. Colour, a label, a live halo while working, and an origin
 *      badge saying which of the three routes produced the asset.
 *   3. The prompt, editable, with a control to re-render just this node.
 *   4. The id, in mono, because it is what the run log and the backend logs
 *      call this node.
 *
 * The card's height is fixed by `nodeHeight(kind)` and it fills its box
 * exactly, so the preview well is the only element that flexes. A thumbnail
 * arriving mid-run changes nothing about the board's geometry.
 */

import {
  AlertTriangle,
  Ban,
  Maximize2,
  Play,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import {
  createContext,
  memo,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";

import { OriginBadge } from "@/components/studio/OriginBadge";
import { NODE_STATE_META, kindMeta } from "@/components/studio/state-styles";
import { isMediaKind, isPromptKind } from "@/components/studio/graph-layout";
import { formatElapsed, isVideoUrl, mediaUrl } from "@/lib/studio-events";
import { cn } from "@/lib/utils";
import type { RerunSupport, StudioNode } from "@/types/studio";

/* ──────────────────────────────────────────────────────────────────────────
 * Shared canvas services
 *
 * Handlers and the re-run capability flag reach nodes through context rather
 * than through node data. Node data has to stay a pure function of the
 * `StudioNode` so the canvas can hand React Flow the *same object* for every
 * node an event did not touch — which is what keeps a 25-node board from
 * re-rendering wholesale every few seconds.
 * ────────────────────────────────────────────────────────────────────────── */

export interface GraphCanvasServices {
  rerunSupport: RerunSupport;
  /**
   * Ask the backend to re-render one node. Reports the outcome rather than
   * throwing: the canvas has already raised the toast, and the node only needs
   * to know whether to keep treating its box as dirty.
   */
  onRerun: (nodeId: string, prompt: string) => Promise<boolean>;
  /** Open the full-size viewer for a node's finished media. */
  onOpenMedia: (node: StudioNode) => void;
  /** False before a run exists — every action is inert until then. */
  canRerun: boolean;
}

const NOOP_SERVICES: GraphCanvasServices = {
  rerunSupport: "unknown",
  onRerun: async () => false,
  onOpenMedia: () => undefined,
  canRerun: false,
};

const GraphCanvasContext = createContext<GraphCanvasServices>(NOOP_SERVICES);

export const GraphCanvasProvider = GraphCanvasContext.Provider;

export function useGraphCanvas(): GraphCanvasServices {
  return useContext(GraphCanvasContext);
}

/* ──────────────────────────────────────────────────────────────────────────
 * Node data contract
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * Deliberately a `type` and not an `interface`: React Flow constrains node
 * data to `Record<string, unknown>`, which a type alias satisfies structurally
 * and an interface does not.
 */
export type GraphNodeData = {
  node: StudioNode;
  /** Downstream of a failure — greyed out as a casualty, not a cause. */
  dead: boolean;
};

export type GraphFlowNode = Node<GraphNodeData, "studio">;

/* ──────────────────────────────────────────────────────────────────────────
 * The card
 * ────────────────────────────────────────────────────────────────────────── */

function GraphNodeCard({ data, selected }: NodeProps<GraphFlowNode>) {
  const { node, dead } = data;
  const services = useGraphCanvas();

  const state = NODE_STATE_META[node.state] ?? NODE_STATE_META.pending;
  const kind = kindMeta(node.kind);
  const KindIcon = kind.icon;

  const url = mediaUrl(node.payload.url ?? node.payload.path);
  const showsMedia = isMediaKind(node.kind);
  const showsPrompt = isPromptKind(node.kind);

  return (
    <article
      data-state={dead ? "dead" : node.state}
      data-selected={selected ? "true" : undefined}
      className={cn(
        "studio-node flex h-full w-full flex-col gap-[7px] rounded-[10px] border p-[9px]",
        dead ? "studio-node-dead border-border/45" : state.chip
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={false}
        className="studio-node-port"
      />

      <header className="flex h-[18px] shrink-0 items-center gap-[6px]">
        <span
          aria-hidden
          className={cn(
            "relative size-[6px] shrink-0 rounded-full",
            dead ? "bg-muted-foreground/50" : cn(state.dot, state.text),
            !dead && state.live && "studio-live-dot"
          )}
        />
        <KindIcon
          aria-hidden
          className="size-[12px] shrink-0 text-muted-foreground"
        />
        <span
          title={node.id}
          className="min-w-0 flex-1 truncate font-mono text-[11px] leading-none text-foreground/90"
        >
          {node.id}
        </span>
        {node.elapsed_sec > 0 ? (
          <span className="studio-nums shrink-0 font-mono text-[10.5px] leading-none text-muted-foreground">
            {formatElapsed(node.elapsed_sec)}
          </span>
        ) : null}
      </header>

      {showsMedia ? (
        <MediaWell node={node} url={url} dead={dead} onOpen={services.onOpenMedia} />
      ) : null}

      <MetaRow node={node} dead={dead} />

      {showsPrompt ? <PromptEditor node={node} dead={dead} /> : null}

      <Handle
        type="source"
        position={Position.Right}
        isConnectable={false}
        className="studio-node-port"
      />
    </article>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Preview well
 * ────────────────────────────────────────────────────────────────────────── */

function MediaWell({
  node,
  url,
  dead,
  onOpen,
}: {
  node: StudioNode;
  url: string | null;
  dead: boolean;
  onOpen: (node: StudioNode) => void;
}) {
  const [loaded, setLoaded] = useState(false);
  const kind = kindMeta(node.kind);
  const KindIcon = kind.icon;

  // A re-run replaces the picture at the same node; fade the new one in too.
  useEffect(() => setLoaded(false), [url]);

  const open = useCallback(() => onOpen(node), [onOpen, node]);

  if (url) {
    const video = isVideoUrl(url);
    return (
      <div
        onDoubleClick={open}
        className="studio-media relative min-h-0 flex-1 overflow-hidden rounded-[7px]"
      >
        {video ? (
          <video
            // A media fragment makes the browser paint a real frame instead of
            // a black rectangle: there is no separate poster in the contract.
            // One second in, not zero — these clips open on a fade from black.
            src={`${url}#t=1`}
            preload="metadata"
            muted
            playsInline
            onLoadedData={() => setLoaded(true)}
            className={cn(
              "size-full object-contain transition-opacity duration-300",
              loaded ? "opacity-100" : "opacity-0"
            )}
          />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element -- backend-served
          // media of unknown intrinsic size on a separate origin; next/image
          // would need a remotePatterns entry in a config another agent owns.
          <img
            src={url}
            alt={`Kết quả của node ${node.id}`}
            loading="lazy"
            decoding="async"
            onLoad={() => setLoaded(true)}
            onError={() => setLoaded(true)}
            className={cn(
              "size-full object-contain transition-opacity duration-300",
              loaded ? "opacity-100" : "opacity-0"
            )}
          />
        )}

        <button
          type="button"
          onClick={open}
          title={video ? "Phát video" : "Xem ảnh đầy đủ"}
          className={cn(
            "nodrag studio-media-open absolute grid place-items-center rounded-full",
            "border border-primary/45 bg-background/80 text-primary backdrop-blur-sm",
            "transition-colors hover:bg-primary hover:text-primary-foreground",
            "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
            video
              ? "top-1/2 left-1/2 size-[34px] -translate-x-1/2 -translate-y-1/2"
              : "right-[6px] bottom-[6px] size-[22px]"
          )}
        >
          {video ? (
            <Play aria-hidden className="size-[15px] translate-x-px" fill="currentColor" />
          ) : (
            <Maximize2 aria-hidden className="size-[11px]" />
          )}
          <span className="sr-only">
            {video ? "Phát video" : "Xem ảnh đầy đủ"}
          </span>
        </button>
      </div>
    );
  }

  /* No file yet. The well still holds its space — the layout is fixed — so it
     says which of the three reasons it is empty for. */
  if (node.state === "running" || node.state === "retry") {
    return (
      <div className="studio-media studio-media-working relative grid min-h-0 flex-1 place-items-center overflow-hidden rounded-[7px]">
        <span className="relative z-10 font-mono text-[10.5px] tracking-[0.14em] text-primary/80 uppercase">
          Đang dựng
        </span>
      </div>
    );
  }

  if (dead || node.state === "failed") {
    return (
      <div className="studio-media grid min-h-0 flex-1 place-items-center rounded-[7px]">
        <Ban aria-hidden className="size-[18px] text-muted-foreground/45" />
      </div>
    );
  }

  if (node.state === "pending") {
    return (
      <div className="studio-media studio-media-pending grid min-h-0 flex-1 place-items-center rounded-[7px]">
        <KindIcon aria-hidden className="size-[18px] text-muted-foreground/35" />
      </div>
    );
  }

  // Finished, but the event carried no url. Say so rather than show a hole.
  return (
    <div className="studio-media grid min-h-0 flex-1 place-items-center gap-1 rounded-[7px] px-2 text-center">
      <KindIcon aria-hidden className="size-[16px] text-muted-foreground/45" />
      <span className="text-[10.5px] leading-tight text-muted-foreground/70">
        Không kèm bản xem trước
      </span>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Meta row — route, verdict, and whatever went wrong
 * ────────────────────────────────────────────────────────────────────────── */

function MetaRow({ node, dead }: { node: StudioNode; dead: boolean }) {
  const state = NODE_STATE_META[node.state] ?? NODE_STATE_META.pending;
  const origin = node.payload.origin;
  const qa = typeof node.payload.qa === "string" ? node.payload.qa : null;

  const trouble = dead
    ? `Dừng theo nhánh lỗi${
        node.payload.failed_dep ? ` · ${node.payload.failed_dep}` : ""
      }`
    : node.state === "failed"
      ? node.payload.error || node.payload.message || "Node lỗi"
      : node.state === "degraded"
        ? node.payload.note || node.payload.message || "Dùng bản dự phòng"
        : null;

  return (
    <div className="flex h-[19px] shrink-0 items-center gap-[6px]">
      {origin && !dead ? (
        <OriginBadge origin={origin} size="xs" />
      ) : (
        <span
          className={cn(
            "shrink-0 text-[10.5px] font-medium",
            dead ? "text-muted-foreground/70" : state.text
          )}
        >
          {dead ? "Bỏ qua" : state.label}
          {node.state === "retry" && node.payload.attempt
            ? ` ${node.payload.attempt}`
            : ""}
        </span>
      )}

      {trouble ? (
        <span
          title={trouble}
          className={cn(
            "min-w-0 flex-1 truncate text-[10.5px]",
            dead ? "text-muted-foreground/60" : state.text
          )}
        >
          {trouble}
        </span>
      ) : (
        <span className="min-w-0 flex-1 truncate text-[10.5px] text-muted-foreground/75">
          {node.payload.slot ?? kindMeta(node.kind).label}
        </span>
      )}

      {qa && !dead ? <QaChip verdict={qa} notes={node.payload.qa_notes} /> : null}
    </div>
  );
}

function QaChip({ verdict, notes }: { verdict: string; notes?: string[] }) {
  const passed = verdict.toUpperCase() === "PASS";
  const Icon = passed ? ShieldCheck : ShieldAlert;
  const detail =
    !passed && notes && notes.length > 0
      ? `Soi lỗi: ${notes.slice(0, 3).join(" · ")}`
      : passed
        ? "Soi lỗi chính tả và nhận diện: đạt"
        : "Soi lỗi: cần xem lại";

  return (
    <span
      title={detail}
      className={cn(
        "inline-flex shrink-0 items-center gap-[3px] rounded-[4px] border px-[4px] py-px",
        "text-[9.5px] font-semibold tracking-[0.06em] uppercase",
        passed
          ? "border-primary/35 bg-primary/10 text-primary"
          : "border-gold/45 bg-gold/12 text-gold"
      )}
    >
      <Icon aria-hidden className="size-[9px]" strokeWidth={2.4} />
      {passed ? "QA" : "QA?"}
    </span>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Prompt editor
 * ────────────────────────────────────────────────────────────────────────── */

function PromptEditor({ node, dead }: { node: StudioNode; dead: boolean }) {
  const { rerunSupport, onRerun, canRerun } = useGraphCanvas();

  const incoming = typeof node.payload.prompt === "string" ? node.payload.prompt : "";
  const [draft, setDraft] = useState(incoming);
  const [pending, setPending] = useState(false);
  const editedRef = useRef(false);

  // Adopt a prompt the backend sends later, but never overwrite typing in
  // progress: a node emits several events and one of them must not eat an edit.
  useEffect(() => {
    if (!editedRef.current) setDraft(incoming);
  }, [incoming]);

  const busy = node.state === "running" || node.state === "retry";
  const neverRan = node.state === "pending";

  const blocked =
    !canRerun
      ? "Chưa có lượt chạy nào để dựng lại"
      : rerunSupport === "unavailable"
        ? "Backend chưa có endpoint POST /api/studio/{campaign}/node/{node}/rerun"
        : dead
          ? "Nhánh này đã dừng vì một node phía trước lỗi"
          : busy
            ? "Node đang chạy"
            : neverRan
              ? "Node chưa chạy lần nào"
              : null;

  const submit = useCallback(async () => {
    if (blocked || pending) return;
    setPending(true);
    const accepted = await onRerun(node.id, draft.trim());
    // Only hand the box back to the backend once the request landed. If it
    // failed, the edit stays the user's and a later event will not clobber it.
    if (accepted) editedRef.current = false;
    setPending(false);
  }, [blocked, draft, node.id, onRerun, pending]);

  return (
    <div className="flex shrink-0 flex-col gap-[5px]">
      <textarea
        rows={2}
        value={draft}
        disabled={dead}
        spellCheck={false}
        onChange={(event) => {
          editedRef.current = true;
          setDraft(event.target.value);
        }}
        // React Flow reads these: `nodrag` keeps a text selection from dragging
        // the node, `nowheel` keeps scrolling the box from zooming the canvas.
        className="nodrag nowheel studio-prompt"
        placeholder={incoming ? "Prompt của node" : "Nhập prompt để dựng lại"}
        aria-label={`Prompt của node ${node.id}`}
      />

      <button
        type="button"
        onClick={submit}
        disabled={blocked !== null || pending}
        title={blocked ?? "Dựng lại riêng ô này với prompt ở trên"}
        // Sentence case and dimmed while dead: there is one of these on every
        // image node, and twenty shouting buttons would out-weigh the twenty
        // pictures they sit under.
        className={cn(
          "nodrag inline-flex h-[20px] shrink-0 items-center justify-center gap-[5px] rounded-[5px] border",
          "text-[10px] font-medium transition-colors",
          "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
          blocked !== null || pending
            ? "cursor-not-allowed border-border/45 text-muted-foreground/45"
            : "border-primary/45 text-primary hover:bg-primary hover:text-primary-foreground"
        )}
      >
        {blocked !== null && rerunSupport === "unavailable" ? (
          <AlertTriangle aria-hidden className="size-[10px]" />
        ) : (
          <RefreshCw
            aria-hidden
            className={cn("size-[10px]", pending && "studio-spin")}
          />
        )}
        {pending ? "Đang gửi…" : "Dựng lại"}
      </button>
    </div>
  );
}

/**
 * Memoised on `data` identity. The canvas reuses the exact same data object for
 * every node an event did not touch, so an event about one node re-renders
 * that node and nothing else.
 */
export const GraphNode = memo(GraphNodeCard);
