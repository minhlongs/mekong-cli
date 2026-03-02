/**
 * Arbitrage Execution Engine — Wires RealtimeArbitrageScanner → CircuitBreaker
 * → AtomicCrossExchangeOrderExecutor → position tracking → Telegram alerts.
 * Manages cooldowns, max concurrent executions, and cumulative metrics.
 */

import { EventEmitter } from 'events';
import { logger } from '../utils/logger';
import type { ArbitrageOpportunity } from './realtime-arbitrage-scanner';
import { AtomicCrossExchangeOrderExecutor, type AtomicExecutionResult } from './atomic-cross-exchange-order-executor';
import { AdaptiveCircuitBreaker } from './adaptive-circuit-breaker-per-exchange';
import { AntiDetectionSafetyLayer } from './anti-detection-order-randomizer-safety-layer';
import { BinhPhapStealthStrategy } from './binh-phap-stealth-trading-strategy';
import type { IExchange } from '../interfaces/IExchange';

export interface ArbEngineConfig {
  /** Cooldown per pair after execution (ms). Default 30_000 */
  cooldownMs?: number;
  /** Max concurrent executions. Default 3 */
  maxConcurrent?: number;
  /** Position size in base asset. Default 0.01 */
  positionSizeBase?: number;
  /** Dry run mode — log but don't execute. Default true */
  dryRun?: boolean;
  /** Max daily loss USD before halting. Default 100 */
  maxDailyLossUsd?: number;
  /** Enable anti-detection stealth layer. Default true for live, false for dry-run */
  enableStealth?: boolean;
}

export interface ArbTradeRecord {
  id: string;
  opportunity: ArbitrageOpportunity;
  result: AtomicExecutionResult;
  executedAt: number;
}

export interface ArbEngineMetrics {
  totalExecutions: number;
  successfulTrades: number;
  failedTrades: number;
  totalPnlUsd: number;
  winRate: number;
  avgLatencyMs: number;
  dailyPnlUsd: number;
  halted: boolean;
}

export class ArbitrageExecutionEngine extends EventEmitter {
  private readonly config: Required<ArbEngineConfig>;
  private readonly executor: AtomicCrossExchangeOrderExecutor;
  private readonly circuitBreaker: AdaptiveCircuitBreaker;
  private readonly safetyLayer: AntiDetectionSafetyLayer;
  private readonly stealthStrategy: BinhPhapStealthStrategy;
  private readonly exchanges: Map<string, IExchange>;
  private cooldowns = new Map<string, number>(); // key: "buy:sell:symbol" → cooldown expiry
  private activeCount = 0;
  private tradeHistory: ArbTradeRecord[] = [];
  private latencySum = 0;
  private dailyPnl = 0;
  private dailyResetDate = new Date().toDateString();
  private halted = false;
  private tradeCounter = 0;

  constructor(
    config: ArbEngineConfig,
    exchanges: Map<string, IExchange>,
    circuitBreaker: AdaptiveCircuitBreaker,
  ) {
    super();
    const enableStealth = config.enableStealth ?? !(config.dryRun ?? true);
    this.config = {
      cooldownMs: config.cooldownMs ?? 30_000,
      maxConcurrent: config.maxConcurrent ?? 3,
      positionSizeBase: config.positionSizeBase ?? 0.01,
      dryRun: config.dryRun ?? true,
      maxDailyLossUsd: config.maxDailyLossUsd ?? 100,
      enableStealth,
    };
    this.exchanges = exchanges;
    this.circuitBreaker = circuitBreaker;
    this.safetyLayer = new AntiDetectionSafetyLayer();
    this.stealthStrategy = new BinhPhapStealthStrategy();
    this.executor = new AtomicCrossExchangeOrderExecutor();
  }

