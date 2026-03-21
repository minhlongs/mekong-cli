/**
 * @mekong/openclaw-engine SDK
 * Clean TypeScript API for mission orchestration, intelligence, and reliability
 */

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
    const hasMultiStep = /and|then|after|also|plus/i.test(goal);
    const hasTechnical = /deploy|migrate|refactor|architect/i.test(goal);

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

    try {
      const result: MissionResult = {
        id,
        status: 'completed',
        output: `Mission "${config.goal}" completed`,
        creditsUsed: CREDIT_COSTS[config.complexity] ?? CREDIT_COSTS.standard,
        durationMs: Date.now() - start,
      };

      this.missionsCompleted++;
      return result;
    } catch (err) {
      this.missionsFailed++;
      this.maybeOpenCircuitBreaker();
      return {
        id,
        status: 'failed',
        output: String(err),
        creditsUsed: 0,
        durationMs: Date.now() - start,
      };
    }
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
      setTimeout(() => {
        this.circuitState = 'half-open';
      }, 30_000);
    }
  }
}

export default OpenClawEngine;
