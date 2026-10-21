/**
 * EmergencyCircuitBreaker — Safety kill switch for arbitrage engine.
 */

import { getArbLogger } from './arb-logger';
import {
  CircuitState, TripEvent, CircuitBreakerConfig, DEFAULT_CIRCUIT_BREAKER_CONFIG,
} from './emergency-circuit-types';

export * from './emergency-circuit-types';

const logger = getArbLogger();

export class EmergencyCircuitBreaker {
  private config: CircuitBreakerConfig;
  private state: CircuitState = 'closed';
  private dailyLossUsd = 0;
  private consecutiveLosses = 0;
  private recentLosses: number[] = [];
  private tripHistory: TripEvent[] = [];
  private lastTripTime = 0;
  private halfOpenTradeCount = 0;
  private cooldownTimer: NodeJS.Timeout | null = null;

  constructor(config?: Partial<CircuitBreakerConfig>) {
    this.config = { ...DEFAULT_CIRCUIT_BREAKER_CONFIG, ...config };
  }

  isAllowed(): boolean {
    if (this.state === 'closed') return true;
    if (this.state === 'half_open') {
      return this.halfOpenTradeCount < this.config.halfOpenMaxTrades;
    }
    return false;
  }

  recordTrade(profitUsd: number): boolean {
    if (this.state === 'half_open') {
      this.halfOpenTradeCount++;
      if (profitUsd < 0) {
        this.trip('loss_streak', `Loss in half-open state: $${profitUsd.toFixed(2)}`, { profitUsd });
        return true;
      }
      if (this.halfOpenTradeCount >= this.config.halfOpenMaxTrades) {
        this.close();
      }
      return false;
    }

    if (profitUsd < 0) {
      this.dailyLossUsd += Math.abs(profitUsd);
      this.consecutiveLosses++;
      this.recentLosses.push(Date.now());

      if (this.dailyLossUsd >= this.config.maxDailyLossUsd) {
        this.trip('daily_loss', `Daily loss $${this.dailyLossUsd.toFixed(2)} >= $${this.config.maxDailyLossUsd}`, {
          dailyLoss: this.dailyLossUsd, limit: this.config.maxDailyLossUsd,
        });
        return true;
      }

      if (this.consecutiveLosses >= this.config.maxConsecutiveLosses) {
        this.trip('loss_streak', `${this.consecutiveLosses} consecutive losses`, {
          count: this.consecutiveLosses, limit: this.config.maxConsecutiveLosses,
        });
        return true;
      }

      const now = Date.now();
      this.recentLosses = this.recentLosses.filter(t => now - t <= this.config.rapidLossWindowMs);
      if (this.recentLosses.length >= this.config.rapidLossCount) {
        this.trip('rapid_loss', `${this.recentLosses.length} losses in ${this.config.rapidLossWindowMs}ms`, {
          count: this.recentLosses.length, windowMs: this.config.rapidLossWindowMs,
        });
        return true;
      }
    } else {
      this.consecutiveLosses = 0;
    }

    return false;
  }

  manualTrip(reason: string): void { this.trip('manual', reason, {}); }

  recordExchangeAnomaly(exchange: string, description: string): boolean {
    this.trip('exchange_anomaly', `${exchange}: ${description}`, { exchange });
    return true;
  }

  getState(): CircuitState { return this.state; }
  getTripHistory(): TripEvent[] { return [...this.tripHistory]; }

  getMetrics(): {
    state: CircuitState; dailyLossUsd: number; consecutiveLosses: number;
    totalTrips: number; lastTripTime: number;
  } {
    return {
      state: this.state, dailyLossUsd: this.dailyLossUsd,
      consecutiveLosses: this.consecutiveLosses,
      totalTrips: this.tripHistory.length, lastTripTime: this.lastTripTime,
    };
  }

  resetDaily(): void {
    this.dailyLossUsd = 0;
    this.consecutiveLosses = 0;
    this.recentLosses = [];
    if (this.state === 'open') this.close();
    logger.info('[CircuitBreaker] Daily reset');
  }

  forceClose(): void {
    this.close();
    logger.info('[CircuitBreaker] Force closed by operator');
  }

  shutdown(): void {
    if (this.cooldownTimer) {
      clearTimeout(this.cooldownTimer);
      this.cooldownTimer = null;
    }
  }

  private trip(trigger: TripEvent['trigger'], reason: string, details: Record<string, number | string>): void {
    this.state = 'open';
    this.lastTripTime = Date.now();
    this.tripHistory.push({ timestamp: Date.now(), reason, trigger, details });
    logger.warn(`[CircuitBreaker] 🔴 TRIPPED: ${reason}`);
    this.scheduleCooldown();
  }

  private scheduleCooldown(): void {
    if (this.cooldownTimer) clearTimeout(this.cooldownTimer);
    this.cooldownTimer = setTimeout(() => {
      if (this.state === 'open') {
        this.state = 'half_open';
        this.halfOpenTradeCount = 0;
        logger.info('[CircuitBreaker] 🟡 Half-open: testing with limited trades');
      }
    }, this.config.cooldownMs);
  }

  private close(): void {
    this.state = 'closed';
    this.halfOpenTradeCount = 0;
    if (this.cooldownTimer) {
      clearTimeout(this.cooldownTimer);
      this.cooldownTimer = null;
    }
    logger.info('[CircuitBreaker] 🟢 Circuit CLOSED — trading resumed');
  }
}
