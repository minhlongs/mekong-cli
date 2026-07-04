/**
 * Session state management for agent runs.
 * Enables pause/resume and session continuity.
 */

import type { RunState, AgentEvent, RunCompleteEvent } from "./events";

const STORAGE_KEY = "mekong_agent_sessions";

export function createRunState(
  runId: string,
  goal: string,
  agent: string,
  totalSteps: number = 0,
): RunState {
  const now = Date.now();
  return {
    runId,
    goal,
    status: "running",
    currentStep: 0,
    totalSteps,
    agent,
    startedAt: now,
    events: [],
  };
}

export function addEvent(state: RunState, event: AgentEvent): RunState {
  return {
    ...state,
    events: [...state.events, event],
    currentStep: event.type === "step_end" ? event.step : state.currentStep,
  };
}

export function completeRun(
  state: RunState,
  success: boolean,
): RunState {
  const results = extractResults(state);
  const completeEvent: RunCompleteEvent = {
    type: "run_complete",
    success,
    totalSteps: state.totalSteps,
    totalDurationMs: Date.now() - state.startedAt,
    results,
    timestamp: Date.now(),
  };
  return {
    ...state,
    status: success ? "completed" : "failed",
    events: [...state.events, completeEvent],
  };
}

function extractResults(state: RunState): RunState["events"] {
  // Filter to step_end events as results
  return state.events.filter(
    (e): e is RunCompleteEvent["results"][number] => e.type === "step_end",
  );
}

export function serializeState(state: RunState): string {
  return JSON.stringify(state);
}

export function deserializeState(json: string): RunState {
  try {
    return JSON.parse(json) as RunState;
  } catch {
    throw new Error(`Invalid run state JSON: ${json.slice(0, 100)}`);
  }
}

export function saveSession(state: RunState): void {
  try {
    const sessions = loadAllSessions();
    sessions[state.runId] = state;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch {
    // Storage unavailable - non-fatal
  }
}

export function loadSession(runId: string): RunState | null {
  try {
    const sessions = loadAllSessions();
    return sessions[runId] ?? null;
  } catch {
    return null;
  }
}

export function loadAllSessions(): Record<string, RunState> {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
  } catch {
    return {};
  }
}

export function deleteSession(runId: string): void {
  try {
    const sessions = loadAllSessions();
    delete sessions[runId];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch {
    // non-fatal
  }
}
