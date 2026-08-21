export interface StandardResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  error?: unknown;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  database: string;
  version: string;
  project: string;
}

export interface Item {
  id: number;
  title: string;
  description?: string | null;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateItemInput {
  title: string;
  description?: string;
  is_completed?: boolean;
}

export interface UpdateItemInput {
  title?: string;
  description?: string;
  is_completed?: boolean;
}
export * from './campaign_dto';
export * from './research';
