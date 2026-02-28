/**
 * ArbitrageExecutor — Simultaneous cross-exchange trade execution.
 * Receives ArbitrageOpportunity from Scanner, executes buy+sell in parallel.
 * Includes: position limits, fee tracking, slippage guard, P&L dashboard.
 */

import { ExchangeClient } from '../execution/ExchangeClient';
import { IOrder } from '../interfaces/IExchange';
import { ArbitrageOpportunity } from './ArbitrageScanner';
import { logger } from '../utils/logger';

export interface ExecutionResult {
  opportunity: ArbitrageOpportunity;
  buyOrder: IOrder | null;
  sellOrder: IOrder | null;
  actualProfitUsd: number;
  totalFeesUsd: number;
  executionTimeMs: number;
  slippageBps: { buy: number; sell: number };
  success: boolean;
  error?: string;
}

export interface ArbitrageTradeLog {
  id: number;
  timestamp: number;
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  amount: number;
  grossProfitUsd: number;
  feesUsd: number;
  netProfitUsd: number;
  executionTimeMs: number;
}

export interface PnLDashboard {
  totalTrades: number;
  successfulTrades: number;
  failedTrades: number;
  totalProfitUsd: number;
  totalFeesUsd: number;
  netProfitUsd: number;
  avgExecutionMs: number;
  bestTradeUsd: number;
  worstTradeUsd: number;
  winRate: number;
  profitFactor: number;
  activePositionValue: number;
}

export interface ExecutorConfig {
  maxPositionSizeUsd: number;    // Max USD per arbitrage trade (default: 1000)
  maxConcurrentTrades: number;   // Max simultaneous open arb trades (default: 3)
  maxSlippageBps: number;        // Abort if slippage > this (default: 20)
  feeRatePerSide: number;        // Fee per side (default: 0.001 = 0.1%)
  minNetProfitUsd: number;       // Min expected net profit to execute (default: 1)
  maxDailyLossUsd: number;       // Kill switch: max daily loss (default: 50)
  cooldownMs: number;            // Min ms between trades on same pair (default: 5000)
}

const DEFAULT_CONFIG: ExecutorConfig = {
  maxPositionSizeUsd: 1000,
  maxConcurrentTrades: 3,
  maxSlippageBps: 20,
  feeRatePerSide: 0.001,
  minNetProfitUsd: 1,
  maxDailyLossUsd: 50,
  cooldownMs: 5000,
};

export class ArbitrageExecutor {
  private config: ExecutorConfig;
  private exchanges: Map<string, ExchangeClient> = new Map();
  private tradeLog: ArbitrageTradeLog[] = [];
  private activeTrades = 0;
  private dailyPnL = 0;
  private lastTradeTime: Map<string, number> = new Map(); // symbol → last trade timestamp
  private tradeCounter = 0;

