/**
 * Event type definitions for @mekongcli/agent-sdk.
 * Mirrors Codebuff's event system adapted to mekong-cli's PEV architecture.
 */

// ─── Base event ───────────────────────────────────────────────────────────────

export interface BaseEvent {
  type: string;
  timestamp: number;
}

// ─── Lifecycle events ─────────────────────────────────────────────────────────

export interface StepStartEvent extends BaseEvent {
  type: "step_start";
  step: number;
  totalSteps: number;
  agent: string;
}

export interface StepEndEvent extends BaseEvent {
  type: "step_end";
  step: number;
  success: boolean;
  durationMs: number;
  output?: string;
  error?: string;
}

// ─── Tool events ──────────────────────────────────────────────────────────────

export interface ToolCallEvent extends BaseEvent {
  type: "tool_call";
  tool: string;
  params: Record<string, unknown>;
}

export interface ToolResultEvent extends BaseEvent {
  type: "tool_result";
  tool: string;
  success: boolean;
  output: string;
  durationMs: number;
  error?: string;
}

// ─── Agent events ─────────────────────────────────────────────────────────────

export interface AgentSpawnEvent extends BaseEvent {
  type: "agent_spawn";
  agentId: string;
  parentAgent: string;
  task: string;
}

// ─── Error event ──────────────────────────────────────────────────────────────

export interface ErrorEvent extends BaseEvent {
  type: "error";
  phase: "plan" | "execute" | "verify" | "spawn";
  message: string;
  recoverable: boolean;
}

// ─── Run completion ───────────────────────────────────────────────────────────

export interface RunCompleteEvent extends BaseEvent {
  type: "run_complete";
  success: boolean;
  totalSteps: number;
  totalDurationMs: number;
  results: RunResult[];
}

// ─── Union type ───────────────────────────────────────────────────────────────

export type AgentEvent =
  | StepStartEvent
  | StepEndEvent
  | ToolCallEvent
  | ToolResultEvent
  | AgentSpawnEvent
  | ErrorEvent
  | RunCompleteEvent;

// ─── Run state ────────────────────────────────────────────────────────────────

export type RunStatus = "running" | "completed" | "failed" | "paused";

export interface RunState {
  runId: string;
  goal: string;
  status: RunStatus;
  currentStep: number;
  totalSteps: number;
  agent: string;
  startedAt: number;
  events: AgentEvent[];
}

// ─── Client config ────────────────────────────────────────────────────────────

export interface MekongAgentClientConfig {
  /** Event callback - receives every event as it happens */
  handleEvent?: (event: AgentEvent) => void | Promise<void>;
  /** Max steps before auto-terminating */
  maxSteps?: number;
  /** Enforce tool restriction from agent.allowed_tools */
  enforceToolRestriction?: boolean;
}

// ─── Run output ───────────────────────────────────────────────────────────────

export interface RunOutput {
  /** Final output from the agent */
  output: string;
  /** Full run state for session continuity */
  state: RunState;
  /** Whether the run succeeded */
  success: boolean;
}

export interface RunResult {
  step: number;
  success: boolean;
  output: string;
  durationMs: number;
}
