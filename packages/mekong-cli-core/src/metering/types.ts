/**
 * Metering types — v0.7 Usage Metering
 * Track LLM calls, tool runs, SOP executions for billing and quota enforcement.
 */

export type UsageCategory = 'llm_call' | 'tool_run' | 'sop_run';

/** A single usage event recorded at runtime */
export interface UsageEvent {
  id: string;
  category: UsageCategory;
  timestamp: string; // ISO 8601
  /** LLM-specific: provider name */
  provider?: string;
  /** LLM-specific: model name */
  model?: string;
  /** LLM-specific: tokens consumed */
  inputTokens?: number;
  outputTokens?: number;
  /** Tool/SOP name */
  resourceName?: string;
  /** Duration in ms */
  durationMs?: number;
  /** Estimated cost in USD */
  estimatedCost?: number;
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/** Aggregated reading for a time bucket */
export interface MeterReading {
  date: string; // YYYY-MM-DD
  llmCalls: number;
  toolRuns: number;
  sopRuns: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCostUsd: number;
}

/** Summary across a billing period */
export interface UsageSummary {
  period: BillingPeriod;
  readings: MeterReading[];
  totals: MeterReading;
  byCategory: Record<UsageCategory, number>;
  topModels: Array<{ model: string; calls: number; costUsd: number }>;
  topTools: Array<{ name: string; runs: number }>;
}

/** A billing period (month) */
export interface BillingPeriod {
  year: number;
  month: number; // 1-12
  label: string; // e.g. "2026-03"
}

/** Overage information when limits are exceeded */
export interface OverageInfo {
  category: UsageCategory;
  limit: number;
  used: number;
  over: number;
  percentUsed: number;
}

/** Result of a limit check */
export interface LimitCheckResult {
  allowed: boolean;
  category: UsageCategory;
  remaining: number;
  limit: number;
  used: number;
  message?: string;
}
