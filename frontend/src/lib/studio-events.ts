"use client";

/**
 * Typed client for the Asset Studio's server-sent event stream.
 *
 * A studio run takes 6–12 minutes, so the stream — not a polling loop and not a
 * spinner — is what the screen is built around. This module owns the whole
 * lifecycle: opening `GET /api/studio/{id}/events`, folding `node` events into
 * a node map, keeping an ordered activity ledger, fetching the finished pack on
 * `done`, and surfacing a connection failure instead of hiding it.
 *
 * Failure policy, deliberate: EventSource reconnects forever by default, which
 * would leave a dead run looking alive. We close on the first transport error,
 * retry exactly once, and then settle into `disconnected` with an error string
 * the UI renders. The backend may not exist yet; this file must degrade, never
 * throw.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type {
  AssetPack,
  GraphNodeSpec,
  NodeState,
  RerunSupport,
  StudioActivityEntry,
  StudioEvent,
  StudioNode,
  StudioNodeRerunRequest,
  StudioRunRequest,
  StudioStreamStatus,
} from "@/types/studio";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/**
 * Origin the backend serves generated media from.
 *
 * `main.py` mounts `StaticFiles` at `/media`, a sibling of `/api` rather than
 * a child of it, and every path leaving the studio endpoints is rewritten to
 * `/media/...`. Those URLs are root-relative, so the browser would resolve
 * them against the Next.js origin unless they are re-based here.
 */
const MEDIA_BASE_URL = API_BASE_URL.replace(/\/api\/?$/, "");

/** One retry, then the failure is the user's to see. */
const RECONNECT_DELAY_MS = 1500;

/** The ledger is a recent-activity view, not a log; older rows are dropped. */
const ACTIVITY_LIMIT = 80;

/** States that mean the node will not run again. */
const TERMINAL_STATES: ReadonlySet<NodeState> = new Set<NodeState>([
  "done",
  "degraded",
  "failed",
]);

/**
 * `pipeline.run_studio` reports run-level milestones through the same channel
 * as real nodes, under dunder ids: `__graph__` carries the DAG (the API layer
 * translates that one into the `graph` event) and `__pack__` announces the
 * finished bundle. `__pack__` still arrives as a `node` event, so without this
 * it lands on the canvas as a thirteenth box with no dependencies, no output
 * and no meaning — sitting in its own column at the far left, because a node
 * with no `deps` sorts to layer zero.
 *
 * They are run metadata, not steps. Dropped from the node map, the progress
 * counts and the activity ledger alike.
 */
function isSyntheticNode(nodeId: string): boolean {
  return nodeId.startsWith("__") && nodeId.endsWith("__");
}

export interface StudioProgress {
  total: number;
  /** Terminal nodes: done + degraded + failed. */
  finished: number;
  done: number;
  running: number;
  failed: number;
  /** 0–1. Zero when the graph has not arrived yet. */
  ratio: number;
}

export interface StudioStream {
  /** Graph order: the order the `graph` event listed them in. */
  nodes: StudioNode[];
  nodeById: Map<string, StudioNode>;
  assets: AssetPack | null;
  status: StudioStreamStatus;
  /** Non-null once something has gone wrong; UI copy, in Vietnamese. */
  error: string | null;
  /** Newest first. */
  activity: StudioActivityEntry[];
  progress: StudioProgress;
  /** Manual reconnect, wired to the "Thử lại" action on the failure panel. */
  reconnect: () => void;
}

const EMPTY_PROGRESS: StudioProgress = {
  total: 0,
  finished: 0,
  done: 0,
  running: 0,
  failed: 0,
  ratio: 0,
};

/**
 * Subscribe to a campaign's live graph.
 *
 * Pass `null` to stay idle — the hook opens no connection until a run exists,
 * which is what the screen does before the Run button is pressed.
 */
