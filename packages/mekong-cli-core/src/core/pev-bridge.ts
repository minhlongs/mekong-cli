/**
 * PEV Bridge — Plan → Execute → Verify orchestrator
 * Connects CLI to RaaS Gateway mission execution loop
 */

import { EventEmitter } from 'node:events';
import { requireCloudClient } from './raas-client.js';
import type { Mission, MissionStatus, Complexity } from '@mekong/raas-sdk';
import { OpenClawEngine } from '@mekong/openclaw-engine';

// ─── Constants ────────────────────────────────────────────────────────────────

const POLL_INTERVAL_MS = 2500;
const POLL_MAX_ATTEMPTS = 60; // 2.5 min max
const MAX_VERIFY_RETRIES = 2;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PEVResult {
  mission_id: string;
  status: MissionStatus;
  outputs: string | null;
  credits_used: number;
  retries: number;
}

export interface PEVEvents {
  plan_start: [goal: string];
  plan_done: [missionId: string];
  execute_progress: [attempt: number, status: MissionStatus];
  verify_result: [passed: boolean, retries: number];
  error: [err: Error];
}

// ─── PEVBridge ────────────────────────────────────────────────────────────────

export class PEVBridge extends EventEmitter {
  private readonly engine = new OpenClawEngine({ enableCircuitBreaker: true });

  /** Classify goal complexity, mapping OpenClaw levels to RaaS SDK Complexity */
  classify(goal: string): Complexity {
    const raw = this.engine.classifyComplexity(goal);
    // Map OpenClaw 4-tier to RaaS SDK 3-tier
    const mapping: Record<string, Complexity> = {
      trivial: 'simple', standard: 'standard', complex: 'complex', epic: 'complex',
    };
    return mapping[raw] ?? 'standard';
  }

  /** Submit mission to gateway with type='plan' to get task breakdown */
  async plan(goal: string): Promise<Mission> {
    this.emit('plan_start', goal);
    const client = requireCloudClient();
    const complexity = this.classify(goal);
    const mission = await client.missions.submit({
      goal,
      complexity,
    });
    this.emit('plan_done', mission.id);
    return mission;
  }

  /**
   * Poll mission status until terminal state (completed/failed/cancelled).
   * Emits execute_progress on each poll tick.
   */
  async execute(missionId: string): Promise<Mission> {
    const client = requireCloudClient();

    for (let attempt = 1; attempt <= POLL_MAX_ATTEMPTS; attempt++) {
      await sleep(POLL_INTERVAL_MS);
      const polled = await client.missions.poll(missionId);
      this.emit('execute_progress', attempt, polled.status);

      if (polled.status === 'completed' || polled.status === 'failed' || polled.status === 'cancelled') {
        return client.missions.get(missionId);
      }
    }

    throw new PEVTimeoutError(missionId, POLL_MAX_ATTEMPTS * POLL_INTERVAL_MS);
  }

  /**
   * Verify mission result.
   * Passes when mission completed with a non-empty result.
   */
  verify(mission: Mission): boolean {
    return mission.status === 'completed' && !!mission.result;
  }

  /**
   * Full PEV loop — plan → execute → verify with retry on verify failure.
   * Retries by resubmitting a new mission on verify failure.
   */
  async run(goal: string): Promise<PEVResult> {
    let retries = 0;
    let lastMission: Mission | null = null;

    while (retries <= MAX_VERIFY_RETRIES) {
      const planned = await this.plan(goal);
      const executed = await this.execute(planned.id);
      lastMission = executed;

      const passed = this.verify(executed);
      this.emit('verify_result', passed, retries);

      if (passed) {
        return buildResult(executed, retries);
      }

      if (retries >= MAX_VERIFY_RETRIES) break;
      retries++;
    }

    // Exhausted retries — return last known state
    if (!lastMission) throw new Error('PEV run failed before any mission completed');
    return buildResult(lastMission, retries);
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildResult(mission: Mission, retries: number): PEVResult {
  return {
    mission_id: mission.id,
    status: mission.status,
    outputs: mission.result ?? null,
    credits_used: mission.credits_cost,
    retries,
  };
}

// ─── Errors ───────────────────────────────────────────────────────────────────

export class PEVTimeoutError extends Error {
  readonly code = 'PEV_TIMEOUT';
  constructor(missionId: string, elapsedMs: number) {
    super(`Mission ${missionId} timed out after ${elapsedMs / 1000}s`);
    this.name = 'PEVTimeoutError';
  }
}
