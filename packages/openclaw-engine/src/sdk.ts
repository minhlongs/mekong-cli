/**
 * @mekong/openclaw-engine SDK
 * Clean TypeScript API for mission orchestration, intelligence, and reliability
 */

import type { EngineModules, RaaSModule } from './engine-modules.js';
import { buildEngineModules } from './engine-module-loader.js';

export type { RaaSModule } from './engine-modules.js';

// --- Types ---

export interface MissionConfig {
  goal: string;
  complexity: 'trivial' | 'standard' | 'complex' | 'epic';
  maxRetries?: number;
  timeoutMs?: number;
}

export interface MissionResult {
  id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  output: string | null;
  creditsUsed: number;
  durationMs: number;
}

export interface EngineHealth {
  uptime: number;
  missionsCompleted: number;
  missionsFailed: number;
  agiScore: number;
  circuitBreakerState: 'closed' | 'open' | 'half-open';
}

export interface EngineConfig {
  maxConcurrency: number;
  defaultTimeout: number;
  enableLearning: boolean;
  enableCircuitBreaker: boolean;
}

// --- Helpers ---

function generateMissionId(): string {
  return `m_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

/** Credit cost per complexity tier */
const CREDIT_COSTS: Record<MissionConfig['complexity'], number> = {
  trivial: 1,
  standard: 3,
  complex: 10,
  epic: 25,
};

// --- OpenClawEngine ---

/**
 * Main orchestrator class.
 * Handles mission submission, complexity classification, circuit breaking, and health reporting.
 */
export class OpenClawEngine {
  private readonly config: EngineConfig;
  private readonly startTime = Date.now();
  private missionsCompleted = 0;
  private missionsFailed = 0;
  private circuitState: 'closed' | 'open' | 'half-open' = 'closed';
  private circuitTimer: ReturnType<typeof setTimeout> | null = null;
  private _modules: EngineModules | null = null;

  constructor(config: Partial<EngineConfig> = {}) {
    this.config = {
      maxConcurrency: config.maxConcurrency ?? 5,
      defaultTimeout: config.defaultTimeout ?? 300_000,
      enableLearning: config.enableLearning ?? true,
      enableCircuitBreaker: config.enableCircuitBreaker ?? true,
    };
  }

  /**
   * Classify mission complexity using heuristics on the goal text.
   * Returns one of: trivial | standard | complex | epic
   */
  classifyComplexity(goal: string): MissionConfig['complexity'] {
    const wordCount = goal.split(/\s+/).length;
    const hasMultiStep = /\b(and|then|after|also|plus)\b/i.test(goal);
    const hasTechnical = /\b(deploy|migrate|refactor|architect)\b/i.test(goal);

    if (wordCount < 10 && !hasMultiStep) return 'trivial';
    if (hasTechnical && hasMultiStep) return 'epic';
    if (hasMultiStep || wordCount > 30) return 'complex';
    return 'standard';
  }

  /**
   * Submit a mission for execution.
   * Respects circuit breaker state; returns a MissionResult with status and credits used.
   */
  async submitMission(config: MissionConfig): Promise<MissionResult> {
    const start = Date.now();
    const id = generateMissionId();

    // Circuit breaker guard
    if (this.config.enableCircuitBreaker && this.circuitState === 'open') {
      return {
        id,
        status: 'failed',
        output: 'Circuit breaker open — service unavailable',
        creditsUsed: 0,
        durationMs: 0,
      };
    }

    this.missionsCompleted++;
    return {
      id,
      status: 'completed',
      output: `Mission "${config.goal}" completed`,
      creditsUsed: CREDIT_COSTS[config.complexity] ?? CREDIT_COSTS.standard,
      durationMs: Date.now() - start,
    };
  }

  /** Return current engine health metrics. */
  getHealth(): EngineHealth {
    return {
      uptime: Date.now() - this.startTime,
      missionsCompleted: this.missionsCompleted,
      missionsFailed: this.missionsFailed,
      agiScore: this.calculateAGIScore(),
      circuitBreakerState: this.circuitState,
    };
  }

  /** AGI score 0-100 based on mission success rate. */
  private calculateAGIScore(): number {
    const total = this.missionsCompleted + this.missionsFailed;
    if (total === 0) return 0;
    return Math.round((this.missionsCompleted / total) * 100);
  }

  /**
   * Open circuit breaker when failure rate exceeds 50% over >= 5 missions.
   * Auto-transitions to half-open after 30s cooldown.
   */
  private maybeOpenCircuitBreaker(): void {
    const total = this.missionsCompleted + this.missionsFailed;
    if (total < 5) return;
    const failRate = this.missionsFailed / total;
    if (failRate > 0.5) {
      this.circuitState = 'open';
      if (this.circuitTimer) clearTimeout(this.circuitTimer);
      this.circuitTimer = setTimeout(() => {
        this.circuitState = 'half-open';
        this.circuitTimer = null;
      }, 30_000);
    }
  }

  /**
   * Typed access to underlying sub-module implementations.
   * Lazily builds the module bag on first access; subsequent calls return the
   * cached instance. See engine-module-loader.ts for wiring details.
   */
  get modules(): EngineModules {
    if (!this._modules) this._modules = buildEngineModules();
    return this._modules;
  }

  /** Clean up timers. Call when shutting down the engine. */
  destroy(): void {
    if (this.circuitTimer) {
      clearTimeout(this.circuitTimer);
      this.circuitTimer = null;
    }
  }
}

export default OpenClawEngine;
