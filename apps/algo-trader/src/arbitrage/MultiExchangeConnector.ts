/**
 * MultiExchangeConnector — Manages connections to multiple exchanges.
 * Handles: connection pooling, health checks, auto-reconnect, balance tracking.
 * Supported: Binance, OKX, Bybit, Gate.io (via CCXT).
 */

import { ExchangeClient } from '../execution/ExchangeClient';
import { IBalance } from '../interfaces/IExchange';
import { logger } from '../utils/logger';

export interface ExchangeConfig {
  id: string;         // CCXT exchange ID (e.g., 'binance', 'okx', 'bybit', 'gateio')
  apiKey?: string;
  secret?: string;
  label?: string;     // Human-readable label (default: id)
  enabled: boolean;
}

export interface ExchangeHealth {
  exchange: string;
  connected: boolean;
  lastPingMs: number;
  lastPingTime: number;
  failCount: number;
  avgLatencyMs: number;
}

export interface ConnectorConfig {
  healthCheckIntervalMs: number;   // How often to ping exchanges (default: 30000)
  maxFailsBeforeDisable: number;   // Disable exchange after N consecutive fails (default: 5)
  autoReconnect: boolean;          // Auto-reconnect on failure (default: true)
  reconnectDelayMs: number;        // Delay before reconnect attempt (default: 5000)
}

const DEFAULT_CONFIG: ConnectorConfig = {
  healthCheckIntervalMs: 30000,
  maxFailsBeforeDisable: 5,
  autoReconnect: true,
  reconnectDelayMs: 5000,
};

/** Pre-configured exchange IDs for the 4 target exchanges */
export const SUPPORTED_EXCHANGES = ['binance', 'okx', 'bybit', 'gateio'] as const;
export type SupportedExchange = typeof SUPPORTED_EXCHANGES[number];

export class MultiExchangeConnector {
  private config: ConnectorConfig;
  private clients: Map<string, ExchangeClient> = new Map();
  private health: Map<string, ExchangeHealth> = new Map();
  private balances: Map<string, Record<string, IBalance>> = new Map();
  private healthTimer: NodeJS.Timeout | null = null;
  private disabledExchanges: Set<string> = new Set();

  constructor(config?: Partial<ConnectorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Register an exchange. Does NOT connect yet — call connectAll().
   */
  addExchange(exchangeConfig: ExchangeConfig): void {
    if (!exchangeConfig.enabled) return;

    const label = exchangeConfig.label || exchangeConfig.id;
    const client = new ExchangeClient(exchangeConfig.id, exchangeConfig.apiKey, exchangeConfig.secret);

    this.clients.set(label, client);
    this.health.set(label, {
      exchange: label,
      connected: false,
      lastPingMs: 0,
      lastPingTime: 0,
      failCount: 0,
      avgLatencyMs: 0,
    });
  }

  /**
   * Connect all registered exchanges in parallel.
   * Returns list of successfully connected exchange names.
   */
  async connectAll(): Promise<string[]> {
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
        logger.info(`[Connector] ✅ ${name} connected (${latency}ms)`);
      } catch (err) {
        const h = this.health.get(name)!;
        h.failCount++;
        logger.error(`[Connector] ❌ ${name} failed: ${err instanceof Error ? err.message : String(err)}`);
      }
    });

    await Promise.allSettled(tasks);
    return connected;
  }

  /**
   * Start health check loop. Pings each exchange periodically.
   */
  startHealthChecks(): void {
    if (this.healthTimer) return;

    this.healthTimer = setInterval(() => this.runHealthCheck(), this.config.healthCheckIntervalMs);
    logger.info(`[Connector] Health checks started (every ${this.config.healthCheckIntervalMs}ms)`);
  }

  /**
   * Stop health check loop.
   */
  stopHealthChecks(): void {
    if (this.healthTimer) {
      clearInterval(this.healthTimer);
      this.healthTimer = null;
    }
  }

  /**
   * Run a single health check across all exchanges.
   */
  async runHealthCheck(): Promise<void> {
    for (const [name, client] of this.clients) {
      if (this.disabledExchanges.has(name)) continue;

      try {
        const start = Date.now();
        await client.fetchTicker('BTC/USDT'); // Ping via ticker fetch
        const latency = Date.now() - start;

        const h = this.health.get(name)!;
        h.connected = true;
        h.lastPingMs = latency;
        h.lastPingTime = Date.now();
        h.failCount = 0;
        h.avgLatencyMs = (h.avgLatencyMs * 0.7) + (latency * 0.3); // EMA
      } catch {
        const h = this.health.get(name)!;
        h.connected = false;
        h.failCount++;

        if (h.failCount >= this.config.maxFailsBeforeDisable) {
          this.disabledExchanges.add(name);
          logger.warn(`[Connector] ${name} disabled after ${h.failCount} failures`);

          if (this.config.autoReconnect) {
            this.scheduleReconnect(name);
          }
        }
      }
    }
  }

  /**
   * Schedule a reconnect attempt for a disabled exchange.
   */
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
        logger.info(`[Connector] ${name} reconnected successfully`);
      } catch {
        logger.warn(`[Connector] ${name} reconnect failed, will retry`);
        this.scheduleReconnect(name);
      }
    }, this.config.reconnectDelayMs);
  }

  /**
   * Fetch balances from all connected exchanges.
   */
  async fetchAllBalances(): Promise<Map<string, Record<string, IBalance>>> {
    const tasks = Array.from(this.getActiveClients().entries()).map(async ([name, client]) => {
      try {
        const balance = await client.fetchBalance();
        this.balances.set(name, balance);
      } catch (err) {
        logger.warn(`[Connector] Balance fetch failed for ${name}: ${err instanceof Error ? err.message : String(err)}`);
      }
    });

    await Promise.allSettled(tasks);
    return new Map(this.balances);
  }

  /**
   * Get all active (connected, not disabled) exchange clients.
   */
  getActiveClients(): Map<string, ExchangeClient> {
    const active = new Map<string, ExchangeClient>();
    for (const [name, client] of this.clients) {
      const h = this.health.get(name);
      if (h?.connected && !this.disabledExchanges.has(name)) {
        active.set(name, client);
      }
    }
    return active;
  }

  /**
   * Get a specific exchange client by name.
   */
  getClient(name: string): ExchangeClient | undefined {
    return this.clients.get(name);
  }

  /**
   * Get health status for all exchanges.
   */
  getHealthStatus(): ExchangeHealth[] {
    return Array.from(this.health.values());
  }

  /**
   * Get number of active exchanges.
   */
  getActiveCount(): number {
    return this.getActiveClients().size;
  }

  /**
   * Get all registered exchange names.
   */
  getExchangeNames(): string[] {
    return Array.from(this.clients.keys());
  }

  /**
   * Check if a specific exchange is healthy.
   */
  isHealthy(name: string): boolean {
    const h = this.health.get(name);
    return h !== undefined && h.connected && !this.disabledExchanges.has(name);
  }

  /**
   * Shutdown all connections and stop health checks.
   */
  shutdown(): void {
    this.stopHealthChecks();
    this.clients.clear();
    this.health.clear();
    this.balances.clear();
    this.disabledExchanges.clear();
    logger.info('[Connector] Shutdown complete');
  }
}
