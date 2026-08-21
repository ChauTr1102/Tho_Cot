import { CreateItemInput, HealthStatus, Item, StandardResponse, UpdateItemInput } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiError extends Error {
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
      const errorMsg = json?.message || `Request failed with status ${res.status}`;
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
};
