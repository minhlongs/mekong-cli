/**
 * SpreadDetectorEngine — Unified multi-exchange spread detection + execution engine.
 * Integrates: ArbitrageScanner (detect) → SignalScorer (rank) → OrderBookAnalyzer (validate)
 *           → EmergencyCircuitBreaker (safety) → ArbitrageExecutor (execute)
 *           → SpreadHistoryTracker (learn) → ProfitTracker (track)
 *
 * Lifecycle: init() → start() → [detect→score→validate→execute loop] → stop()
 * Package version: uses IExchange interface, no app-specific dependencies.
 */

import { IExchange } from '@agencyos/trading-core/interfaces';
import { getArbLogger } from './arb-logger';
import {
  ArbitrageOpportunity, ScannerConfig, ExecutorConfig,
  ExecutionResult, ExchangeConfig,
} from './arbitrage-types';
import { ArbitrageScanner } from './arbitrage-scanner';
import { ArbitrageExecutor } from './arbitrage-executor';
import { ArbitrageSignalScorer, ScorerConfig, ScoredSignal, SignalFactors } from './signal-scorer';
import { OrderBookAnalyzer, OrderBook } from './order-book-analyzer';
import { EmergencyCircuitBreaker, CircuitBreakerConfig, CircuitState } from './emergency-circuit-breaker';
import { SpreadHistoryTracker, SpreadHistoryConfig, SpreadZScore } from './spread-history-tracker';
import { ProfitTracker } from './profit-tracker';
import { MultiExchangeConnector } from './multi-exchange-connector';

export const TARGET_EXCHANGES = ['binance', 'okx', 'bybit'] as const;
export type TargetExchange = typeof TARGET_EXCHANGES[number];

export interface SpreadDetectorConfig {
  exchanges: ExchangeConfig[];
  symbols: string[];
  scanner: Partial<ScannerConfig>;
  executor: Partial<ExecutorConfig>;
  scorer: Partial<ScorerConfig>;
  circuitBreaker: Partial<CircuitBreakerConfig>;
  spreadHistory: Partial<SpreadHistoryConfig>;
  initialEquity: number;
  maxOpportunitiesPerCycle: number;
  enableOrderBookValidation: boolean;
  enableSignalScoring: boolean;
  enableSpreadHistory: boolean;
  logIntervalMs: number;
  orderbookRefreshMs: number;
  /** Optional: provide IExchange factory for creating clients from ExchangeConfig */
  exchangeFactory?: (config: ExchangeConfig) => IExchange;
}

export interface DetectionEvent {
  opportunity: ArbitrageOpportunity;
  signal: ScoredSignal | null;
  zScore: SpreadZScore | null;
  orderbookFeasible: boolean;
  executed: boolean;
  result: ExecutionResult | null;
  reason: string;
  timestamp: number;
}

export interface EngineStats {
  status: 'idle' | 'running' | 'stopped' | 'halted';
  uptime: number;
  totalDetections: number;
  totalScored: number;
  totalExecuted: number;
  successfulExecutions: number;
  skippedByScorer: number;
  skippedByOrderbook: number;
  skippedByCircuitBreaker: number;
  circuitState: CircuitState;
  connectedExchanges: string[];
  avgDetectionLatencyMs: number;
}

const DEFAULT_CONFIG: SpreadDetectorConfig = {
  exchanges: [],
  symbols: ['BTC/USDT', 'ETH/USDT'],
  scanner: { pollIntervalMs: 2000, minSpreadPercent: 0.05 },
  executor: { maxPositionSizeUsd: 1000, maxConcurrentTrades: 3 },
  scorer: { executeThreshold: 65 },
  circuitBreaker: { maxDailyLossUsd: 100, maxConsecutiveLosses: 5 },
  spreadHistory: { maxRecordsPerPair: 1000 },
  initialEquity: 10000,
  maxOpportunitiesPerCycle: 5,
  enableOrderBookValidation: true,
  enableSignalScoring: true,
  enableSpreadHistory: true,
  logIntervalMs: 60000,
  orderbookRefreshMs: 5000,
};

