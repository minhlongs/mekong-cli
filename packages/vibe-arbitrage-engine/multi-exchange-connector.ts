/**
 * MultiExchangeConnector — Manages connections to multiple exchanges.
 * Handles: connection pooling, health checks, auto-reconnect, balance tracking.
 */

import { IExchange, IBalance } from '@mekong/trading-core/interfaces';
import { getArbLogger } from './arb-logger';
import { ExchangeConfig } from './arbitrage-types';
import {
  ExchangeHealth, ConnectorConfig, DEFAULT_CONNECTOR_CONFIG, ExchangeFactory,
} from './multi-exchange-types';

export * from './multi-exchange-types';

export class MultiExchangeConnector {
  private config: ConnectorConfig;
  private clients: Map<string, IExchange> = new Map();
  private health: Map<string, ExchangeHealth> = new Map();
  private balances: Map<string, Record<string, IBalance>> = new Map();
  private healthTimer: ReturnType<typeof setInterval> | null = null;
  private disabledExchanges: Set<string> = new Set();
  private factory: ExchangeFactory | null = null;

  constructor(config?: Partial<ConnectorConfig>) {
    this.config = { ...DEFAULT_CONNECTOR_CONFIG, ...config };
  }

  setFactory(factory: ExchangeFactory): void {
    this.factory = factory;
  }

  addClient(name: string, client: IExchange): void {
    this.clients.set(name, client);
    this.health.set(name, {
      exchange: name, connected: false, lastPingMs: 0, lastPingTime: 0, failCount: 0, avgLatencyMs: 0,
    });
  }

  addExchange(exchangeConfig: ExchangeConfig): void {
    if (!exchangeConfig.enabled) return;
    const label = exchangeConfig.label || exchangeConfig.id;
    if (this.factory) {
      this.addClient(label, this.factory(exchangeConfig));
    } else {
      this.health.set(label, {
        exchange: label, connected: false, lastPingMs: 0, lastPingTime: 0, failCount: 0, avgLatencyMs: 0,
      });
    }
  }

  async connectAll(): Promise<string[]> {
    const log = getArbLogger();
    const connected: string[] = [];
    const tasks = Array.from(this.clients.entries()).map(async ([name, client]) => {
      try {
        const start = Date.now();
        await client.connect();
        const latency = Date.now() - start;
        const h = this.health.get(name)!;
        h.connected = true;
        h.lastPingMs = latency;
        h.lastPingTime = Date.now();
        h.avgLatencyMs = latency;
        connected.push(name);
        log.info(`[Connector] ${name} connected (${latency}ms)`);
      } catch (err) {
        const h = this.health.get(name)!;
        h.failCount++;
        log.error(`[Connector] ${name} failed: ${err instanceof Error ? err.message : String(err)}`);
      }
    });
    await Promise.allSettled(tasks);
    return connected;
  }

  startHealthChecks(): void {
    if (this.healthTimer) return;
    this.healthTimer = setInterval(() => this.runHealthCheck(), this.config.healthCheckIntervalMs);
  }

  stopHealthChecks(): void {
    if (this.healthTimer) { clearInterval(this.healthTimer); this.healthTimer = null; }
  }

  async runHealthCheck(): Promise<void> {
    for (const [name, client] of this.clients) {
      if (this.disabledExchanges.has(name)) continue;
      try {
        const start = Date.now();
        await client.fetchTicker('BTC/USDT');
        const latency = Date.now() - start;
        const h = this.health.get(name)!;
        h.connected = true;
        h.lastPingMs = latency;
        h.lastPingTime = Date.now();
        h.failCount = 0;
        h.avgLatencyMs = (h.avgLatencyMs * 0.7) + (latency * 0.3);
      } catch {
        const h = this.health.get(name)!;
        h.connected = false;
        h.failCount++;
        if (h.failCount >= this.config.maxFailsBeforeDisable) {
          this.disabledExchanges.add(name);
          getArbLogger().warn(`[Connector] ${name} disabled after ${h.failCount} failures`);
          if (this.config.autoReconnect) this.scheduleReconnect(name);
        }
      }
    }
  }

  private scheduleReconnect(name: string): void {
    setTimeout(async () => {
      const client = this.clients.get(name);
      if (!client) return;
      try {
        await client.connect();
        this.disabledExchanges.delete(name);
        const h = this.health.get(name)!;
        h.connected = true;
        h.failCount = 0;
        getArbLogger().info(`[Connector] ${name} reconnected successfully`);
      } catch {
        getArbLogger().warn(`[Connector] ${name} reconnect failed, will retry`);
        this.scheduleReconnect(name);
      }
    }, this.config.reconnectDelayMs);
  }

  async fetchAllBalances(): Promise<Map<string, Record<string, IBalance>>> {
    const tasks = Array.from(this.getActiveClients().entries()).map(async ([name, client]) => {
      try {
        const balance = await client.fetchBalance();
        this.balances.set(name, balance);
      } catch (err) {
        getArbLogger().warn(`[Connector] Balance fetch failed for ${name}: ${err instanceof Error ? err.message : String(err)}`);
      }
    });
    await Promise.allSettled(tasks);
    return new Map(this.balances);
  }

  getActiveClients(): Map<string, IExchange> {
    const active = new Map<string, IExchange>();
    for (const [name, client] of this.clients) {
      const h = this.health.get(name);
      if (h?.connected && !this.disabledExchanges.has(name)) active.set(name, client);
    }
    return active;
  }

  getClient(name: string): IExchange | undefined { return this.clients.get(name); }
  getHealthStatus(): ExchangeHealth[] { return Array.from(this.health.values()); }
  getActiveCount(): number { return this.getActiveClients().size; }
  getExchangeNames(): string[] { return Array.from(this.clients.keys()); }
  isHealthy(name: string): boolean {
    const h = this.health.get(name);
    return h !== undefined && h.connected && !this.disabledExchanges.has(name);
  }

  shutdown(): void {
    this.stopHealthChecks();
    this.clients.clear();
    this.health.clear();
    this.balances.clear();
    this.disabledExchanges.clear();
    getArbLogger().info('[Connector] Shutdown complete');
  }
}
