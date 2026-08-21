import { CreateItemInput, HealthStatus, Item, StandardResponse, UpdateItemInput, ExtractRequest, ExtractResponse, VerifyChecklistRequest, VerifyChecklistResponseData } from "@/types";
import { parseResearchCampaignPlan, validateResearchSubmission, type ResearchCampaignPlan, type ResearchSubmission } from "@/types/research";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<StandardResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    const json = await res.json().catch(() => null);

    if (!res.ok) {
      const errorMsg = json?.detail || json?.message || `Request failed with status ${res.status}`;
      throw new ApiError(errorMsg, res.status, json);
    }

    return json as StandardResponse<T>;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      (error as Error)?.message || "Failed to connect to backend server. Make sure FastAPI is running on http://localhost:8000",
      0
    );
  }
}

export const api = {
  // Health check
  getHealth: () => request<HealthStatus>("/health"),

  // Items CRUD
  getItems: () => request<Item[]>("/items"),
  getItem: (id: number) => request<Item>(`/items/${id}`),
  createItem: (data: CreateItemInput) =>
    request<Item>("/items", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateItem: (id: number, data: UpdateItemInput) =>
    request<Item>(`/items/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteItem: (id: number) =>
    request<{ id: number }>(`/items/${id}`, {
      method: "DELETE",
    }),

  // Extractor
  extractProduct: async (input: ExtractRequest): Promise<ExtractResponse> => {
    const response = await fetch(`${API_BASE_URL}/extractor/extract`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: input.url,
        render: input.render ?? true,
        ...(input.model ? { model: input.model } : {}),
      }),
    });

    const json: unknown = await response.json().catch(() => null);

    if (!response.ok) {
      const payload = json as { detail?: string; message?: string } | null;
      throw new ApiError(
        payload?.detail || payload?.message || `Lỗi khi trích xuất dữ liệu từ URL (${response.status})`,
        response.status,
        json
      );
    }

    return json as ExtractResponse;
  },

  runResearch: async ({ input, files, evidence }: ResearchSubmission): Promise<ResearchCampaignPlan> => {
    const validationErrors = validateResearchSubmission({ input, files, evidence });
    if (validationErrors.length) throw new ApiError(validationErrors[0], 0, validationErrors);

    const form = new FormData();
    form.append("schema_version", input.schema_version);
    form.append("campaign_id", input.campaign_id);
    form.append("product_brief", JSON.stringify(input.product_brief));
    form.append("brand_kit", JSON.stringify(input.brand_kit));
    form.append("audience_brief", JSON.stringify(input.audience_brief));
    form.append("market_signal", JSON.stringify(input.market_signal));
    form.append("logo", files.logo!);
    files.product_photos.forEach((file) => form.append("product_photos", file));
    files.existing_product_visuals.forEach((file) => form.append("existing_product_visuals", file));
    if (evidence.trim()) form.append("evidence", evidence.trim());

    try {
      const response = await fetch(`${API_BASE_URL}/research/run`, { method: "POST", body: form });
      const json: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const payload = json as { message?: string } | null;
        throw new ApiError(payload?.message || `Research failed with status ${response.status}`, response.status, json);
      }
      return parseResearchCampaignPlan(json);
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(error instanceof Error ? error.message : "Không thể kết nối research backend.", 0);
    }
  },

  verifyChecklist: (payload: VerifyChecklistRequest) =>
    request<VerifyChecklistResponseData>("/verify-checklist", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

