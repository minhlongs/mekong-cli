/**
 * TypeScript interfaces for all Gateway API responses.
 * Re-exports shared types from lib/types/* where overlap exists.
 */

export type { Engine, SystemResources, EngineStatus } from "@/lib/types/engine-types";
export type { Task, TaskStatus, TaskPriority } from "@/lib/types/task-types";
export type { Position, FairValue, LlmSignal, TradingStats } from "@/lib/types/trading-types";
export type { TokenUsage, CompressionEvent, ContextMetrics } from "@/lib/types/context-types";
export type { ChatMessage, PipelineStep, ModelConfig } from "@/lib/agent-types";
export type { ToolDef, ToolCall } from "@/lib/tool-types";

// --- Gateway-specific response shapes ---

export interface ApiResult<T> {
  data: T | null;
  error: string | null;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "down";
  timestamp: string;
  version: string;
}

/** Typed error thrown by api-client on non-2xx responses */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// SSE event from /ws/events or mission stream
export interface SseEvent<T = unknown> {
  type: string;
  payload: T;
}
