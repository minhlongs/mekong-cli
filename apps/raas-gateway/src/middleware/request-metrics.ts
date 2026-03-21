/**
 * Request metrics middleware — tracks per-path counters in KV (hourly buckets)
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';

interface MetricsBucket {
  totalRequests: number;
  latencySum: number;
  latencyMax: number;
  statusCounts: Record<string, number>;
  pathCounts: Record<string, number>;
}

async function updateMetrics(
  kv: KVNamespace,
  key: string,
  method: string,
  path: string,
  status: number,
  latencyMs: number
): Promise<void> {
  try {
    const existing = await kv.get(key, 'json') as MetricsBucket | null;
    const bucket: MetricsBucket = existing ?? {
      totalRequests: 0,
      latencySum: 0,
      latencyMax: 0,
      statusCounts: {},
      pathCounts: {},
    };

    bucket.totalRequests += 1;
    bucket.latencySum += latencyMs;
    bucket.latencyMax = Math.max(bucket.latencyMax, latencyMs);

    const statusKey = String(status);
    bucket.statusCounts[statusKey] = (bucket.statusCounts[statusKey] ?? 0) + 1;

    const pathKey = `${method}:${path}`;
    bucket.pathCounts[pathKey] = (bucket.pathCounts[pathKey] ?? 0) + 1;

    // 24h TTL — buckets expire automatically
    await kv.put(key, JSON.stringify(bucket), { expirationTtl: 86400 });
  } catch {
    // Fire-and-forget: silently ignore KV write errors
  }
}

export function requestMetrics(): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const start = Date.now();
    await next();
    const latencyMs = Date.now() - start;

    const key = `metrics:${new Date().toISOString().slice(0, 13)}`; // e.g. metrics:2026-03-21T14
    const method = c.req.method;
    const path = c.req.routePath || c.req.path;
    const status = c.res.status;

    // Guard: executionCtx may not exist in test environments
    const promise = updateMetrics(c.env.RATE_LIMIT_KV, key, method, path, status, latencyMs);
    try {
      c.executionCtx.waitUntil(promise);
    } catch {
      // No ExecutionContext (test env) — fire-and-forget
    }
  };
}
