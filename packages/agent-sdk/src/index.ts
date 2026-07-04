/**
 * @mekongcli/agent-sdk
 *
 * Event-driven SDK for mekong-cli agent runs.
 * Streams progress events, enables session continuity.
 *
 * Usage:
 *   import { MekongAgentClient } from "@mekongcli/agent-sdk";
 *   const client = new MekongAgentClient({
 *     handleEvent: (e) => console.log(e)
 *   });
 *   const result = await client.run({ goal: "fix bug", agent: "cto" });
 */

export { MekongAgentClient } from "./client";
export type {
  AgentCompleteEvent,
  AgentEvent,
  AgentSpawnEvent,
  ErrorEvent,
  MekongAgentClientConfig,
  RunCompleteEvent,
  RunOutput,
  RunResult,
  RunState,
  StepEndEvent,
  StepStartEvent,
  ToolCallEvent,
  ToolResultEvent,
} from "./events";
export {
  completeRun,
  createRunState,
  deleteSession,
  deserializeState,
  loadAllSessions,
  loadSession,
  saveSession,
  serializeState,
} from "./session";