export class SpreadDetectorEngine {
  private config: SpreadDetectorConfig;
  private connector: MultiExchangeConnector;
  private scanner: ArbitrageScanner;
  private executor: ArbitrageExecutor;
  private scorer: ArbitrageSignalScorer;
  private orderbook: OrderBookAnalyzer;
  private circuitBreaker: EmergencyCircuitBreaker;
  private spreadHistory: SpreadHistoryTracker;
  private profitTracker: ProfitTracker;

  private isRunning = false;
  private startTime = 0;
  private events: DetectionEvent[] = [];
  private logTimer: ReturnType<typeof setInterval> | null = null;
  private orderbookTimer: ReturnType<typeof setInterval> | null = null;
  private detectionLatencies: number[] = [];

  private stats: EngineStats = {
    status: 'idle',
    uptime: 0,
    totalDetections: 0,
    totalScored: 0,
    totalExecuted: 0,
    successfulExecutions: 0,
    skippedByScorer: 0,
    skippedByOrderbook: 0,
    skippedByCircuitBreaker: 0,
    circuitState: 'closed',
    connectedExchanges: [],
    avgDetectionLatencyMs: 0,
  };

  constructor(config?: Partial<SpreadDetectorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.connector = new MultiExchangeConnector();
    if (this.config.exchangeFactory) {
      this.connector.setFactory(this.config.exchangeFactory);
    }
    this.scanner = new ArbitrageScanner(this.config.scanner);
    this.executor = new ArbitrageExecutor(this.config.executor);
    this.scorer = new ArbitrageSignalScorer(this.config.scorer);
    this.orderbook = new OrderBookAnalyzer();
    this.circuitBreaker = new EmergencyCircuitBreaker(this.config.circuitBreaker);
    this.spreadHistory = new SpreadHistoryTracker(this.config.spreadHistory);
    this.profitTracker = new ProfitTracker({ initialEquity: this.config.initialEquity });
  }

  async init(): Promise<string[]> {
    const log = getArbLogger();
    log.info('[SpreadDetector] Initializing...');

    for (const ex of this.config.exchanges) {
      this.connector.addExchange(ex);
    }

    const connected = await this.connector.connectAll();
    this.stats.connectedExchanges = connected;

    if (connected.length < 2) {
      throw new Error(`SpreadDetector needs >=2 exchanges, only ${connected.length} connected`);
    }

    const clients = this.connector.getActiveClients();
    for (const [name, client] of clients) {
      this.scanner.addExchange(name, client);
      this.executor.addExchange(name, client);
    }

    this.scanner.onOpportunity((opp) => { this.handleDetection(opp); });

    log.info(`[SpreadDetector] Initialized: ${connected.length} exchanges (${connected.join(', ')}), ${this.config.symbols.length} symbols`);
    return connected;
  }

  async start(): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;
    this.startTime = Date.now();
    this.stats.status = 'running';

    this.connector.startHealthChecks();

    if (this.config.enableOrderBookValidation) {
      this.startOrderbookRefresh();
    }

    this.logTimer = setInterval(() => this.logDashboard(), this.config.logIntervalMs);
    await this.scanner.start();

