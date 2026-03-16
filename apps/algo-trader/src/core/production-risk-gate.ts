/**
 * Production Risk Gate — Single entry point for all pre-trade risk checks.
 * Designed for $100K+ portfolios. Composes circuit breakers, position limits,
 * rate limiter, and kill switch into one canTrade() call.
 */

import { CircuitBreakerManager } from './circuit-breakers';
import { PortfolioManager } from './PortfolioManager';
import { logger } from '../utils/logger';

export interface ProductionRiskConfig {
  portfolioValue: number;         // Total portfolio value (e.g. 100000)
  maxDailyLossPct: number;        // Max daily loss as % (default: 3)
  maxDrawdownPct: number;         // Max drawdown from peak (default: 10)
  maxPerMarketPct: number;        // Max % of portfolio per market (default: 5)
  maxConsecutiveLosses: number;   // Halt after N consecutive losses (default: 5)
  maxOrdersPerMinute: number;     // Rate limiter (default: 60)
}

const DEFAULT_CONFIG: ProductionRiskConfig = {
  portfolioValue: 100000,
  maxDailyLossPct: 3,
  maxDrawdownPct: 10,
  maxPerMarketPct: 5,
  maxConsecutiveLosses: 5,
  maxOrdersPerMinute: 60,
};

/** Sliding window rate limiter */
class RateLimiter {
  private timestamps: number[] = [];
  private maxPerWindow: number;
  private windowMs: number;

  constructor(maxPerWindow: number, windowMs: number = 60000) {
    this.maxPerWindow = maxPerWindow;
    this.windowMs = windowMs;
  }

  tryAcquire(): boolean {
    const now = Date.now();
    // Remove expired timestamps
    this.timestamps = this.timestamps.filter(t => now - t < this.windowMs);
    if (this.timestamps.length >= this.maxPerWindow) return false;
    this.timestamps.push(now);
    return true;
  }

  getCount(): number {
    const now = Date.now();
    this.timestamps = this.timestamps.filter(t => now - t < this.windowMs);
    return this.timestamps.length;
  }
}

export interface RiskCheckResult {
  allowed: boolean;
  reason?: string;
  checks: {
    killSwitch: boolean;
    dailyLoss: boolean;
    drawdown: boolean;
    consecutiveLoss: boolean;
    perMarketCap: boolean;
    rateLimit: boolean;
  };
}

export class ProductionRiskGate {
  private config: ProductionRiskConfig;
  private cbManager: CircuitBreakerManager;
  private rateLimiter: RateLimiter;
  private peakValue: number;
  private currentValue: number;
  private dailyPnl: number = 0;

  constructor(config?: Partial<ProductionRiskConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.cbManager = new CircuitBreakerManager({
      maxDrawdownPercent: this.config.maxDrawdownPct,
      maxConsecutiveLosses: this.config.maxConsecutiveLosses,
      dailyLossLimitUsd: this.config.portfolioValue * (this.config.maxDailyLossPct / 100),
    });
    this.rateLimiter = new RateLimiter(this.config.maxOrdersPerMinute);
    this.peakValue = this.config.portfolioValue;
    this.currentValue = this.config.portfolioValue;
  }

  /**
   * Single check before any trade — returns allowed/denied + reason
   */
  canTrade(marketId?: string, positionValueUsd?: number): RiskCheckResult {
    const checks = {
      killSwitch: false,
      dailyLoss: false,
      drawdown: false,
      consecutiveLoss: false,
      perMarketCap: false,
      rateLimit: false,
    };

    // 1. Kill switch
    const status = this.cbManager.getStatus();
    if (status.killSwitch.isTripped) {
      checks.killSwitch = true;
      return { allowed: false, reason: `Kill switch: ${status.killSwitch.reason}`, checks };
    }

    // 2. Daily loss
    if (status.dailyLoss.isTripped) {
      checks.dailyLoss = true;
      return { allowed: false, reason: `Daily loss limit ${this.config.maxDailyLossPct}% hit`, checks };
    }

    // 3. Drawdown
    const drawdownPct = this.peakValue > 0 ? ((this.peakValue - this.currentValue) / this.peakValue) * 100 : 0;
    if (this.cbManager.checkAll(drawdownPct, undefined, this.dailyPnl)) {
      checks.drawdown = true;
      return { allowed: false, reason: `Drawdown ${drawdownPct.toFixed(1)}% exceeds ${this.config.maxDrawdownPct}%`, checks };
    }

    // 4. Consecutive loss
    if (status.consecutiveLoss.isTripped) {
      checks.consecutiveLoss = true;
      return { allowed: false, reason: `${this.config.maxConsecutiveLosses} consecutive losses`, checks };
    }

    // 5. Per-market cap
    if (marketId && positionValueUsd) {
      const maxPerMarket = this.config.portfolioValue * (this.config.maxPerMarketPct / 100);
      if (positionValueUsd > maxPerMarket) {
        checks.perMarketCap = true;
        return { allowed: false, reason: `Market ${marketId}: $${positionValueUsd} > cap $${maxPerMarket}`, checks };
      }
    }

    // 6. Rate limiter
    if (!this.rateLimiter.tryAcquire()) {
      checks.rateLimit = true;
      return { allowed: false, reason: `Rate limit: ${this.config.maxOrdersPerMinute}/min exceeded`, checks };
    }

    return { allowed: true, checks };
  }

  /** Record trade outcome for circuit breaker tracking */
  recordTrade(profit: number): void {
    this.dailyPnl += profit;
    this.currentValue += profit;
    if (this.currentValue > this.peakValue) this.peakValue = this.currentValue;

    const drawdownPct = ((this.peakValue - this.currentValue) / this.peakValue) * 100;
    this.cbManager.checkAll(drawdownPct, profit, this.dailyPnl);
  }

  /** Emergency stop */
  emergencyStop(reason?: string): void {
    this.cbManager.emergencyStop(reason || 'Manual emergency stop');
    logger.error(`[ProductionRiskGate] EMERGENCY STOP: ${reason}`);
  }

  /** Reset all breakers (requires explicit call) */
  reset(): void {
    this.cbManager.resetAll();
    this.dailyPnl = 0;
    logger.warn('[ProductionRiskGate] All risk gates reset');
  }

  /** Get full status */
  getStatus() {
    return {
      ...this.cbManager.getStatus(),
      portfolioValue: this.currentValue,
      peakValue: this.peakValue,
      dailyPnl: this.dailyPnl,
      drawdownPct: this.peakValue > 0 ? ((this.peakValue - this.currentValue) / this.peakValue) * 100 : 0,
      ordersThisMinute: this.rateLimiter.getCount(),
      config: this.config,
    };
  }
}
