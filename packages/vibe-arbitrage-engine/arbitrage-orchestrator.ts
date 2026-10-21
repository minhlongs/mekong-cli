/**
 * ArbitrageOrchestrator — Infinite-loop engine connecting all arbitrage components.
 */

import { getArbLogger } from './arb-logger';
import { ExecutionResult, ArbitrageOpportunity } from './arbitrage-types';
import { MultiExchangeConnector } from './multi-exchange-connector';
import { RealTimePriceAggregator } from './real-time-price-aggregator';
import { ArbitrageScanner } from './arbitrage-scanner';
import { ArbitrageExecutor } from './arbitrage-executor';
import { LatencyOptimizer } from './latency-optimizer';
import {
  OrchestratorConfig, OrchestratorStats, DEFAULT_ORCHESTRATOR_CONFIG,
} from './arbitrage-orchestrator-types';

export * from './arbitrage-orchestrator-types';

export class ArbitrageOrchestrator {
  private config: OrchestratorConfig;
  private connector: MultiExchangeConnector;
  private aggregator: RealTimePriceAggregator;
  private scanner: ArbitrageScanner;
  private executor: ArbitrageExecutor;
  private latencyOptimizer: LatencyOptimizer;

  private isRunning = false;
  private startTime = 0;
  private stats: OrchestratorStats = {
    status: 'idle', totalCycles: 0, totalOpportunities: 0, totalExecutions: 0,
    successfulExecutions: 0, connectedExchanges: 0, lastCycleMs: 0, uptime: 0,
  };

  private logTimer: ReturnType<typeof setInterval> | null = null;
  private dailyResetTimer: ReturnType<typeof setInterval> | null = null;
  private executionResults: ExecutionResult[] = [];

  constructor(config?: Partial<OrchestratorConfig>) {
    this.config = { ...DEFAULT_ORCHESTRATOR_CONFIG, ...config };
    this.connector = new MultiExchangeConnector();
    if (this.config.exchangeFactory) this.connector.setFactory(this.config.exchangeFactory);
    this.aggregator = new RealTimePriceAggregator({ pollIntervalMs: this.config.scanner.pollIntervalMs || 2000, minExchanges: 2 });
    this.scanner = new ArbitrageScanner(this.config.scanner);
    this.executor = new ArbitrageExecutor(this.config.executor);
    this.latencyOptimizer = new LatencyOptimizer();
  }

  async init(): Promise<void> {
    const log = getArbLogger();
    log.info('[Orchestrator] Initializing...');
    for (const exchangeConfig of this.config.exchanges) this.connector.addExchange(exchangeConfig);

    const connected = await this.connector.connectAll();
    this.stats.connectedExchanges = connected.length;
    if (connected.length < 2) throw new Error(`Need at least 2 exchanges, only ${connected.length} connected`);

    for (const [name, client] of this.connector.getActiveClients()) {
      this.scanner.addExchange(name, client);
      this.executor.addExchange(name, client);
      this.aggregator.addExchange(name, client);
      if (this.config.enableLatencyOptimizer) {
        this.latencyOptimizer.registerWarmup(name, async () => {
          const start = Date.now();
          await client.fetchTicker('BTC/USDT');
          this.latencyOptimizer.record(name, Date.now() - start, 'ticker', true);
        });
      }
    }

    this.aggregator.setSymbols(this.config.symbols);
    this.scanner.onOpportunity((opp) => { this.handleOpportunity(opp); });
    log.info(`[Orchestrator] Initialized: ${connected.length} exchanges, ${this.config.symbols.length} symbols`);
  }

