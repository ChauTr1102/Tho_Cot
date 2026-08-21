/**
 * TypeScript mirrors of the Asset Studio contracts.
 *
 * Two Python sources are mirrored here and must stay in sync with them:
 *
 *  1. The SSE event contract emitted by `GET /api/studio/{campaign_id}/events`
 *     (backend/app/api/v1/endpoints/studio.py, Task 11).
 *  2. The asset models in `backend/app/schemas/campaign.py` as extended by
 *     Task 2 (`Platform`, `AssetOrigin`, `ShotAsset`, `VideoCutdown` and the
 *     optional fields added to `ImageAsset` / `VideoAsset`).
 *
 * Backend extensions are additive by contract, so every field the studio adds
 * is optional here too. Unknown enum members are tolerated rather than
 * crashing the UI: the frontend ships before the backend does, and a screen a
 * judge is watching must never blank out because a node reported a state this
 * build has not heard of.
 */

/* ────────────────────────────────────────────────────────────────────────────
 * Graph vocabulary
 * ────────────────────────────────────────────────────────────────────────── */

/** `graph.NodeState`, lowercased on the wire. */
export type NodeState =
  | "pending"
  | "running"
  | "done"
  | "retry"
  | "degraded"
  | "failed";

export const NODE_STATES: readonly NodeState[] = [
  "pending",
  "running",
  "done",
  "retry",
  "degraded",
  "failed",
] as const;

/**
 * `Node.kind`. The set is open — `pipeline.build_nodes` names its own kinds and
 * may add more — so consumers must handle an unrecognised kind gracefully.
 */
export type NodeKind =
  | "plan"
  | "inventory"
  | "worksheet"
  | "image"
  | "keyframe"
  | "video"
  | "inspect"
  | "compose"
  | "cutdown"
  | (string & {});

/** `campaign.AssetOrigin` — how a single asset was produced. */
export type AssetOrigin = "reuse" | "remix" | "generate";

/** `campaign.Platform` — the marketplace a kit is built for. */
export type Platform = "tiktok_shop" | "shopee";

/** `campaign.ImageKind` — values are the Python enum's `.value`, not its name. */
export type ImageKind =
  | "product_hero_image"
  | "sku_detail_image"
  | "campaign_collection_image"
  | "marketplace_thumbnail"
  | "promotion_banner"
  | (string & {});

/* ────────────────────────────────────────────────────────────────────────────
 * SSE events
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * The free-form `payload` attached to a node event. The keys listed are the
 * ones Task 11 documents; the index signature keeps forward compatibility with
 * fields a later task adds.
 */
export interface NodePayload {
  /** Media URL for a finished image or video node, served by the backend. */
  url?: string;
  /** Which of the three routes produced this asset. */
  origin?: AssetOrigin;
  /** Visual QA verdict, e.g. "PASS" / "FAIL". */
  qa?: string;
  /** Kit slot id, e.g. "shopee_main". */
  slot?: string;
  platform?: Platform;
  /** Retry counter, present while a node is in the `retry` state. */
  attempt?: number;
  /** Human-readable detail, typically on `failed` or `degraded`. */
  message?: string;
  [key: string]: unknown;
}

/** One entry of the `graph` event's `nodes` array: the DAG's shape. */
export interface GraphNodeSpec {
  id: string;
  kind: NodeKind;
  deps: string[];
}

/** Sent once, before any node starts, so the canvas can lay out up front. */
export interface StudioGraphEvent {
  event: "graph";
  nodes: GraphNodeSpec[];
}

/** Sent on every node state transition. */
export interface StudioNodeEvent {
  event: "node";
  node_id: string;
  kind: NodeKind;
  state: NodeState;
  elapsed_sec: number;
  payload?: NodePayload;
}

/** Sent once when the whole run finishes; the stream closes after it. */
export interface StudioDoneEvent {
  event: "done";
  campaign_id: string;
}

