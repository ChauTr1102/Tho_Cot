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
  /**
   * Alias for `url` on nodes that name their output `path` — the compose node
   * emits both. Rewritten to a `/media/...` URL by the API layer just like
   * `url`, so the canvas treats the two interchangeably.
   */
  path?: string;
  /** Which of the three routes produced this asset. */
  origin?: AssetOrigin;
  /** Visual QA verdict, e.g. "PASS" / "FAIL". */
  qa?: string;
  /** Findings behind a non-PASS verdict, at most a handful. */
  qa_notes?: string[];
  /** Kit slot id, e.g. "shopee_main". */
  slot?: string;
  platform?: Platform;
  /** Retry counter, present while a node is in the `retry` state. */
  attempt?: number;
  /** Human-readable detail, typically on `failed` or `degraded`. */
  message?: string;

  /**
   * The prompt this node rendered from.
   *
   * Not emitted by the backend yet — `pipeline.build_nodes` returns the
   * `RenderedImage` dataclass, which `_event_payload` drops. The canvas reads
   * it when it is present and offers an empty override box when it is not, so
   * adding it backend-side needs no frontend change. See `rerunStudioNode`.
   */
  prompt?: string;
  /** Poster frame for a video node, if the backend renders one separately. */
  poster?: string;
  /** Aspect ratio of the produced asset, e.g. "9:16". */
  ratio?: string;
  /** Seconds of finished video, on a clip or compose node. */
  duration?: number;

  /* Keys the graph executor adds itself (`graph.GraphEvent`). */
  /** Why a node failed without running: "dependency_failed" | "unschedulable". */
  reason?: string;
  /** The dependency whose failure killed this node. */
  failed_dep?: string;
  /** Exception text on a real failure. */
  error?: string;
  error_type?: string;
  /** Short reason a node finished `degraded` rather than `done`. */
  note?: string;
  /** True when the result came from the on-disk cache rather than a render. */
  cached?: boolean;

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
 * Real generated assets, in CampaignOutputDTO shape — `GET
 * /api/studio/{campaign_id}/assets` (backend/app/api/v1/endpoints/studio.py's
 * `AssetDTOResponse`).
 *
 * This is the studio's slice of `CampaignOutputDTO`
 * (backend/app/schemas/campaign_dto.py): `product_collection_image_set` and
 * `short_form_video_asset` carry `/media/...` paths that point at real files
 * the backend generated (not mock URLs), so the QA gate's image-dependent
 * checks can actually inspect them. Both asset fields are nullable — null
 * means "not ready yet", not "empty" — a caller should keep falling back to
 * mock/placeholder data for a field that is still null rather than sending an
 * empty object that would type-check and fail the QA checklist for the wrong
 * reason.
 * ────────────────────────────────────────────────────────────────────────── */

export interface StudioShortFormVideoAsset {
  generated_video_urls: string[];
  format: string;
  duration: string;
  additional_cuts: string[];
}

export interface StudioProductCollectionImageSet {
  product_hero_image: string;
  sku_detail_image: string;
  campaign_collection_image: string;
  marketplace_thumbnail: string;
  promotion_banner?: string | null;
  bundle_image?: string | null;
  seasonal_sale_image?: string | null;
}

export interface StudioCommerceCopy {
  product_title: string;
  product_description: string;
  listing_bullet_points: string[];
  ad_caption: string;
  promotion_copy?: string | null;
  short_hook_lines: string[];
}

export interface StudioAssetDTOResponse {
  /** The A/B posters by route id — `{"A": "/media/…", "B": "/media/…"}`. Empty
      for a kit rendered before the studio varied artwork by route. */
  ab_variants?: Record<string, string>;
  campaign_id: string;
  status: string;
  product_collection_image_set: StudioProductCollectionImageSet | null;
  short_form_video_asset: StudioShortFormVideoAsset | null;
  commerce_copy: StudioCommerceCopy | null;
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

/* ────────────────────────────────────────────────────────────────────────────
 * Single-node re-run — `POST /api/studio/{campaign_id}/node/{node_id}/rerun`
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * Re-render one node of a graph that has already run.
 *
 * `prompt` overrides the prompt the node rendered from the first time; omit it
 * to re-run the node unchanged. The endpoint answers immediately and the
 * result arrives on the campaign's existing SSE stream as ordinary `node`
 * events for that `node_id` — `running`, then a terminal state carrying the
 * new `url`. The canvas needs no second channel and no polling.
 *
 * Dependents are deliberately not re-run: re-rendering one keyframe must not
 * silently invalidate the master video a judge is halfway through watching.
 */
export interface StudioNodeRerunRequest {
  prompt?: string;
}

/** `{ok: true}` — an acknowledgement, not a result. */
export interface StudioNodeRerunResponse {
  ok: true;
}

/**
 * Whether the backend implements the single-node re-run endpoint.
 *
 * `unknown` until the probe answers. The control renders disabled with an
 * honest tooltip while support is `unavailable`, rather than posting into a
 * route that does not exist and failing silently.
 */
export type RerunSupport = "unknown" | "available" | "unavailable";