  constructor(config?: Partial<ExecutorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** Register an exchange client */
  addExchange(name: string, client: ExchangeClient): void {
    this.exchanges.set(name, client);
  }

  /**
   * Execute an arbitrage opportunity: buy on cheap exchange, sell on expensive exchange.
   * Both orders are sent simultaneously for minimum latency.
   */
  async execute(opp: ArbitrageOpportunity): Promise<ExecutionResult> {
    const startMs = Date.now();

    // Pre-flight checks
    const checkResult = this.preFlightChecks(opp);
    if (checkResult) {
      return this.failedResult(opp, checkResult, startMs);
    }

    const buyClient = this.exchanges.get(opp.buyExchange);
    const sellClient = this.exchanges.get(opp.sellExchange);

    if (!buyClient || !sellClient) {
      return this.failedResult(opp, `exchange_not_found: ${!buyClient ? opp.buyExchange : opp.sellExchange}`, startMs);
    }

    // Calculate position size
    const positionUsd = Math.min(this.config.maxPositionSizeUsd, opp.estimatedProfitUsd * 100);
    const amount = positionUsd / opp.buyPrice;

    if (amount <= 0) {
      return this.failedResult(opp, 'invalid_position_size', startMs);
    }

    this.activeTrades++;

    try {
      // Execute both sides simultaneously for minimum latency
      const [buyResult, sellResult] = await Promise.allSettled([
        buyClient.createMarketOrder(opp.symbol, 'buy', amount),
        sellClient.createMarketOrder(opp.symbol, 'sell', amount),
      ]);

      const buyOrder = buyResult.status === 'fulfilled' ? buyResult.value : null;
      const sellOrder = sellResult.status === 'fulfilled' ? sellResult.value : null;

      const executionTimeMs = Date.now() - startMs;

      // Calculate actual slippage
      const buySlippage = buyOrder ? Math.abs(buyOrder.price - opp.buyPrice) / opp.buyPrice * 10000 : 0;
      const sellSlippage = sellOrder ? Math.abs(sellOrder.price - opp.sellPrice) / opp.sellPrice * 10000 : 0;

      // Slippage guard: warn if excessive
      if (buySlippage > this.config.maxSlippageBps || sellSlippage > this.config.maxSlippageBps) {
        logger.warn(`[ArbExecutor] High slippage detected: buy=${buySlippage.toFixed(1)}bps, sell=${sellSlippage.toFixed(1)}bps`);
      }

      // Calculate actual P&L
      let actualProfitUsd = 0;
      let totalFeesUsd = 0;

      if (buyOrder && sellOrder) {
        const grossProfit = (sellOrder.price - buyOrder.price) * Math.min(buyOrder.amount, sellOrder.amount);
        const buyFee = buyOrder.price * buyOrder.amount * this.config.feeRatePerSide;
        const sellFee = sellOrder.price * sellOrder.amount * this.config.feeRatePerSide;
        totalFeesUsd = buyFee + sellFee;
        actualProfitUsd = grossProfit - totalFeesUsd;
      }

      // Log trade
      this.logTrade(opp, amount, actualProfitUsd, totalFeesUsd, executionTimeMs);

      // Update daily P&L
      this.dailyPnL += actualProfitUsd;
      this.lastTradeTime.set(opp.symbol, Date.now());

      const success = buyOrder !== null && sellOrder !== null;

      if (success) {
        logger.info(
          `[ArbExecutor] ✅ ${opp.symbol}: BUY@${opp.buyExchange}=$${buyOrder!.price.toFixed(2)} SELL@${opp.sellExchange}=$${sellOrder!.price.toFixed(2)} ` +
          `P&L: $${actualProfitUsd.toFixed(2)} (${executionTimeMs}ms)`
        );
      } else {
        const buyErr = buyResult.status === 'rejected' ? (buyResult.reason as Error).message : '';
        const sellErr = sellResult.status === 'rejected' ? (sellResult.reason as Error).message : '';
        logger.error(`[ArbExecutor] ❌ Partial fill: buy=${buyErr || 'OK'}, sell=${sellErr || 'OK'}`);
      }

      return {
        opportunity: opp,
        buyOrder,
        sellOrder,
        actualProfitUsd,
        totalFeesUsd,
        executionTimeMs,
        slippageBps: { buy: buySlippage, sell: sellSlippage },
        success,
        error: success ? undefined : 'partial_fill',
      };
    } catch (err) {
      return this.failedResult(opp, err instanceof Error ? err.message : String(err), startMs);
    } finally {
      this.activeTrades--;
    }
  }

  /**
   * Pre-flight checks before execution.
   * Returns error string if check fails, null if all clear.
   */
  private preFlightChecks(opp: ArbitrageOpportunity): string | null {
    // Max concurrent trades
    if (this.activeTrades >= this.config.maxConcurrentTrades) {
      return `max_concurrent_${this.config.maxConcurrentTrades}_reached`;
    }

    // Daily loss limit
    if (this.dailyPnL <= -this.config.maxDailyLossUsd) {
      return `daily_loss_limit_${this.config.maxDailyLossUsd}_hit`;
    }

    // Min profit threshold
    if (opp.estimatedProfitUsd < this.config.minNetProfitUsd) {
      return `profit_$${opp.estimatedProfitUsd.toFixed(2)}_below_min_$${this.config.minNetProfitUsd}`;
    }

    // Cooldown per symbol
    const lastTrade = this.lastTradeTime.get(opp.symbol);
    if (lastTrade && (Date.now() - lastTrade) < this.config.cooldownMs) {
      return 'cooldown_active';
    }

    return null;
  }

  /** Log a completed trade */
  private logTrade(
    opp: ArbitrageOpportunity,
    amount: number,
    netProfit: number,
    fees: number,
    execMs: number
  ): void {
    this.tradeLog.push({
      id: ++this.tradeCounter,
      timestamp: Date.now(),
      symbol: opp.symbol,
      buyExchange: opp.buyExchange,
      sellExchange: opp.sellExchange,
      buyPrice: opp.buyPrice,
      sellPrice: opp.sellPrice,
      amount,
      grossProfitUsd: netProfit + fees,
      feesUsd: fees,
      netProfitUsd: netProfit,
      executionTimeMs: execMs,
    });
  }

  /** Get P&L dashboard summary */
  getDashboard(): PnLDashboard {
    const trades = this.tradeLog;
    const successful = trades.filter(t => t.netProfitUsd > 0);
    const totalProfit = trades.reduce((s, t) => s + (t.netProfitUsd > 0 ? t.netProfitUsd : 0), 0);
    const totalLoss = Math.abs(trades.reduce((s, t) => s + (t.netProfitUsd < 0 ? t.netProfitUsd : 0), 0));

    return {
      totalTrades: trades.length,
      successfulTrades: successful.length,
      failedTrades: trades.length - successful.length,
      totalProfitUsd: trades.reduce((s, t) => s + Math.max(0, t.netProfitUsd), 0),
      totalFeesUsd: trades.reduce((s, t) => s + t.feesUsd, 0),
      netProfitUsd: trades.reduce((s, t) => s + t.netProfitUsd, 0),
      avgExecutionMs: trades.length > 0 ? trades.reduce((s, t) => s + t.executionTimeMs, 0) / trades.length : 0,
      bestTradeUsd: trades.length > 0 ? Math.max(...trades.map(t => t.netProfitUsd)) : 0,
      worstTradeUsd: trades.length > 0 ? Math.min(...trades.map(t => t.netProfitUsd)) : 0,
      winRate: trades.length > 0 ? (successful.length / trades.length) * 100 : 0,
      profitFactor: totalLoss > 0 ? totalProfit / totalLoss : totalProfit > 0 ? Infinity : 0,
      activePositionValue: 0, // TODO: track from open orders
    };
  }

  /** Get full trade log */
  getTradeLog(): ArbitrageTradeLog[] {
    return [...this.tradeLog];
  }

  /** Reset daily P&L (call at start of each trading day) */
  resetDaily(): void {
    this.dailyPnL = 0;
    logger.info('[ArbExecutor] Daily P&L reset');
  }

  /** Print formatted dashboard to logger */
  printDashboard(): void {
    const d = this.getDashboard();
    logger.info('\n=== ARB P&L DASHBOARD ===');
    logger.info(`Trades:     ${d.totalTrades} (${d.successfulTrades} wins / ${d.failedTrades} losses)`);
    logger.info(`Win Rate:   ${d.winRate.toFixed(1)}%`);
    logger.info(`Net P&L:    $${d.netProfitUsd.toFixed(2)}`);
    logger.info(`Fees Paid:  $${d.totalFeesUsd.toFixed(2)}`);
    logger.info(`Profit Factor: ${d.profitFactor === Infinity ? '∞' : d.profitFactor.toFixed(2)}`);
    logger.info(`Best Trade: $${d.bestTradeUsd.toFixed(2)}`);
    logger.info(`Worst Trade: $${d.worstTradeUsd.toFixed(2)}`);
    logger.info(`Avg Exec:   ${d.avgExecutionMs.toFixed(0)}ms`);
    logger.info(`Daily P&L:  $${this.dailyPnL.toFixed(2)}`);
    logger.info('=========================\n');
  }

  private failedResult(opp: ArbitrageOpportunity, error: string, startMs: number): ExecutionResult {
    logger.warn(`[ArbExecutor] Skipped ${opp.symbol}: ${error}`);
    return {
      opportunity: opp,
      buyOrder: null,
      sellOrder: null,
      actualProfitUsd: 0,
      totalFeesUsd: 0,
      executionTimeMs: Date.now() - startMs,
      slippageBps: { buy: 0, sell: 0 },
      success: false,
      error,
    };
  }
}
