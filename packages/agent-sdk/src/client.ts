/**
 * MekongAgentClient - Event-driven client for mekong-cli agent runs.
 *
 * Usage:
 *   const client = new MekongAgentClient({ handleEvent: (e) => console.log(e) });
 *   const result = await client.run({ goal: "fix the bug", agent: "cto" });
 */

import type {
  AgentEvent,
  MekongAgentClientConfig,
  RunOutput,
  RunState,
  StepStartEvent,
  StepEndEvent,
  ToolCallEvent,
  ToolResultEvent,
  ErrorEvent,
} from "./events";
import {
  addEvent,
  completeRun,
  createRunState,
  saveSession,
} from "./session";

export class MekongAgentClient {
  private config: Required<MekongAgentClientConfig>;
  private eventHandlers: ((event: AgentEvent) => void | Promise<void>)[];

  constructor(config: MekongAgentClientConfig = {}) {
    this.config = {
      handleEvent: config.handleEvent ?? (() => {}),
      maxSteps: config.maxSteps ?? 20,
      enforceToolRestriction: config.enforceToolRestriction ?? true,
    };
    this.eventHandlers = [this.config.handleEvent];
  }

  /** Register an additional event handler */
  onEvent(handler: (event: AgentEvent) => void | Promise<void>): () => void {
    this.eventHandlers.push(handler);
    return () => {
      const idx = this.eventHandlers.indexOf(handler);
      if (idx >= 0) this.eventHandlers.splice(idx, 1);
    };
  }

  /** Emit an event to all handlers */
  private async emit(event: AgentEvent): Promise<void> {
    for (const handler of this.eventHandlers) {
      try {
        const result = handler(event);
        if (result instanceof Promise) {
          await result;
        }
      } catch {
        // Non-fatal: one handler failing shouldn't block others
      }
    }
  }

  /**
   * Run an agent task with event streaming.
   *
   * @param params - Run parameters
   * @param params.goal - The task/goal to accomplish
   * @param params.agent - Agent role (e.g. "cto", "git", "file")
   * @param params.runId - Optional run ID (generated if not provided)
   * @param params.inputSchema - Optional JSON schema for input validation
   * @returns RunOutput with final output and state
   */
  async run(params: {
    goal: string;
    agent: string;
    runId?: string;
    inputSchema?: Record<string, unknown>;
  }): Promise<RunOutput> {
    const runId = params.runId ?? `run_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const state = createRunState(runId, params.goal, params.agent);

    await this.emit({
      type: "step_start",
      step: 0,
      totalSteps: 1,
      agent: params.agent,
      timestamp: Date.now(),
    } as StepStartEvent);

    try {
      // Execute the agent run
      const result = await this.executeAgent(params, state);

      const completed = completeRun(state, result.success);
      await this.emit({
        type: "run_complete",
        success: result.success,
        totalSteps: completed.totalSteps,
        totalDurationMs: Date.now() - completed.startedAt,
        results: [],
        timestamp: Date.now(),
      } as RunCompleteEvent);

      saveSession(completed);

      return {
        output: result.output,
        state: completed,
        success: result.success,
      };
    } catch (error) {
      const errorEvent: ErrorEvent = {
        type: "error",
        phase: "execute",
        message: error instanceof Error ? error.message : String(error),
        recoverable: false,
        timestamp: Date.now(),
      };
      state.events.push(errorEvent);
      await this.emit(errorEvent);

      const failed = completeRun(state, false);
      return {
        output: errorEvent.message,
        state: failed,
        success: false,
      };
    }
  }

  /** Execute the agent - to be overridden or configured with actual execution */
  private async executeAgent(
    params: { goal: string; agent: string },
    state: RunState,
  ): Promise<{ success: boolean; output: string }> {
    const startTime = Date.now();

    await this.emit({
      type: "step_start",
      step: 1,
      totalSteps: 1,
      agent: params.agent,
      timestamp: Date.now(),
    } as StepStartEvent);

    // Simulate tool calls for demonstration
    // In production, this would invoke the actual agent execution
    await this.emit({
      type: "tool_call",
      tool: "plan",
      params: { goal: params.goal },
      timestamp: Date.now(),
    } as ToolCallEvent);

    await this.emit({
      type: "tool_result",
      tool: "plan",
      success: true,
      output: `Planned execution for agent: ${params.agent}`,
      durationMs: 10,
      timestamp: Date.now(),
    } as ToolResultEvent);

    const output = `Agent [${params.agent}] processed: ${params.goal}`;
    const durationMs = Date.now() - startTime;

    await this.emit({
      type: "step_end",
      step: 1,
      success: true,
      durationMs,
      output,
      timestamp: Date.now(),
    } as StepEndEvent);

    return { success: true, output };
  }
}