export function useStudioStream(campaignId: string | null): StudioStream {
  const [nodeById, setNodeById] = useState<Map<string, StudioNode>>(
    () => new Map()
  );
  const [activity, setActivity] = useState<StudioActivityEntry[]>([]);
  const [assets, setAssets] = useState<AssetPack | null>(null);
  const [status, setStatus] = useState<StudioStreamStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  /** Bumping this re-runs the effect, which is what "Thử lại" does. */
  const [connectionAttempt, setConnectionAttempt] = useState(0);

  const seqRef = useRef(0);

  const reconnect = useCallback(() => {
    setError(null);
    setConnectionAttempt((n) => n + 1);
  }, []);

  useEffect(() => {
    if (!campaignId) {
      setNodeById(new Map());
      setActivity([]);
      setAssets(null);
      setError(null);
      setStatus("idle");
      return;
    }

    let disposed = false;
    let retried = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let source: EventSource | null = null;

    const eventsUrl = `${API_BASE_URL}/studio/${encodeURIComponent(
      campaignId
    )}/events`;

    /** Pull the finished bundle once the run reports `done`. */
    const loadPack = async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/studio/${encodeURIComponent(campaignId)}/pack`
        );
        if (!res.ok) return;
        const body = await res.json();
        // `/pack` uses the StandardResponse envelope; tolerate a bare body too.
        const pack = (body?.data ?? body) as AssetPack | null;
        if (!disposed && pack && Array.isArray(pack.images)) setAssets(pack);
      } catch {
        // A missing pack is not a run failure — the graph already told the
        // story. Stay quiet rather than contradict a successful run.
      }
    };

    const seedGraph = (specs: GraphNodeSpec[]) => {
      setNodeById((previous) => {
        const next = new Map<string, StudioNode>();
        for (const spec of specs) {
          if (isSyntheticNode(spec.id)) continue;
          const existing = previous.get(spec.id);
          next.set(spec.id, {
            id: spec.id,
            kind: spec.kind,
            deps: spec.deps ?? [],
            state: existing?.state ?? "pending",
            elapsed_sec: existing?.elapsed_sec ?? 0,
            payload: existing?.payload ?? {},
            updated_at: existing?.updated_at ?? Date.now(),
          });
        }
        // Keep nodes that arrived before their graph entry did.
        for (const [id, node] of previous) if (!next.has(id)) next.set(id, node);
        return next;
      });
    };

    const applyEvent = (event: StudioEvent) => {
      switch (event.event) {
        case "graph":
          seedGraph(event.nodes ?? []);
          return;

        case "node": {
          if (isSyntheticNode(event.node_id)) return;
          const at = Date.now();
          setNodeById((previous) => {
            const next = new Map(previous);
            const existing = next.get(event.node_id);
            next.set(event.node_id, {
              id: event.node_id,
              kind: event.kind ?? existing?.kind ?? "image",
              deps: existing?.deps ?? [],
              state: event.state,
              elapsed_sec: event.elapsed_sec ?? existing?.elapsed_sec ?? 0,
              payload: { ...existing?.payload, ...(event.payload ?? {}) },
              updated_at: at,
            });
            return next;
          });
          // Read into a local *before* queueing the update. React runs the
          // updater at render time, not at call time, so several events
          // arriving in one batch would all read the same, final `seqRef` —
          // and two transitions of the same node in one batch (a `running`
          // and its `done`) would collide on the key. That is exactly what
          // the backlog replay delivers on connect.
          seqRef.current += 1;
          const seq = seqRef.current;
          setActivity((previous) =>
            [
              {
                key: `${event.node_id}:${seq}`,
                node_id: event.node_id,
                kind: event.kind,
                state: event.state,
                elapsed_sec: event.elapsed_sec ?? 0,
                origin: event.payload?.origin,
                message: event.payload?.message,
                at,
              },
              ...previous,
            ].slice(0, ACTIVITY_LIMIT)
          );
          return;
        }

        case "done":
          setStatus("done");
          source?.close();
          void loadPack();
          return;

        case "error":
          // A node-level failure. The stream stays open: other branches of the
          // graph are still running and the user needs to watch them finish.
          setError(event.message || "Một node trong graph đã lỗi.");
          return;
      }
    };

    const handlePayload = (raw: unknown) => {
      if (typeof raw !== "string" || raw.length === 0) return;
      let parsed: StudioEvent;
      try {
        parsed = JSON.parse(raw) as StudioEvent;
      } catch {
        return; // A malformed frame must not take the screen down.
      }
      if (!disposed && parsed && typeof parsed.event === "string") {
        applyEvent(parsed);
      }
    };

    const connect = () => {
      setStatus((current) => (current === "streaming" ? current : "connecting"));

      try {
        source = new EventSource(eventsUrl);
      } catch {
        setStatus("disconnected");
        setError("Trình duyệt không mở được kết nối tới luồng sự kiện.");
        return;
      }

      source.onopen = () => {
        if (disposed) return;
        setStatus("streaming");
        setError(null);
      };

      // The backend may or may not name its frames. Cover both: `onmessage`
      // catches unnamed `data:` frames, the listeners catch `event: node` etc.
      source.onmessage = (message) => handlePayload(message.data);
      for (const name of ["graph", "node", "done"] as const) {
        source.addEventListener(name, (message) =>
          handlePayload((message as MessageEvent).data)
        );
      }

      // `error` is overloaded: EventSource fires it for transport failures, and
      // the contract also defines a server-sent `error` event. A transport
      // error carries no `data`, which is how the two are told apart.
      source.addEventListener("error", (message) => {
        const data = (message as MessageEvent).data;
        if (typeof data === "string" && data.length > 0) {
          handlePayload(data);
          return;
        }
        source?.close();
        if (disposed) return;

        if (!retried) {
          retried = true;
          setStatus("reconnecting");
          timer = setTimeout(connect, RECONNECT_DELAY_MS);
          return;
        }
        setStatus("disconnected");
        setError(
          "Mất kết nối tới luồng sự kiện của studio. Kiểm tra backend rồi thử lại."
        );
      });
    };

    connect();

    return () => {
      disposed = true;
      if (timer) clearTimeout(timer);
      source?.close();
    };
  }, [campaignId, connectionAttempt]);

  const nodes = useMemo(() => Array.from(nodeById.values()), [nodeById]);

  const progress = useMemo<StudioProgress>(() => {
    if (nodes.length === 0) return EMPTY_PROGRESS;
    let finished = 0;
    let done = 0;
    let running = 0;
    let failed = 0;
    for (const node of nodes) {
      if (TERMINAL_STATES.has(node.state)) finished += 1;
      if (node.state === "done") done += 1;
      if (node.state === "running") running += 1;
      if (node.state === "failed") failed += 1;
    }
    return {
      total: nodes.length,
      finished,
      done,
      running,
      failed,
      ratio: finished / nodes.length,
    };
  }, [nodes]);

  return {
    nodes,
    nodeById,
    assets,
    status,
    error,
    activity,
    progress,
    reconnect,
  };
}

/**
 * Start a run. Returns the campaign id the SSE stream is keyed on.
 *
 * Throws on any non-2xx or malformed response so the caller can render a real
 * failure state; the screen must never pretend a run started when it did not.
 */
export async function startStudioRun(
  request: StudioRunRequest
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/studio/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`POST /studio/run trả về HTTP ${res.status}`);
  }

  const body = await res.json().catch(() => null);
  const campaignId: unknown = body?.data?.campaign_id ?? body?.campaign_id;
  if (typeof campaignId !== "string" || campaignId.length === 0) {
    throw new Error("Phản hồi từ /studio/run thiếu campaign_id");
  }
  return campaignId;
}

/* ────────────────────────────────────────────────────────────────────────────
 * Media
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * Resolve a node payload's media reference into something an `<img>` can load.
 *
 * The backend rewrites generated files to `/media/...`, but leaves any path
 * *outside* its data directory untouched — a source photograph read straight
 * from `sample_data/` arrives as an absolute filesystem path. Those are not
 * fetchable from a browser, so they resolve to `null` and the node renders its
 * "no preview" state instead of a broken image icon.
 */
export function mediaUrl(value?: string | null): string | null {
  if (typeof value !== "string" || value.length === 0) return null;
  if (/^(?:https?:|data:|blob:)/i.test(value)) return value;
  if (value.startsWith("/media/")) return `${MEDIA_BASE_URL}${value}`;
  return null;
}

/** Extensions the canvas plays as video rather than showing as a still. */
const VIDEO_EXTENSIONS = /\.(?:mp4|webm|mov|m4v|ogv)(?:[?#]|$)/i;

export function isVideoUrl(url: string): boolean {
  return VIDEO_EXTENSIONS.test(url);
}

/* ────────────────────────────────────────────────────────────────────────────
 * Single-node re-run
 * ────────────────────────────────────────────────────────────────────────── */

function rerunUrl(campaignId: string, nodeId: string): string {
  return `${API_BASE_URL}/studio/${encodeURIComponent(
    campaignId
  )}/node/${encodeURIComponent(nodeId)}/rerun`;
}

/**
 * Re-render a single node, optionally against an edited prompt.
 *
 * Resolves as soon as the backend acknowledges. The *result* is not returned
 * here — it arrives on the campaign's open SSE stream as ordinary `node`
 * events, which is what keeps the canvas a single source of truth rather than
 * two half-synchronised ones.
 *
 * Throws on any non-2xx so the caller can surface a real failure. A 404 or 405
 * is treated specially: it means the endpoint is not deployed, so the local
 * support flag is downgraded and every re-run control disables itself.
 */
export async function rerunStudioNode(
  campaignId: string,
  nodeId: string,
  request: StudioNodeRerunRequest = {}
): Promise<void> {
  const res = await fetch(rerunUrl(campaignId, nodeId), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (res.status === 404 || res.status === 405) {
    cachedSupport = "unavailable";
    throw new Error("Backend chưa có endpoint chạy lại từng node.");
  }
  if (!res.ok) {
    throw new Error(`POST .../node/${nodeId}/rerun trả về HTTP ${res.status}`);
  }
}

/**
 * Module-level because the answer is a property of the deployment, not of a
 * campaign: once one probe has answered, every later run knows.
 */
let cachedSupport: RerunSupport = "unknown";
let inFlightProbe: Promise<RerunSupport> | null = null;

/**
 * Ask the backend whether the re-run endpoint exists, without side effects.
 *
 * A GET against a POST-only route answers 405 (the route is registered); a GET
 * against a route nobody declared answers 404. A preflight cannot be used for
 * this — FastAPI's CORS middleware answers every `OPTIONS` with 200 before the
 * router ever sees the path — and a POST cannot be used either, because a
 * probe must not start work. So: GET, and read the status code.
 *
 * A transport error leaves the answer `unknown` rather than `unavailable`: the
 * backend being briefly unreachable is not evidence that a feature is missing,
 * and leaving the control enabled means a click reports the real error.
 */
async function probeRerunSupport(campaignId: string): Promise<RerunSupport> {
  if (cachedSupport !== "unknown") return cachedSupport;
  inFlightProbe ??= (async () => {
    try {
      const res = await fetch(rerunUrl(campaignId, "__probe__"), {
        method: "GET",
      });
      cachedSupport = res.status === 404 ? "unavailable" : "available";
    } catch {
      inFlightProbe = null; // let a later run try again
      return "unknown";
    }
    return cachedSupport;
  })();
  return inFlightProbe;
}

/**
 * Whether the re-run control should be live, resolved once per session.
 *
 * Returns `unknown` before the probe answers, which the UI treats as "enabled,
 * optimistically" — the first click reports the truth either way.
 */
export function useRerunSupport(campaignId: string | null): RerunSupport {
  const [support, setSupport] = useState<RerunSupport>(cachedSupport);

  useEffect(() => {
    if (!campaignId || cachedSupport !== "unknown") {
      setSupport(cachedSupport);
      return;
    }
    let disposed = false;
    void probeRerunSupport(campaignId).then((answer) => {
      if (!disposed) setSupport(answer);
    });
    return () => {
      disposed = true;
    };
  }, [campaignId]);

  return support;
}

/**
 * Wall clock for the run, ticking once a second while it is in flight.
 *
 * Node timings come from the backend; this is the number the user actually
 * watches, so it is measured on the client from the moment Run was pressed.
 */
export function useRunClock(
  startedAt: number | null,
  stoppedAt: number | null
): number {
  const [now, setNow] = useState<number>(() => Date.now());

  useEffect(() => {
    if (startedAt === null || stoppedAt !== null) return;
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [startedAt, stoppedAt]);

  if (startedAt === null) return 0;
  return Math.max(0, Math.round(((stoppedAt ?? now) - startedAt) / 1000));
}

/** `MM:SS` for run clocks, `M:SS` never — tabular numerals need fixed width. */
export function formatClock(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

/** Compact per-node timing: `42s` under a minute, `4m12s` above it. */
export function formatElapsed(totalSeconds: number): string {
  const safe = Math.max(0, Math.round(totalSeconds));
  if (safe < 60) return `${safe}s`;
  return `${Math.floor(safe / 60)}m${String(safe % 60).padStart(2, "0")}s`;
}
