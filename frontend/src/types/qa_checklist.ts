// Types for POST /api/verify-checklist. Mirrors backend/app/schemas/qa_checklist.py
// exactly (snake_case field names, since these are sent/received as raw JSON
// matching the wire format — no camelCase conversion, unlike campaign_dto.ts).

export type QASeverity = "BLOCKER" | "WARNING";
export type RegenerateTarget = "plan" | "asset";

export interface QAIssue {
  rule_id: string;
  severity: QASeverity;
  message: string;
  field: string;
  regenerate: RegenerateTarget;
}

export interface QACheckedItem {
  rule_id: string;
  description: string;
  passed: boolean;
  category: RegenerateTarget;
}

export interface VerifyChecklistResponseData {
  passed: boolean;
  iteration: number;
  issues: QAIssue[];
  checked_items: QACheckedItem[];
  regenerate: RegenerateTarget[];
}

// campaign_input / campaign_output below use the same snake_case shape as
// backend/app/schemas/campaign_dto.py. Left as loosely-typed JSON objects
// here (rather than full mirrored interfaces) since the pipeline stages
// that produce them are not wired up to real generation state yet — the
// caller is responsible for passing an object that matches CampaignInputDTO
// / CampaignOutputDTO's JSON shape.
export interface VerifyChecklistRequest {
  campaign_input: Record<string, unknown>;
  campaign_output: Record<string, unknown>;
  iteration?: number;
}
