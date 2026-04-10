// Mock data for agent chat panel — replaced by API in Phase 7

import type { ChatMessage, PipelineStep, ModelConfig, ContextFooterData } from "@/lib/agent-types";

export const MOCK_MESSAGES: ChatMessage[] = [
  {
    id: "1",
    role: "agent",
    content: "OpenClaw online. Full codebase context loaded. How can I help?",
    timestamp: Date.now() - 120_000,
    model: "architect",
  },
  {
    id: "2",
    role: "user",
    content: "Fix the authentication bug in user service",
    timestamp: Date.now() - 90_000,
  },
  {
    id: "3",
    role: "system",
    content: "Tool: Read(src/auth/user-service.ts)",
    timestamp: Date.now() - 85_000,
    toolCall: "Read",
  },
  {
    id: "4",
    role: "agent",
    content: "Found the issue — JWT expiry check missing null guard on line 47. Applying fix now.",
    timestamp: Date.now() - 80_000,
    model: "reasoning",
  },
];

export const MOCK_PIPELINE_STEPS: PipelineStep[] = [
  { id: "plan", label: "Plan", status: "done", duration: 340 },
  { id: "execute", label: "Execute", status: "active" },
  { id: "verify", label: "Verify", status: "pending" },
];

export const MOCK_MODEL_CONFIGS: ModelConfig[] = [
  {
    id: "architect",
    name: "Claude Opus 4.6",
    provider: "Anthropic",
    latencyMs: 212,
    status: "online",
    tokensUsed: 8400,
    tokenLimit: 200_000,
  },
  {
    id: "reasoning",
    name: "Sonnet 4.6",
    provider: "Anthropic",
    latencyMs: 88,
    status: "online",
    tokensUsed: 3200,
    tokenLimit: 200_000,
  },
  {
    id: "audit",
    name: "Claude Haiku",
    provider: "Anthropic",
    latencyMs: 44,
    status: "degraded",
    tokensUsed: 1100,
    tokenLimit: 200_000,
  },
];

export const MOCK_CONTEXT_FOOTER: ContextFooterData = {
  tokensUsed: 12_700,
  tokenLimit: 200_000,
  cacheHits: 7,
  estimatedCost: 0.04,
};
