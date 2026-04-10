// Tool system type definitions for Mekong IDE Phase 3

export type ToolCategory = "read" | "write" | "execute" | "meta" | "blocked";

export type ToolCallStatus = "running" | "complete" | "error";

export interface ToolDef {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  hotkey?: string;
  approvalRequired?: boolean;
}

export interface ToolCall {
  id: string;
  toolId: string;
  toolName: string;
  args: Record<string, unknown>;
  status: ToolCallStatus;
  result?: string;
  durationMs?: number;
  timestamp: number;
}
