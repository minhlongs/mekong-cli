/**
 * @agencyos/vibe-observability — Observability SDK
 *
 * Structured logging, tracing, metrics collection, health checks.
 * Provider-agnostic: works with Langfuse, Sentry, custom backends.
 *
 * Usage:
 *   import { createLogger, createHealthChecker, createMetricsCollector } from '@agencyos/vibe-observability';
 */

// ─── Types ──────────────────────────────────────────────────────

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: Record<string, unknown>;
  traceId?: string;
}

export interface HealthCheck {
  name: string;
  status: HealthStatus;
  latencyMs: number;
  message?: string;
  lastChecked: string;
}

export interface MetricPoint {
  name: string;
  value: number;
  unit: string;
  tags: Record<string, string>;
  timestamp: string;
}

// ─── Structured Logger ──────────────────────────────────────────

export interface LoggerConfig {
  serviceName: string;
  minLevel: LogLevel;
  structured: boolean;
}

export function createLogger(config: LoggerConfig) {
  const levels: LogLevel[] = ['debug', 'info', 'warn', 'error', 'fatal'];
  const minIdx = levels.indexOf(config.minLevel);

  function shouldLog(level: LogLevel): boolean {
    return levels.indexOf(level) >= minIdx;
  }

  function formatEntry(level: LogLevel, message: string, context?: Record<string, unknown>): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      context: { service: config.serviceName, ...context },
    };
  }

  return {
    debug: (msg: string, ctx?: Record<string, unknown>) => shouldLog('debug') ? formatEntry('debug', msg, ctx) : null,
    info: (msg: string, ctx?: Record<string, unknown>) => shouldLog('info') ? formatEntry('info', msg, ctx) : null,
    warn: (msg: string, ctx?: Record<string, unknown>) => shouldLog('warn') ? formatEntry('warn', msg, ctx) : null,
    error: (msg: string, ctx?: Record<string, unknown>) => shouldLog('error') ? formatEntry('error', msg, ctx) : null,
    fatal: (msg: string, ctx?: Record<string, unknown>) => shouldLog('fatal') ? formatEntry('fatal', msg, ctx) : null,
  };
}

// ─── Health Checker ─────────────────────────────────────────────

export interface HealthCheckConfig {
  checks: Array<{ name: string; check: () => Promise<boolean>; timeoutMs?: number }>;
}

export function createHealthChecker(config: HealthCheckConfig) {
  return {
    async runAll(): Promise<{ overall: HealthStatus; checks: HealthCheck[] }> {
      const results: HealthCheck[] = [];

      for (const { name, check, timeoutMs = 5000 } of config.checks) {
        const start = Date.now();
        try {
          const result = await Promise.race([
            check(),
            new Promise<boolean>((_, reject) => setTimeout(() => reject(new Error('timeout')), timeoutMs)),
          ]);
          results.push({
            name,
            status: result ? 'healthy' : 'unhealthy',
            latencyMs: Date.now() - start,
            lastChecked: new Date().toISOString(),
          });
        } catch (err) {
          results.push({
            name,
            status: 'unhealthy',
            latencyMs: Date.now() - start,
            message: err instanceof Error ? err.message : 'Unknown error',
            lastChecked: new Date().toISOString(),
          });
        }
      }

      const unhealthy = results.filter((r) => r.status === 'unhealthy').length;
      const overall: HealthStatus = unhealthy === 0 ? 'healthy' : unhealthy < results.length ? 'degraded' : 'unhealthy';

      return { overall, checks: results };
    },
  };
}

// ─── Metrics Collector ──────────────────────────────────────────

export function createMetricsCollector(serviceName: string) {
  const buffer: MetricPoint[] = [];

  return {
    /**
     * Record a metric point
     */
    record(name: string, value: number, unit: string, tags: Record<string, string> = {}): void {
      buffer.push({
        name,
        value,
        unit,
        tags: { service: serviceName, ...tags },
        timestamp: new Date().toISOString(),
      });
    },

    /**
     * Flush buffer and return all collected metrics
     */
    flush(): MetricPoint[] {
      const points = [...buffer];
      buffer.length = 0;
      return points;
    },

    /**
     * Get buffer size
     */
    size(): number {
      return buffer.length;
    },
  };
}
