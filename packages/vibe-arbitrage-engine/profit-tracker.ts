/**
 * ProfitTracker — Real-time equity curve, drawdown monitoring, and performance metrics.
 */

import { getArbLogger } from './arb-logger';
import {
  EquityPoint, DrawdownAlert, PerformanceSummary,
  ProfitTrackerConfig, DEFAULT_PROFIT_TRACKER_CONFIG,
} from './profit-tracker-types';
import {
  computeEquityReturns, calculateSharpeRatio,
  calculateSortinoRatio, printPerformanceReport,
} from './profit-tracker-math';

export * from './profit-tracker-types';
export * from './profit-tracker-math';

const logger = getArbLogger();

export class ProfitTracker {
  private config: ProfitTrackerConfig;
  private equityCurve: EquityPoint[] = [];
  private alerts: DrawdownAlert[] = [];
  private alertListeners: ((alert: DrawdownAlert) => void)[] = [];
  private triggeredThresholds: Set<number> = new Set();

  private currentEquity: number;
  private peakEquity: number;
  private troughEquity: number;
  private cumulativePnl = 0;
  private tradeCount = 0;
  private winCount = 0;
  private lossCount = 0;
  private totalWinAmount = 0;
  private totalLossAmount = 0;
  private maxConsecutiveWins = 0;
  private maxConsecutiveLosses = 0;
  private currentStreak = 0;
  private maxDrawdownPercent = 0;
  private startTime: number;

  constructor(config?: Partial<ProfitTrackerConfig>) {
    this.config = { ...DEFAULT_PROFIT_TRACKER_CONFIG, ...config };
    this.currentEquity = this.config.initialEquity;
    this.peakEquity = this.config.initialEquity;
    this.troughEquity = this.config.initialEquity;
    this.startTime = Date.now();
    this.equityCurve.push({
      timestamp: this.startTime, equity: this.config.initialEquity,
      pnl: 0, cumulativePnl: 0, drawdownPercent: 0, tradeId: 0,
    });
  }

  onDrawdownAlert(callback: (alert: DrawdownAlert) => void): void {
    this.alertListeners.push(callback);
  }

  recordTrade(pnl: number): void {
    this.tradeCount++;
    this.cumulativePnl += pnl;
    this.currentEquity = this.config.initialEquity + this.cumulativePnl;

    if (pnl > 0) {
      this.winCount++;
      this.totalWinAmount += pnl;
      this.currentStreak = this.currentStreak > 0 ? this.currentStreak + 1 : 1;
      this.maxConsecutiveWins = Math.max(this.maxConsecutiveWins, this.currentStreak);
    } else if (pnl < 0) {
      this.lossCount++;
      this.totalLossAmount += Math.abs(pnl);
      this.currentStreak = this.currentStreak < 0 ? this.currentStreak - 1 : -1;
      this.maxConsecutiveLosses = Math.max(this.maxConsecutiveLosses, Math.abs(this.currentStreak));
    }

    if (this.currentEquity > this.peakEquity) {
      this.peakEquity = this.currentEquity;
      this.triggeredThresholds.clear();
    }
    if (this.currentEquity < this.troughEquity) {
      this.troughEquity = this.currentEquity;
    }

    const drawdownPercent = this.peakEquity > 0
      ? ((this.peakEquity - this.currentEquity) / this.peakEquity) * 100 : 0;
    if (drawdownPercent > this.maxDrawdownPercent) this.maxDrawdownPercent = drawdownPercent;

    this.equityCurve.push({
      timestamp: Date.now(), equity: this.currentEquity, pnl,
      cumulativePnl: this.cumulativePnl, drawdownPercent, tradeId: this.tradeCount,
    });

    if (this.equityCurve.length > this.config.maxEquityPoints) {
      this.equityCurve.splice(0, this.equityCurve.length - this.config.maxEquityPoints);
    }
    this.checkDrawdownAlerts(drawdownPercent);
  }