    getArbLogger().info('[SpreadDetector] Engine STARTED');
  }

  stop(): void {
    this.isRunning = false;
    this.stats.status = 'stopped';
    this.scanner.stop();
    this.connector.stopHealthChecks();
    this.circuitBreaker.shutdown();

    if (this.logTimer) { clearInterval(this.logTimer); this.logTimer = null; }
    if (this.orderbookTimer) { clearInterval(this.orderbookTimer); this.orderbookTimer = null; }

    this.connector.shutdown();
    getArbLogger().info('[SpreadDetector] Engine STOPPED');
    this.logDashboard();
  }

  private async handleDetection(opp: ArbitrageOpportunity): Promise<void> {
    if (!this.isRunning) return;
    const startMs = Date.now();
    this.stats.totalDetections++;

    if (!this.circuitBreaker.isAllowed()) {
      this.stats.skippedByCircuitBreaker++;
      this.stats.circuitState = this.circuitBreaker.getState();
      this.recordEvent(opp, null, null, false, false, null, 'circuit_breaker_open');
      return;
    }

    let zScore: SpreadZScore | null = null;
    if (this.config.enableSpreadHistory) {
      this.spreadHistory.record({
        symbol: opp.symbol, buyExchange: opp.buyExchange,
        sellExchange: opp.sellExchange, spreadPercent: opp.spreadPercent,
        timestamp: opp.timestamp,
      });
      zScore = this.spreadHistory.getZScore(
        opp.buyExchange, opp.sellExchange, opp.symbol, opp.spreadPercent
      );
    }

    let signal: ScoredSignal | null = null;
    if (this.config.enableSignalScoring) {
      const liquidityScore = this.orderbook.hasOrderBook(opp.buyExchange, opp.symbol)
        ? this.orderbook.getLiquidityScore(opp.buyExchange, opp.symbol).score : 50;

      const factors: SignalFactors = {
        spreadPercent: opp.spreadPercent,
        netProfitPercent: opp.netProfitPercent,
        liquidityScore,
        latencyMs: opp.latency.buy + opp.latency.sell,
        feeCostPercent: (this.config.scanner.feeRatePerSide || 0.001) * 2 * 100,
        spreadZScore: zScore?.zScore || 0,
        fillable: true,
        exchangeHealthy: this.connector.isHealthy(opp.buyExchange) &&
                         this.connector.isHealthy(opp.sellExchange),
      };

      signal = this.scorer.score(factors);
      this.stats.totalScored++;

      if (signal.recommendation === 'skip') {
        this.stats.skippedByScorer++;
        this.recordEvent(opp, signal, zScore, false, false, null, `score_too_low: ${signal.totalScore}`);
        return;
      }
    }

    let orderbookFeasible = true;
    if (this.config.enableOrderBookValidation) {
      const positionUsd = Math.min(
        this.config.executor.maxPositionSizeUsd || 1000,
        opp.estimatedProfitUsd * 100
      );
      const amount = positionUsd / opp.buyPrice;

      if (this.orderbook.hasOrderBook(opp.buyExchange, opp.symbol) &&
          this.orderbook.hasOrderBook(opp.sellExchange, opp.symbol)) {
        const sim = this.orderbook.simulateArbitrageFill(
          opp.buyExchange, opp.sellExchange, opp.symbol,
          amount, this.config.scanner.feeRatePerSide || 0.001
        );
        orderbookFeasible = sim.feasible;

        if (!orderbookFeasible) {
          this.stats.skippedByOrderbook++;
          this.recordEvent(opp, signal, zScore, false, false, null,
            `orderbook_infeasible: slippage=${sim.totalSlippageBps.toFixed(1)}bps`);
          return;
        }
      }
    }

    if (this.stats.totalExecuted >= this.config.maxOpportunitiesPerCycle &&
        this.stats.successfulExecutions === 0) {
      this.recordEvent(opp, signal, zScore, orderbookFeasible, false, null, 'rate_limited');
      return;
    }

    this.stats.totalExecuted++;
    try {
      const result = await this.executor.execute(opp);
      this.profitTracker.recordTrade(result.actualProfitUsd);
      const tripped = this.circuitBreaker.recordTrade(result.actualProfitUsd);
      this.stats.circuitState = this.circuitBreaker.getState();

      if (tripped) {
        getArbLogger().warn('[SpreadDetector] Circuit breaker TRIPPED');
        this.stats.status = 'halted';
      }

      if (result.success) this.stats.successfulExecutions++;

      const latency = Date.now() - startMs;
      this.detectionLatencies.push(latency);
      if (this.detectionLatencies.length > 100) this.detectionLatencies.shift();

      this.recordEvent(opp, signal, zScore, orderbookFeasible, true, result,
        result.success ? 'executed_ok' : `execution_failed: ${result.error}`);
    } catch (err) {
      getArbLogger().error(`[SpreadDetector] Execution error: ${err instanceof Error ? err.message : String(err)}`);
      this.recordEvent(opp, signal, zScore, orderbookFeasible, false, null,
        `execution_error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  private startOrderbookRefresh(): void {
    this.orderbookTimer = setInterval(async () => {
      const clients = this.connector.getActiveClients();
      for (const [name, client] of clients) {
        for (const symbol of this.config.symbols) {
          try {
            const rawBook = await client.fetchOrderBook(symbol, 20);
            if (rawBook) {
              this.orderbook.updateOrderBook({
                exchange: name, symbol,
                bids: rawBook.bids, asks: rawBook.asks,
                timestamp: Date.now(),
              });
            }
          } catch { /* orderbook is optional enhancement */ }
        }
      }
    }, this.config.orderbookRefreshMs);
  }

  private recordEvent(
    opp: ArbitrageOpportunity, signal: ScoredSignal | null,
    zScore: SpreadZScore | null, orderbookFeasible: boolean,
    executed: boolean, result: ExecutionResult | null, reason: string
  ): void {
    this.events.push({ opportunity: opp, signal, zScore, orderbookFeasible, executed, result, reason, timestamp: Date.now() });
    if (this.events.length > 500) this.events.splice(0, this.events.length - 500);
  }

  private logDashboard(): void {
    const log = getArbLogger();
    const uptime = this.isRunning ? Date.now() - this.startTime : 0;
    this.stats.uptime = uptime;
    const avgLatency = this.detectionLatencies.length > 0
      ? this.detectionLatencies.reduce((a, b) => a + b, 0) / this.detectionLatencies.length : 0;
    this.stats.avgDetectionLatencyMs = avgLatency;
    const profitSummary = this.profitTracker.getSummary();

    log.info(`[SpreadDetector] Status=${this.stats.status} | Detections=${this.stats.totalDetections} | Executed=${this.stats.totalExecuted} | P&L=$${profitSummary.cumulativePnl.toFixed(2)}`);
  }

  getStats(): EngineStats {
    this.stats.uptime = this.isRunning ? Date.now() - this.startTime : 0;
    this.stats.circuitState = this.circuitBreaker.getState();
    return { ...this.stats };
  }

  getEvents(limit: number = 50): DetectionEvent[] { return this.events.slice(-limit); }
  getProfitSummary() { return this.profitTracker.getSummary(); }
  getSpreadStats() { return this.spreadHistory.getAllStats(); }
  getBestTradingHours(buyExchange: string, sellExchange: string, symbol: string) {
    return this.spreadHistory.getBestTradingHours(buyExchange, sellExchange, symbol);
  }
  getScoreDistribution() { return this.scorer.getGradeDistribution(); }
  getCircuitBreakerMetrics() { return this.circuitBreaker.getMetrics(); }

  emergencyStop(reason: string): void {
    this.circuitBreaker.manualTrip(reason);
    this.stats.status = 'halted';
    this.stats.circuitState = this.circuitBreaker.getState();
    getArbLogger().warn(`[SpreadDetector] EMERGENCY STOP: ${reason}`);
  }

  resume(): void {
    this.circuitBreaker.forceClose();
    this.stats.status = 'running';
    this.stats.circuitState = 'closed';
    getArbLogger().info('[SpreadDetector] Resumed trading');
  }

  resetDaily(): void {
    this.executor.resetDaily();
    this.circuitBreaker.resetDaily();
    this.stats.skippedByCircuitBreaker = 0;
  }

  updateOrderBook(book: OrderBook): void { this.orderbook.updateOrderBook(book); }
  isActive(): boolean { return this.isRunning; }

  getComponents() {
    return {
      connector: this.connector, scanner: this.scanner, executor: this.executor,
      scorer: this.scorer, orderbook: this.orderbook, circuitBreaker: this.circuitBreaker,
      spreadHistory: this.spreadHistory, profitTracker: this.profitTracker,
    };
  }
}
