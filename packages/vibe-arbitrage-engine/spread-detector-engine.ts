/**
 * SpreadDetectorEngine — Unified multi-exchange spread detection + execution engine.
 */

import { getArbLogger } from './arb-logger';
import { ArbitrageOpportunity, ExecutionResult } from './arbitrage-types';
import { ArbitrageScanner } from './arbitrage-scanner';
import { ArbitrageExecutor } from './arbitrage-executor';
import { ArbitrageSignalScorer, ScoredSignal } from './signal-scorer';
import { OrderBookAnalyzer, OrderBook } from './order-book-analyzer';
import { EmergencyCircuitBreaker } from './emergency-circuit-breaker';
import { SpreadHistoryTracker, SpreadZScore } from './spread-history-tracker';
import { ProfitTracker } from './profit-tracker';
import { MultiExchangeConnector } from './multi-exchange-connector';
import {
  SpreadDetectorConfig, DetectionEvent, EngineStats, DEFAULT_SPREAD_DETECTOR_CONFIG,
} from './spread-detector-types';
import {
  evaluateDetectionSignal, validateOrderbookFeasibility, refreshOrderBooksOnce,
} from './spread-detector-helpers';

export * from './spread-detector-types';
export * from './spread-detector-helpers';

export class SpreadDetectorEngine {
  private config: SpreadDetectorConfig;
  private connector = new MultiExchangeConnector();
  private scanner: ArbitrageScanner;
  private executor: ArbitrageExecutor;
  private scorer: ArbitrageSignalScorer;
  private orderbook = new OrderBookAnalyzer();
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
    status: 'idle', uptime: 0, totalDetections: 0, totalScored: 0, totalExecuted: 0,
    successfulExecutions: 0, skippedByScorer: 0, skippedByOrderbook: 0,
    skippedByCircuitBreaker: 0, circuitState: 'closed', connectedExchanges: [], avgDetectionLatencyMs: 0,
  };

  constructor(config?: Partial<SpreadDetectorConfig>) {
    this.config = { ...DEFAULT_SPREAD_DETECTOR_CONFIG, ...config };
    if (this.config.exchangeFactory) this.connector.setFactory(this.config.exchangeFactory);
    this.scanner = new ArbitrageScanner(this.config.scanner);
    this.executor = new ArbitrageExecutor(this.config.executor);
    this.scorer = new ArbitrageSignalScorer(this.config.scorer);
    this.circuitBreaker = new EmergencyCircuitBreaker(this.config.circuitBreaker);
    this.spreadHistory = new SpreadHistoryTracker(this.config.spreadHistory);
    this.profitTracker = new ProfitTracker({ initialEquity: this.config.initialEquity });
  }

  async init(): Promise<string[]> {
    getArbLogger().info('[SpreadDetector] Initializing...');
    for (const ex of this.config.exchanges) this.connector.addExchange(ex);
    const connected = await this.connector.connectAll();
    this.stats.connectedExchanges = connected;
    if (connected.length < 2) throw new Error(`SpreadDetector needs >=2 exchanges, only ${connected.length} connected`);
    for (const [name, client] of this.connector.getActiveClients()) {
      this.scanner.addExchange(name, client);
      this.executor.addExchange(name, client);
    }
    this.scanner.onOpportunity((opp) => { this.handleDetection(opp); });
    getArbLogger().info(`[SpreadDetector] Initialized: ${connected.length} exchanges (${connected.join(', ')}), ${this.config.symbols.length} symbols`);
    return connected;
  }

  async start(): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;
    this.startTime = Date.now();
    this.stats.status = 'running';
    this.connector.startHealthChecks();
    if (this.config.enableOrderBookValidation) {
      this.orderbookTimer = setInterval(() => refreshOrderBooksOnce(this.connector, this.orderbook, this.config.symbols), this.config.orderbookRefreshMs);
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
      return this.recordEvent(opp, null, null, false, false, null, 'circuit_breaker_open');
    }
    let zScore: SpreadZScore | null = null;
    if (this.config.enableSpreadHistory) {
      this.spreadHistory.record({ symbol: opp.symbol, buyExchange: opp.buyExchange, sellExchange: opp.sellExchange, spreadPercent: opp.spreadPercent, timestamp: opp.timestamp });
      zScore = this.spreadHistory.getZScore(opp.buyExchange, opp.sellExchange, opp.symbol, opp.spreadPercent);
    }
    let signal: ScoredSignal | null = null;
    if (this.config.enableSignalScoring) {
      signal = evaluateDetectionSignal(opp, this.config, this.orderbook, this.connector, this.scorer, zScore);
      this.stats.totalScored++;
      if (signal.recommendation === 'skip') {
        this.stats.skippedByScorer++;
        return this.recordEvent(opp, signal, zScore, false, false, null, `score_too_low: ${signal.totalScore}`);
      }
    }
    let orderbookFeasible = true;
    if (this.config.enableOrderBookValidation) {
      const check = validateOrderbookFeasibility(opp, this.config, this.orderbook);
      orderbookFeasible = check.feasible;
      if (!orderbookFeasible) {
        this.stats.skippedByOrderbook++;
        return this.recordEvent(opp, signal, zScore, false, false, null, `orderbook_infeasible: slippage=${check.slippageBps.toFixed(1)}bps`);
      }
    }
    if (this.stats.totalExecuted >= this.config.maxOpportunitiesPerCycle && this.stats.successfulExecutions === 0) {
      return this.recordEvent(opp, signal, zScore, orderbookFeasible, false, null, 'rate_limited');
    }
    await this.executeOpportunity(opp, signal, zScore, orderbookFeasible, startMs);
  }

  private async executeOpportunity(opp: ArbitrageOpportunity, signal: ScoredSignal | null, zScore: SpreadZScore | null, orderbookFeasible: boolean, startMs: number): Promise<void> {
    this.stats.totalExecuted++;
    try {
      const result = await this.executor.execute(opp);
      this.profitTracker.recordTrade(result.actualProfitUsd);
      if (this.circuitBreaker.recordTrade(result.actualProfitUsd)) { getArbLogger().warn('[SpreadDetector] Circuit breaker TRIPPED'); this.stats.status = 'halted'; }
      this.stats.circuitState = this.circuitBreaker.getState();
      if (result.success) this.stats.successfulExecutions++;
      this.detectionLatencies.push(Date.now() - startMs);
      if (this.detectionLatencies.length > 100) this.detectionLatencies.shift();
      this.recordEvent(opp, signal, zScore, orderbookFeasible, true, result, result.success ? 'executed_ok' : `execution_failed: ${result.error}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      getArbLogger().error(`[SpreadDetector] Execution error: ${msg}`);
      this.recordEvent(opp, signal, zScore, orderbookFeasible, false, null, `execution_error: ${msg}`);
    }
  }

  private recordEvent(opp: ArbitrageOpportunity, signal: ScoredSignal | null, zScore: SpreadZScore | null, orderbookFeasible: boolean, executed: boolean, result: ExecutionResult | null, reason: string): void {
    this.events.push({ opportunity: opp, signal, zScore, orderbookFeasible, executed, result, reason, timestamp: Date.now() });
    if (this.events.length > 500) this.events.splice(0, this.events.length - 500);
  }

  private logDashboard(): void {
    this.stats.uptime = this.isRunning ? Date.now() - this.startTime : 0;
    this.stats.avgDetectionLatencyMs = this.detectionLatencies.length > 0 ? this.detectionLatencies.reduce((a, b) => a + b, 0) / this.detectionLatencies.length : 0;
    const profit = this.profitTracker.getSummary();
    getArbLogger().info(`[SpreadDetector] Status=${this.stats.status} | Detections=${this.stats.totalDetections} | Executed=${this.stats.totalExecuted} | P&L=$${profit.cumulativePnl.toFixed(2)}`);
  }

  getStats(): EngineStats { this.stats.uptime = this.isRunning ? Date.now() - this.startTime : 0; this.stats.circuitState = this.circuitBreaker.getState(); return { ...this.stats }; }
  getEvents(limit: number = 50): DetectionEvent[] { return this.events.slice(-limit); }
  getProfitSummary() { return this.profitTracker.getSummary(); }
  getSpreadStats() { return this.spreadHistory.getAllStats(); }
  getBestTradingHours(buyExchange: string, sellExchange: string, symbol: string) { return this.spreadHistory.getBestTradingHours(buyExchange, sellExchange, symbol); }
  getScoreDistribution() { return this.scorer.getGradeDistribution(); }
  getCircuitBreakerMetrics() { return this.circuitBreaker.getMetrics(); }
  emergencyStop(reason: string): void { this.circuitBreaker.manualTrip(reason); this.stats.status = 'halted'; this.stats.circuitState = this.circuitBreaker.getState(); getArbLogger().warn(`[SpreadDetector] EMERGENCY STOP: ${reason}`); }
  resume(): void { this.circuitBreaker.forceClose(); this.stats.status = 'running'; this.stats.circuitState = 'closed'; getArbLogger().info('[SpreadDetector] Resumed trading'); }
  resetDaily(): void { this.executor.resetDaily(); this.circuitBreaker.resetDaily(); this.stats.skippedByCircuitBreaker = 0; }
  updateOrderBook(book: OrderBook): void { this.orderbook.updateOrderBook(book); }
  isActive(): boolean { return this.isRunning; }
  getComponents() { return { connector: this.connector, scanner: this.scanner, executor: this.executor, scorer: this.scorer, orderbook: this.orderbook, circuitBreaker: this.circuitBreaker, spreadHistory: this.spreadHistory, profitTracker: this.profitTracker }; }
}
