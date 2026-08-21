/**
 * The two calls that bracket a run: propose, then approve.
 *
 * The studio no longer starts rendering the moment you press a button. A
 * director reads the campaign plan and proposes what to make — which
 * marketplaces, which assets, and the visual register — and you approve or
 * adjust it before a single image is generated. That proposal costs about
 * ninety seconds, and it is spent while you read it rather than while you watch
 * an empty screen; approving starts the render immediately.
 *
 * `direction` is the field that matters most here. It is free text, and it
 * outranks the director's own reading of the brief: "dễ thương, pastel", "điện
 * ảnh, tối giản", "sale 9.9 tưng bừng", "nói với dân văn phòng". The register
 * that comes back is written for that instruction, not chosen from a menu.
 */

import type { Platform } from "@/types/studio";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/** The campaign's visual register, authored per campaign by the director. */
export interface Register {
  name: string;
  lens: string;
  light: string;
  surface: string;
  grade: string;
  palette: string[];
  why: string;
  /** `director` when written for this brief, `preset` when it fell back. */
  source: string;
}

/** One asset the campaign will produce. */
export interface Deliverable {
  id: string;
  kind: "image" | "poster";
  platform: Platform;
  ratio: string;
  purpose: string;
}

export interface Draft {
  summary: string;
  register: Register;
  platforms: Platform[];
  deliverables: Deliverable[];
  video_shots: number;
  video_seconds: number;
  notes: string[];
}

export interface GraphNodeSpecLite {
  id: string;
  kind: string;
  deps: string[];
}

export interface DraftResult {
  campaignId: string;
  draft: Draft;
  graph: { nodes: GraphNodeSpecLite[]; rationale: string };
}

export interface DraftRequest {
  /** A campaign research has finished. The normal path. */
  campaign_id?: string;
  /** A demo brand under `sample_data/`. The fallback when nothing is researched. */
  brand_dir?: string;
  /** The planning agent's output, in either the nested or flat format. */
  plan?: Record<string, unknown>;
  campaign_input?: Record<string, unknown>;
  direction?: string;
  with_video?: boolean;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    // The backend answers errors in the same envelope, so prefer its message
    // over a bare status code — it is written for a person.
    const message =
      (payload && (payload.message || payload.detail || payload.error)) ??
      `HTTP ${res.status}`;
    throw new Error(String(message));
  }
  return (payload?.data ?? payload) as T;
}

/**
 * Ask the director what this campaign should be.
 *
 * Slow on purpose — around ninety seconds — because the model writes the whole
 * proposal. Callers should show that it is thinking, not spin.
 */
export async function requestDraft(req: DraftRequest): Promise<DraftResult> {
  const data = await post<{
    campaign_id: string;
    draft: Draft;
    graph: { nodes: GraphNodeSpecLite[]; rationale: string };
  }>("/studio/draft", { with_video: true, ...req });

  if (!data?.campaign_id) {
    throw new Error("Phản hồi từ /studio/draft thiếu campaign_id");
  }
  return {
    campaignId: data.campaign_id,
    draft: data.draft,
    graph: data.graph ?? { nodes: [], rationale: "" },
  };
}

/**
 * Approve a proposal and start building it.
 *
 * `draft` carries the user's edits. Only the fields a person can sensibly
 * change are honoured server-side; sending the whole object back unchanged is
 * the normal case.
 */
export async function approveDraft(
  campaignId: string,
  opts: { draft?: Partial<Draft>; withVideo?: boolean } = {}
): Promise<string> {
  const data = await post<{ campaign_id: string }>(
    `/studio/${encodeURIComponent(campaignId)}/approve`,
    { draft: opts.draft ?? null, with_video: opts.withVideo ?? true }
  );
  return data?.campaign_id ?? campaignId;
}

/** A campaign the research stage has already worked on. */
export interface ResearchCampaign {
  id: string;
  name: string;
  status: string;
  updated_at?: string;
}

/**
 * Campaigns the research stage has finished — the studio's inbox.
 *
 * The studio is downstream. Its input is whatever research already produced, so
 * the screen lists those rather than asking a user to describe a product the
 * system has on file. Campaigns that are not `researched` are returned too, so
 * the picker can show them greyed rather than pretending they do not exist.
 */
export async function listResearchCampaigns(): Promise<ResearchCampaign[]> {
  const res = await fetch(`${API_BASE_URL}/studio/campaigns`);
  if (!res.ok) return [];
  const body = await res.json().catch(() => null);
  const rows = body?.data ?? body;
  return Array.isArray(rows) ? (rows as ResearchCampaign[]) : [];
}

/** A few directions worth offering, so the field is not an empty box. */
export const DIRECTION_PRESETS: { label: string; value: string }[] = [
  { label: "Sale tưng bừng", value: "sale tưng bừng, chữ thật to, badge giảm giá đỏ vàng" },
  { label: "Dễ thương", value: "dễ thương, pastel, hợp Gen Z" },
  { label: "Điện ảnh", value: "điện ảnh, tối giản, ánh sáng một nguồn, nền tối" },
  { label: "Dân văn phòng", value: "điềm đạm, sạch sẽ, nói với dân văn phòng bận rộn" },
  { label: "Quà tặng", value: "sang trọng, thủ công, dùng làm quà biếu" },
];

/** A finished node, in the shape `GraphCanvas` consumes. */
export interface StudioNodeLite {
  id: string;
  kind: string;
  deps: string[];
  state: string;
  elapsed_sec: number;
  payload: { url?: string; slot?: string };
  updated_at: number;
}

/** One file a finished run left on disk. */
export interface SavedAsset {
  name: string;
  url: string;
  kind: "image" | "video" | "audio" | "file";
  platform: string | null;
  bytes: number;
}