  /** Process an arbitrage opportunity — returns true if executed */
  async processOpportunity(opp: ArbitrageOpportunity): Promise<boolean> {
    // Daily reset check
    const today = new Date().toDateString();
    if (today !== this.dailyResetDate) {
      this.dailyPnl = 0;
      this.dailyResetDate = today;
      this.halted = false;
    }

    // Safety checks
    if (this.halted) {
      logger.warn('[ArbEngine] Halted — daily loss limit reached');
      return false;
    }

    const spread = opp.spread;
    const pairKey = `${spread.buyExchange}:${spread.sellExchange}:${spread.symbol}`;

    // Cooldown check
    const cooldownExpiry = this.cooldowns.get(pairKey) ?? 0;
    if (Date.now() < cooldownExpiry) {
      return false;
    }

    // Concurrent limit
    if (this.activeCount >= this.config.maxConcurrent) {
      return false;
    }

    // Circuit breaker check
    const buyKey = AdaptiveCircuitBreaker.key(spread.buyExchange, spread.symbol);
    const sellKey = AdaptiveCircuitBreaker.key(spread.sellExchange, spread.symbol);
    if (!this.circuitBreaker.isAllowed(buyKey) || !this.circuitBreaker.isAllowed(sellKey)) {
      logger.info(`[ArbEngine] Circuit breaker blocked: ${pairKey}`);
      return false;
    }

    // Dry run mode
    if (this.config.dryRun) {
      const record = this.createDryRunRecord(opp);
      this.tradeHistory.push(record);
      this.dailyPnl += spread.estimatedProfitUsd;
      this.emit('trade', record);
      logger.info(`[ArbEngine] DRY-RUN: ${spread.symbol} buy@${spread.buyExchange} sell@${spread.sellExchange} spread=${(spread.netSpreadPct * 100).toFixed(3)}%`);
      this.cooldowns.set(pairKey, Date.now() + this.config.cooldownMs);
      return true;
    }

    // Live execution
    const buyExchange = this.exchanges.get(spread.buyExchange);
    const sellExchange = this.exchanges.get(spread.sellExchange);
    if (!buyExchange || !sellExchange) {
      logger.error(`[ArbEngine] Exchange not found: ${spread.buyExchange} or ${spread.sellExchange}`);
      return false;
    }

    // Anti-detection stealth layer (active for live trading)
    let stealthSize = this.config.positionSizeBase;
    if (this.config.enableStealth) {
      if (!this.safetyLayer.shouldProceed(spread.buyExchange)
        || !this.safetyLayer.shouldProceed(spread.sellExchange)) {
        logger.info(`[ArbEngine] Anti-detection paused: ${spread.buyExchange}/${spread.sellExchange}`);
        return false;
      }

      const stealthPlan = this.stealthStrategy.planExecution(
        spread.buyExchange, this.config.positionSizeBase, spread.symbol,
      );
      if (!stealthPlan.shouldProceed) {
        logger.info(`[ArbEngine] Stealth plan blocked: ${spread.symbol} on ${spread.buyExchange}`);
        return false;
      }

      // Apply stealth delay (timing randomization to avoid pattern detection)
      if (stealthPlan.delayMs > 0) {
        await new Promise((r) => setTimeout(r, stealthPlan.delayMs));
      }

      // Randomize order size (±5% to avoid uniform size detection)
      stealthSize = this.safetyLayer.randomizeSize(this.config.positionSizeBase);
    }

    this.activeCount++;
    // Apply randomized cooldown (stealth) or fixed cooldown
    const jitteredCooldown = this.config.enableStealth
      ? this.safetyLayer.randomizeDelay(this.config.cooldownMs)
      : this.config.cooldownMs;
    this.cooldowns.set(pairKey, Date.now() + jitteredCooldown);

    try {
      const result = await this.executor.executeAtomic({
        symbol: spread.symbol,
        amount: stealthSize,
        buyExchange,
        sellExchange,
      });

      this.latencySum += result.totalLatency;
      const record = this.createTradeRecord(opp, result);
      this.tradeHistory.push(record);
      this.dailyPnl += result.netPnl;

      // Record API call for anti-detection rate tracking
      if (this.config.enableStealth) {
        this.safetyLayer.recordCall(spread.buyExchange);
        this.safetyLayer.recordCall(spread.sellExchange);
      }

      // Circuit breaker feedback
      if (result.success) {
        this.circuitBreaker.recordSuccess(buyKey);
        this.circuitBreaker.recordSuccess(sellKey);
        this.circuitBreaker.recordLatency(buyKey, result.buyLatency);
        this.circuitBreaker.recordLatency(sellKey, result.sellLatency);
      } else {
        this.circuitBreaker.recordFailure(buyKey);
        this.circuitBreaker.recordFailure(sellKey);
      }

      // Check daily loss limit
      if (this.dailyPnl < -this.config.maxDailyLossUsd) {
        this.halted = true;
        logger.warn(`[ArbEngine] HALTED — daily loss $${this.dailyPnl.toFixed(2)} exceeds limit $${this.config.maxDailyLossUsd}`);
        this.emit('halted', { dailyPnl: this.dailyPnl });
      }

      this.emit('trade', record);
      return result.success;
    } catch (err) {
      logger.error(`[ArbEngine] Execution error: ${err instanceof Error ? err.message : String(err)}`);
      this.circuitBreaker.recordFailure(buyKey);
      this.circuitBreaker.recordFailure(sellKey);
      return false;
    } finally {
      this.activeCount--;
    }
  }

  getMetrics(): ArbEngineMetrics {
    const successful = this.tradeHistory.filter(t => t.result.success).length;
    const total = this.tradeHistory.length;
    const totalPnl = this.tradeHistory.reduce((sum, t) => sum + t.result.netPnl, 0);
    const avgLatency = total > 0 ? this.latencySum / total : 0;

    return {
      totalExecutions: total,
      successfulTrades: successful,
      failedTrades: total - successful,
      totalPnlUsd: totalPnl,
      winRate: total > 0 ? successful / total : 0,
      avgLatencyMs: avgLatency,
      dailyPnlUsd: this.dailyPnl,
      halted: this.halted,
    };
  }

  getTradeHistory(): ArbTradeRecord[] {
    return [...this.tradeHistory];
  }

  isHalted(): boolean {
    return this.halted;
  }

  /** Reset halt and daily counters */
  resetHalt(): void {
    this.halted = false;
    this.dailyPnl = 0;
  }

  private createTradeRecord(opp: ArbitrageOpportunity, result: AtomicExecutionResult): ArbTradeRecord {
    this.tradeCounter++;
    return {
      id: `arb-${this.tradeCounter}-${Date.now()}`,
      opportunity: opp,
      result,
      executedAt: Date.now(),
    };
  }

  private createDryRunRecord(opp: ArbitrageOpportunity): ArbTradeRecord {
    this.tradeCounter++;
    return {
      id: `arb-dry-${this.tradeCounter}-${Date.now()}`,
      opportunity: opp,
      result: {
        success: true,
        buyLatency: 0,
        sellLatency: 0,
        totalLatency: 0,
        netPnl: opp.spread.estimatedProfitUsd,
        rollbackPerformed: false,
      },
      executedAt: Date.now(),
    };
  }
}
