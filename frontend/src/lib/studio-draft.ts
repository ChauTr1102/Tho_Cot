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

/** A few directions worth offering, so the field is not an empty box. */
export const DIRECTION_PRESETS: { label: string; value: string }[] = [
  { label: "Sale tưng bừng", value: "sale tưng bừng, chữ thật to, badge giảm giá đỏ vàng" },
  { label: "Dễ thương", value: "dễ thương, pastel, hợp Gen Z" },
  { label: "Điện ảnh", value: "điện ảnh, tối giản, ánh sáng một nguồn, nền tối" },
  { label: "Dân văn phòng", value: "điềm đạm, sạch sẽ, nói với dân văn phòng bận rộn" },
  { label: "Quà tặng", value: "sang trọng, thủ công, dùng làm quà biếu" },
];