  async start(): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;
    this.startTime = Date.now();
    this.stats.status = 'running';
    this.connector.startHealthChecks();
    if (this.config.enableLatencyOptimizer) this.latencyOptimizer.startWarmup();
    this.logTimer = setInterval(() => this.logDashboard(), this.config.logIntervalMs);
    this.scheduleDailyReset();
    await this.scanner.start();
    getArbLogger().info('[Orchestrator] Engine STARTED — scanning for opportunities...');
  }

  stop(): void {
    this.isRunning = false;
    this.stats.status = 'stopped';
    this.scanner.stop();
    this.aggregator.stop();
    this.connector.stopHealthChecks();
    this.latencyOptimizer.stopWarmup();
    if (this.logTimer) { clearInterval(this.logTimer); this.logTimer = null; }
    if (this.dailyResetTimer) { clearInterval(this.dailyResetTimer); this.dailyResetTimer = null; }
    this.connector.shutdown();
    getArbLogger().info('[Orchestrator] Engine STOPPED');
    this.logDashboard();
  }

  private async handleOpportunity(opp: ArbitrageOpportunity): Promise<void> {
    if (!this.isRunning) return;
    this.stats.totalOpportunities++;
    if (this.config.enableLatencyOptimizer) {
      const buyOk = this.latencyOptimizer.meetsTarget(opp.buyExchange);
      const sellOk = this.latencyOptimizer.meetsTarget(opp.sellExchange);
      if (!buyOk || !sellOk) {
        getArbLogger().warn(`[Orchestrator] Skipping opp: latency too high (buy=${buyOk}, sell=${sellOk})`);
        return;
      }
    }
    if (this.stats.totalExecutions - this.stats.successfulExecutions > this.config.maxOpportunitiesPerCycle * 3) return;

    this.stats.totalExecutions++;
    const startMs = Date.now();
    try {
      const result = await this.executor.execute(opp);
      this.executionResults.push(result);
      if (this.config.enableLatencyOptimizer) {
        this.latencyOptimizer.record(opp.buyExchange, result.executionTimeMs, 'order', result.success);
        this.latencyOptimizer.record(opp.sellExchange, result.executionTimeMs, 'order', result.success);
      }
      if (result.success) this.stats.successfulExecutions++;
      this.stats.lastCycleMs = Date.now() - startMs;
    } catch (err) {
      getArbLogger().error(`[Orchestrator] Execution error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  private scheduleDailyReset(): void {
    this.dailyResetTimer = setInterval(() => {
      const now = new Date();
      if (now.getUTCHours() === this.config.dailyResetHourUtc && now.getUTCMinutes() === 0) {
        this.executor.resetDaily();
        getArbLogger().info('[Orchestrator] Daily P&L reset completed');
      }
    }, 60000);
  }

  private logDashboard(): void {
    const log = getArbLogger();
    const uptime = this.isRunning ? Date.now() - this.startTime : 0;
    this.stats.uptime = uptime;
    const uptimeMin = (uptime / 60000).toFixed(1);
    const winRate = this.stats.totalExecutions > 0
      ? ((this.stats.successfulExecutions / this.stats.totalExecutions) * 100).toFixed(1) : '0';
    log.info(`[Orchestrator] Status=${this.stats.status} | Uptime=${uptimeMin}min | Exchanges=${this.stats.connectedExchanges} | Opps=${this.stats.totalOpportunities} | Executed=${this.stats.totalExecutions} | WinRate=${winRate}%`);
    if (this.config.enableLatencyOptimizer) {
      for (const p of this.latencyOptimizer.getSummary()) {
        log.info(`[Latency] ${p.exchange}: p50=${p.p50Ms}ms p95=${p.p95Ms}ms (${p.sampleCount} samples)`);
      }
    }
  }

  getStats(): OrchestratorStats {
    this.stats.uptime = this.isRunning ? Date.now() - this.startTime : 0;
    return { ...this.stats };
  }

  getExecutionHistory(): ExecutionResult[] { return [...this.executionResults]; }
  getComponents() {
    return {
      connector: this.connector, aggregator: this.aggregator,
      scanner: this.scanner, executor: this.executor, latencyOptimizer: this.latencyOptimizer,
    };
  }
}