/** A run-level or node-level failure. Does not necessarily end the stream. */
export interface StudioErrorEvent {
  event: "error";
  node_id?: string;
  message: string;
}

export type StudioEvent =
  | StudioGraphEvent
  | StudioNodeEvent
  | StudioDoneEvent
  | StudioErrorEvent;

/* ────────────────────────────────────────────────────────────────────────────
 * Client-side node model
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * A graph node as the client holds it: the shape from the `graph` event, folded
 * together with the latest `node` event for that id.
 */
export interface StudioNode extends GraphNodeSpec {
  state: NodeState;
  /** Seconds the node itself has been running, as reported by the backend. */
  elapsed_sec: number;
  payload: NodePayload;
  /** Client clock (ms epoch) of the last transition — used to order activity. */
  updated_at: number;
}

/** One line of the activity ledger: a transition, kept in arrival order. */
export interface StudioActivityEntry {
  /** Stable key: node id + arrival time, since a node transitions repeatedly. */
  key: string;
  node_id: string;
  kind: NodeKind;
  state: NodeState;
  elapsed_sec: number;
  origin?: AssetOrigin;
  message?: string;
  at: number;
}

/** Lifecycle of the EventSource connection, surfaced to the UI verbatim. */
export type StudioStreamStatus =
  | "idle"
  | "connecting"
  | "reconnecting"
  | "streaming"
  | "done"
  | "disconnected";

/* ────────────────────────────────────────────────────────────────────────────
 * Assets — `GET /api/studio/{campaign_id}/pack`
 * ────────────────────────────────────────────────────────────────────────── */

export interface ImageAsset {
  kind: ImageKind;
  url: string;
  width: number;
  height: number;
  model?: string;

  /* Studio extensions (Task 2). All optional; older bundles omit them. */
  platform?: Platform | null;
  slot?: string | null;
  origin?: AssetOrigin | null;
  local_path?: string | null;
  prompt?: string | null;
  text_rendered?: string[];
  source_photo?: string | null;
  qa_passed?: boolean | null;
  qa_notes?: string[];
  gen_seconds?: number | null;
}

/** One shot of a multi-shot video; its keyframe carries the on-screen text. */
export interface ShotAsset {
  index: number;
  /** "hook" | "product" | "benefit" | "cta" */
  role: string;
  keyframe_path: string;
  clip_path?: string | null;
  duration_sec: number;
  onscreen_text: string;
  vo_text: string;
  /** True when the clip missed its deadline and a Ken Burns move stood in. */
  used_fallback: boolean;
}

/** A derived cut of the master video (shorter, or a different aspect). */
export interface VideoCutdown {
  label: string;
  local_path: string;
  duration_sec: number;
  aspect_ratio: string;
}

export interface VideoAsset {
  url: string;
  duration_sec: number;
  resolution: string;
  aspect_ratio: string;
  model?: string;
  route_id?: string | null;

  /* Studio extensions (Task 2). */
  platform?: Platform | null;
  local_path?: string | null;
  shots?: ShotAsset[];
  has_voiceover?: boolean;
  cutdowns?: VideoCutdown[];
}

/** The finished `AssetBundle`, as returned by `/pack`. */
export interface AssetPack {
  campaign_id?: string;
  images: ImageAsset[];
  videos: VideoAsset[];
  listing_copy?: Record<string, unknown> | null;
}

/* ────────────────────────────────────────────────────────────────────────────
 * Run request — `POST /api/studio/run`
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * What the brief panel submits. The endpoint's body is a `CampaignInput`; this
 * screen sends the subset a demo brand needs, and the backend fills the rest
 * from `sample_data/<brand_dir>/`.
 */
export interface StudioRunRequest {
  brand_dir: string;
  platforms: Platform[];
}

/** `{campaign_id}` — returned immediately, before the run starts. */
export interface StudioRunResponse {
  campaign_id: string;
}
