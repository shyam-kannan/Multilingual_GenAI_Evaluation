const BASE_URL = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// Typed API functions

import type { Prompt, EvalRun, CIRun } from "../types";

export interface OverviewData {
  locale_stats: Record<
    string,
    {
      total_runs: number;
      pass_rate: number;
      avg_quality: number;
      avg_hallucination: number;
    }
  >;
  total_runs: number;
  total_prompts: number;
  recent_runs: {
    id: string;
    locale: string;
    quality_score: number;
    hallucination_score: number;
    overall_passed: boolean;
    created_at: string;
  }[];
}

export interface PromptHistoryData {
  prompt_id: string;
  history: {
    version: number;
    version_id: string;
    labels: string[];
    is_active: boolean;
    created_at: string;
    locale_scores: Record<
      string,
      { avg_quality: number; avg_hallucination: number; run_count: number }
    >;
  }[];
}

export interface CIHistoryEntry {
  id: string;
  prompt_id: string;
  candidate_version_id: string;
  baseline_version_id: string | null;
  status: string;
  regressions: { locale: string; metric: string; baseline: number; candidate: number; delta: number }[];
  details: Record<string, unknown>;
  created_at: string;
}

export const endpoints = {
  getOverview: () => api.get<OverviewData>("/dashboard/overview"),
  getPrompts: () => api.get<Prompt[]>("/prompts"),
  getPromptHistory: (id: string) =>
    api.get<PromptHistoryData>(`/dashboard/prompts/${id}/history`),
  getPromptDetail: (id: string) => api.get<Prompt>(`/prompts/${id}`),
  getEvalRun: (id: string) => api.get<EvalRun>(`/eval-runs/${id}`),
  getEvalRuns: (params?: string) => api.get<EvalRun[]>(`/eval-runs${params ? `?${params}` : ""}`),
  getCIHistory: () => api.get<CIHistoryEntry[]>("/dashboard/ci-history"),
  getDiff: (promptId: string, v1: string, v2: string) =>
    api.get<{ diff: string; v1_version: number; v2_version: number }>(
      `/prompts/${promptId}/diff/${v1}/${v2}`
    ),
};
