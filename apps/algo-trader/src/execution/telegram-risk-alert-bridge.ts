/**
 * Bridges ProductionRiskGate events to TelegramTradeAlertBot.
 * Listens for risk gate decisions and sends alerts on rejections/trips.
 */

import { TelegramTradeAlertBot } from './telegram-trade-alert-bot';
import { ProductionRiskGate, type RiskCheckResult } from '../core/production-risk-gate';
import { logger } from '../utils/logger';

export interface TelegramRiskBridgeConfig {
  /** Send alert on every rejected trade (can be noisy) */
  alertOnReject?: boolean;
  /** Send daily summary at this UTC hour (0-23), default 0 (midnight) */
  dailySummaryHour?: number;
}

/**
 * Wire risk gate checks to Telegram alerts.
 * Call reportTradeCheck() after every canTrade() call.
 */
export class TelegramRiskAlertBridge {
  private bot: TelegramTradeAlertBot;
  private gate: ProductionRiskGate;
  private config: TelegramRiskBridgeConfig;
  private lastKillSwitchAlert = 0;
  private dailySummaryTimer: ReturnType<typeof setInterval> | null = null;

  constructor(bot: TelegramTradeAlertBot, gate: ProductionRiskGate, config?: TelegramRiskBridgeConfig) {
    this.bot = bot;
    this.gate = gate;
    this.config = { alertOnReject: false, dailySummaryHour: 0, ...config };
  }

  /** Call after canTrade() — sends alerts for risk events */
  reportTradeCheck(result: RiskCheckResult, context?: string): void {
    if (result.allowed) return;

    // Kill switch gets special high-priority alert (dedupe 60s)
    if (result.checks.killSwitch) {
      const now = Date.now();
      if (now - this.lastKillSwitchAlert > 60000) {
        this.bot.alertKillSwitch(result.reason || 'Unknown');
        this.lastKillSwitchAlert = now;
      }
      return;
    }

    // Circuit breaker alerts
    if (result.checks.drawdown) {
      this.bot.alertCircuitBreaker('Drawdown', result.reason || '');
    } else if (result.checks.dailyLoss) {
      this.bot.alertCircuitBreaker('Daily Loss', result.reason || '');
    } else if (result.checks.consecutiveLoss) {
      this.bot.alertCircuitBreaker('Consecutive Loss', result.reason || '');
    }

    // Optional: alert on every rejection
    if (this.config.alertOnReject && !result.checks.rateLimit) {
      this.bot.alertAnomaly('Trade Rejected', `${result.reason}${context ? ` | ${context}` : ''}`);
    }
  }

  /** Start daily summary timer */
  startDailySummary(): void {
    // Check every hour if it's time for summary
    this.dailySummaryTimer = setInterval(() => {
      const hour = new Date().getUTCHours();
      if (hour === this.config.dailySummaryHour) {
        const status = this.gate.getStatus();
        this.bot.alertPortfolioStatus(status.portfolioValue, status.dailyPnl, status.drawdownPct);
      }
    }, 3600000);
    this.dailySummaryTimer.unref();
  }

  stop(): void {
    if (this.dailySummaryTimer) {
      clearInterval(this.dailySummaryTimer);
      this.dailySummaryTimer = null;
    }
  }
}
