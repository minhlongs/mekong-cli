// Agent + Chat type definitions for Mekong IDE Phase 3

import type { ModelVariant, StatusVariant } from "@/lib/types";

export type MessageRole = "user" | "agent" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  model?: ModelVariant;
  toolCall?: string; // system messages only: tool invocation summary
}

export type PipelineStatus = "pending" | "active" | "done" | "error";

export interface PipelineStep {
  id: string;
  label: string;
  status: PipelineStatus;
  duration?: number; // ms, when done
}

export interface ModelConfig {
  id: ModelVariant;
  name: string;
  provider: string;
  latencyMs: number;
  status: "online" | "degraded" | "offline";
  tokensUsed: number;
  tokenLimit: number;
}

export interface ContextFooterData {
  tokensUsed: number;
  tokenLimit: number;
  cacheHits: number;
  estimatedCost: number; // USD
}
