/**
 * Circuit Breaker — Auto-halt on abnormal conditions
 */

import { LicenseService, LicenseTier } from '../lib/raas-gate';

export interface CircuitBreakerConfig {
  maxDrawdownPercent?: number;
  maxErrorRate?: number;
  maxLossesInRow?: number;
  cooldownMs?: number;
}

export interface CircuitBreakerState {
  isHalted: boolean;
  haltedAt?: number;
  reason?: string;
  consecutiveLosses: number;
  totalTrades: number;
  totalLosses: number;
  errorCount: number;
}

export type CircuitBreakerStateLegacy = 'OPEN' | 'CLOSED' | 'HALF_OPEN';

export class CircuitBreaker {
  protected state: CircuitBreakerState = {
    isHalted: false,
    consecutiveLosses: 0,
    totalTrades: 0,
    totalLosses: 0,
    errorCount: 0,
  };
  protected config: Required<CircuitBreakerConfig>;

  constructor(config?: CircuitBreakerConfig) {
    this.config = {
      maxDrawdownPercent: config?.maxDrawdownPercent ?? 5,
      maxErrorRate: config?.maxErrorRate ?? 0.1,
      maxLossesInRow: config?.maxLossesInRow ?? 3,
      cooldownMs: config?.cooldownMs ?? 300000,
    };
  }

  recordTrade(pnl: number): void {
    if (this.state.isHalted) return;
    this.state.totalTrades += 1;
    if (pnl < 0) {
      this.state.totalLosses += 1;
      this.state.consecutiveLosses += 1;
      if (this.state.consecutiveLosses >= this.config.maxLossesInRow) {
        this.halt('Max consecutive losses reached');
      }
    } else {
      this.state.consecutiveLosses = 0;
    }
    const lossRate = this.state.totalLosses / this.state.totalTrades;
    if (lossRate > this.config.maxErrorRate && this.state.totalTrades >= 10) {
      this.halt('Max loss rate exceeded');
    }
  }

  recordError(error: string): void {
    this.state.errorCount += 1;
    if (this.state.errorCount >= 5) {
      this.halt('Max error count reached');
    }
  }

  protected halt(reason: string): void {
    this.state.isHalted = true;
    this.state.haltedAt = Date.now();
    this.state.reason = reason;
  }

  canTrade(): boolean {
    if (!this.state.isHalted) return true;
    if (!this.state.haltedAt) return false;
    const elapsed = Date.now() - this.state.haltedAt;
    if (elapsed >= this.config.cooldownMs) {
      this.state.isHalted = false;
      this.state.haltedAt = undefined;
      this.state.reason = undefined;
      this.state.errorCount = 0;
      this.state.consecutiveLosses = 0;
    }
    return !this.state.isHalted;
  }

  getState(): CircuitBreakerState {
    return { ...this.state };
  }

  reset(): void {
    this.state = {
      isHalted: false,
      consecutiveLosses: 0,
      totalTrades: 0,
      totalLosses: 0,
      errorCount: 0,
    };
  }
}

export class CircuitBreakerLegacy extends CircuitBreaker {
  private licenseService = LicenseService.getInstance();

  execute<T>(fn: () => Promise<T>): Promise<T> {
    if (!this.canTrade()) throw new Error('Circuit breaker is open');
    return fn();
  }

  getMetrics(): {
    state: CircuitBreakerStateLegacy;
    consecutiveLosses: number;
    totalTrades: number;
    failureCount: number;
    totalRequests: number;
    totalFailures: number;
    totalSuccesses: number;
  } {
    const s = this.getState();
    return {
      state: s.isHalted ? 'OPEN' : 'CLOSED',
      consecutiveLosses: s.consecutiveLosses,
      totalTrades: s.totalTrades,
      failureCount: s.errorCount,
      totalRequests: s.totalTrades,
      totalFailures: s.totalLosses,
      totalSuccesses: s.totalTrades - s.totalLosses,
    };
  }
}