  getSummary(): PerformanceSummary {
    const returns = computeEquityReturns(this.equityCurve, this.config.sharpeWindowSize);
    const sharpe = calculateSharpeRatio(returns, this.config.riskFreeRate);
    const sortino = calculateSortinoRatio(returns, this.config.riskFreeRate);
    const maxDdUsd = this.peakEquity - this.troughEquity;

    return {
      initialEquity: this.config.initialEquity, currentEquity: this.currentEquity,
      cumulativePnl: this.cumulativePnl,
      cumulativePnlPercent: (this.cumulativePnl / this.config.initialEquity) * 100,
      maxDrawdownPercent: this.maxDrawdownPercent, maxDrawdownUsd: maxDdUsd,
      peakEquity: this.peakEquity, troughEquity: this.troughEquity,
      sharpeRatio: sharpe, sortinoRatio: sortino, totalTrades: this.tradeCount,
      winningTrades: this.winCount, losingTrades: this.lossCount,
      winRate: this.tradeCount > 0 ? (this.winCount / this.tradeCount) * 100 : 0,
      avgWin: this.winCount > 0 ? this.totalWinAmount / this.winCount : 0,
      avgLoss: this.lossCount > 0 ? this.totalLossAmount / this.lossCount : 0,
      profitFactor: this.totalLossAmount > 0 ? this.totalWinAmount / this.totalLossAmount : (this.totalWinAmount > 0 ? Infinity : 0),
      recoveryFactor: maxDdUsd > 0 ? this.cumulativePnl / maxDdUsd : 0,
      maxConsecutiveWins: this.maxConsecutiveWins, maxConsecutiveLosses: this.maxConsecutiveLosses,
      uptimeMs: Date.now() - this.startTime,
    };
  }

  getEquityCurve(): EquityPoint[] { return [...this.equityCurve]; }
  getAlerts(): DrawdownAlert[] { return [...this.alerts]; }
  getCurrentDrawdown(): number {
    return this.peakEquity > 0 ? ((this.peakEquity - this.currentEquity) / this.peakEquity) * 100 : 0;
  }
  shouldHalt(maxDrawdownPercent: number): boolean { return this.getCurrentDrawdown() >= maxDrawdownPercent; }
  printReport(): void { printPerformanceReport(this.getSummary()); }

  reset(): void {
    this.equityCurve = [];
    this.alerts = [];
    this.triggeredThresholds.clear();
    this.currentEquity = this.config.initialEquity;
    this.peakEquity = this.config.initialEquity;
    this.troughEquity = this.config.initialEquity;
    this.cumulativePnl = 0;
    this.tradeCount = 0;
    this.winCount = 0;
    this.lossCount = 0;
    this.totalWinAmount = 0;
    this.totalLossAmount = 0;
    this.maxConsecutiveWins = 0;
    this.maxConsecutiveLosses = 0;
    this.currentStreak = 0;
    this.maxDrawdownPercent = 0;
    this.startTime = Date.now();
  }

  private checkDrawdownAlerts(currentDrawdown: number): void {
    for (const threshold of this.config.drawdownAlertThresholds) {
      if (currentDrawdown >= threshold && !this.triggeredThresholds.has(threshold)) {
        this.triggeredThresholds.add(threshold);
        const alert: DrawdownAlert = {
          timestamp: Date.now(), drawdownPercent: currentDrawdown,
          peakEquity: this.peakEquity, currentEquity: this.currentEquity, threshold: `${threshold}%`,
        };
        this.alerts.push(alert);
        logger.warn(`[ProfitTracker] ⚠️ DRAWDOWN ALERT: ${currentDrawdown.toFixed(2)}% (threshold: ${threshold}%)`);
        for (const listener of this.alertListeners) {
          try { listener(alert); } catch (err) {
            logger.error(`[ProfitTracker] Alert listener error: ${err instanceof Error ? err.message : String(err)}`);
          }
        }
      }
    }
  }
}