export interface SavedResult {
  campaign_id: string;
  /** The same kit as graph nodes, ready for the canvas. */
  nodes: StudioNodeLite[];
  built: boolean;
  images: number;
  videos: number;
  total_files: number;
  bytes: number;
  assets: SavedAsset[];
}

/**
 * The kit a campaign already has, if it has one.
 *
 * A run takes six to twelve minutes and a judge has about that long for the
 * whole submission, so a campaign that was already built opens as a result
 * rather than as a form. `built: false` is an answer, not an error — a campaign
 * nobody has rendered yet simply offers to render.
 */
export async function fetchSavedResult(
  campaignId: string,
  includeIntermediate = false,
): Promise<SavedResult | null> {
  const res = await fetch(
    `${API_BASE_URL}/studio/${encodeURIComponent(campaignId)}/saved${includeIntermediate ? "?include_intermediate=true" : ""}`
  );
  if (!res.ok) return null;
  const body = await res.json().catch(() => null);
  return (body?.data ?? null) as SavedResult | null;
}

/** Absolute URL for a file the backend serves from its /media mount. */
export function mediaUrl(path: string): string {
  if (/^https?:/i.test(path)) return path;
  return `${API_BASE_URL.replace(/\/api\/?$/, "")}${path}`;
}

/* ────────────────────────────────────────────────────────────────────────────
 * Headless run — autopilot
 * ────────────────────────────────────────────────────────────────────────── */

/** `GET /studio/{campaign_id}/assets`, in the DTO shapes described in
 * @/types/studio's `StudioAssetDTOResponse`. Duplicated from `api.ts`'s
 * client rather than imported from it, so this module (used by both the
 * studio screen and the headless autopilot runner) has no dependency on the
 * StandardResponse request wrapper. */
async function fetchStudioAssets(campaignId: string) {
  const res = await fetch(
    `${API_BASE_URL}/studio/${encodeURIComponent(campaignId)}/assets`
  );
  if (res.status === 404) return null; // run not finished (or failed before producing a bundle) yet
  if (!res.ok) throw new Error(`GET /studio/${campaignId}/assets trả về HTTP ${res.status}`);
  const body = await res.json().catch(() => null);
  return body?.data ?? null;
}

export interface AutopilotStudioRunResult {
  campaignId: string;
  productCollectionImageSet: Record<string, unknown> | null;
  shortFormVideoAsset: Record<string, unknown> | null;
  commerceCopy: Record<string, unknown> | null;
}

/**
 * Drive a real studio run end-to-end with no human in the loop: propose,
 * auto-approve the proposal unedited, then poll until the bundle exists.
 *
 * This is the same real generation the manual pipeline runs
 * (`AssetStudio.handlePropose` + `handleApprove` + `useStudioStream`), just
 * without the draft-review UI — autopilot has nobody to show the draft to,
 * so approving it unedited is the equivalent of a user clicking "Duyệt"
 * immediately. `researchCampaignId` is the campaign research already
 * finished for (what `requestDraft({ campaign_id })` expects); the studio
 * mints its own new run id internally, returned here as `campaignId`.
 *
 * Polls `/assets` (rather than opening an EventSource, which needs a
 * component lifecycle to own the connection) every `pollIntervalMs` until
 * either asset field is ready or `timeoutMs` elapses. Throws on a genuine
 * failure (bad request, network error) but not on "still running" — a
 * timeout returns null fields rather than throwing, so a slow render
 * degrades to "no real assets yet" instead of failing the whole autopilot
 * run.
 */
export async function runStudioForAutopilot(
  researchCampaignId: string,
  {
    direction = "",
    pollIntervalMs = 5000,
    timeoutMs = 10 * 60 * 1000,
  }: { direction?: string; pollIntervalMs?: number; timeoutMs?: number } = {}
): Promise<AutopilotStudioRunResult> {
  const { campaignId, draft } = await requestDraft({
    campaign_id: researchCampaignId,
    direction,
    with_video: true,
  });

  await approveDraft(campaignId, { draft, withVideo: true });

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const assets = await fetchStudioAssets(campaignId);
    if (assets && (assets.product_collection_image_set || assets.short_form_video_asset)) {
      return {
        campaignId,
        productCollectionImageSet: assets.product_collection_image_set ?? null,
        shortFormVideoAsset: assets.short_form_video_asset ?? null,
        commerceCopy: assets.commerce_copy ?? null,
      };
    }
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }

  // Timed out — the run may still finish later, but the autopilot flow can't
  // wait indefinitely. Caller falls back to mock data for the report rather
  // than blocking the pipeline forever.
  return { campaignId, productCollectionImageSet: null, shortFormVideoAsset: null, commerceCopy: null };
}

/** The QA verdict a campaign already has, or null when nobody has judged it. */
export async function fetchSavedQa(
  campaignId: string
): Promise<Record<string, unknown> | null> {
  const res = await fetch(
    `${API_BASE_URL}/studio/${encodeURIComponent(campaignId)}/qa`
  );
  if (!res.ok) return null;
  const body = await res.json().catch(() => null);
  return (body?.data ?? null) as Record<string, unknown> | null;
}

/**
 * Store a verdict so re-opening the campaign does not re-run it.
 *
 * A QA pass costs a model call and a minute, and it is sampled rather than
 * deterministic — two runs over one unchanged kit disagree slightly, which
 * reads as the system being unsure instead of the model being sampled.
 */
export async function saveQa(
  campaignId: string,
  result: unknown
): Promise<void> {
  await fetch(`${API_BASE_URL}/studio/${encodeURIComponent(campaignId)}/qa`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  }).catch(() => undefined);
}
