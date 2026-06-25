export interface Prompt {
  id: string;
  name: string;
  created_at: string;
  versions: PromptVersion[];
}

export interface PromptVersion {
  id: string;
  prompt_id: string;
  version: number;
  content: string;
  content_hash: string;
  labels: string[];
  is_active: boolean;
  created_at: string;
}

export interface GoldenExample {
  id: string;
  prompt_id: string;
  locale: string;
  input_text: string;
  expected_output: string | null;
  created_at: string;
}

export interface EvalRun {
  id: string;
  prompt_version_id: string;
  locale: string;
  input_text: string;
  llm_output: string;
  quality_score: number;
  quality_reasoning: string;
  hallucination_score: number;
  hallucination_reasoning: string;
  moderation_passed: boolean;
  moderation_reasoning: string;
  world_readiness_passed: boolean;
  world_readiness_details: Record<string, unknown>;
  overall_passed: boolean;
  created_at: string;
}

export interface CIRun {
  id: string;
  prompt_id: string;
  candidate_version_id: string;
  baseline_version_id: string | null;
  status: "passed" | "failed" | "error";
  regressions: Regression[];
  details: Record<string, unknown>;
  created_at: string;
}

export interface Regression {
  locale: string;
  metric: string;
  baseline: number;
  candidate: number;
  delta: number;
}

export type Locale = "en-US" | "es-MX" | "ar-SA" | "ja-JP";

export const LOCALES: Locale[] = ["en-US", "es-MX", "ar-SA", "ja-JP"];
