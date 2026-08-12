/**
 * OpenClaw Agent type system
 * Defines core types for agent definitions, tools, and execution records
 */

/** LLM routing preference: 'planning' maps to Qwen2.5-Coder-32B, 'worker' maps to DeepSeek-R1-Distill-32B */
export type ModelPreference = 'planning' | 'worker';

/** Tool specification for an agent capability */
export interface AgentTool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

/** Full definition of an OpenClaw agent */
export interface AgentDefinition {
  /** Unique identifier, used as registry key */
  id: string;
  name: string;
  description: string;
  /** Primary capability category */
  capability: string;
  /** Determines which LLM backend to route to */
  modelPreference: ModelPreference;
  systemPrompt: string;
  tools: AgentTool[];
  maxTokens: number;
  temperature: number;
}

/** Record of a single agent execution */
export interface AgentExecution {
  executionId: string;
  agentId: string;
  input: string;
  output: string | null;
  creditsUsed: number;
  modelUsed: string;
  durationMs: number;
  createdAt: Date;
}
