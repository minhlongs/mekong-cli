/**
 * Metrics endpoints — aggregate KV hourly buckets for monitoring systems
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

interface MetricsBucket {
  totalRequests: number;
  latencySum: number;
  latencyMax: number;
  statusCounts: Record<string, number>;
  pathCounts: Record<string, number>;
}

export const metrics = new Hono<{ Bindings: Env }>();

// Build list of last N hourly KV keys (most-recent first)
function hourlyKeys(count: number): string[] {
  const keys: string[] = [];
  const now = new Date();
  for (let i = 0; i < count; i++) {
    const d = new Date(now.getTime() - i * 3600_000);
    keys.push(`metrics:${d.toISOString().slice(0, 13)}`);
  }
  return keys;
}

// GET /metrics — aggregate last 24 hourly buckets
metrics.get('/', async (c) => {
  const keys = hourlyKeys(24);
  const buckets = await Promise.all(
    keys.map((k) => c.env.RATE_LIMIT_KV.get(k, 'json') as Promise<MetricsBucket | null>)
  );

  let totalRequests = 0;
  let latencySum = 0;
  let latencyMax = 0;
  const statusBreakdown: Record<string, number> = {};
  const pathTotals: Record<string, number> = {};
  const requestsPerHour: number[] = [];

  for (const bucket of buckets) {
    const hourCount = bucket?.totalRequests ?? 0;
    requestsPerHour.push(hourCount);
    if (!bucket) continue;

    totalRequests += bucket.totalRequests;
    latencySum += bucket.latencySum;
    latencyMax = Math.max(latencyMax, bucket.latencyMax);

    for (const [s, n] of Object.entries(bucket.statusCounts)) {
      statusBreakdown[s] = (statusBreakdown[s] ?? 0) + n;
    }
    for (const [p, n] of Object.entries(bucket.pathCounts)) {
      pathTotals[p] = (pathTotals[p] ?? 0) + n;
    }
  }

  const topPaths = Object.entries(pathTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([path, count]) => ({ path, count }));

  return json({
    totalRequests,
    requestsPerHour,
    statusBreakdown,
    topPaths,
    avgLatencyMs: totalRequests > 0 ? Math.round(latencySum / totalRequests) : 0,
    maxLatencyMs: latencyMax,
    timestamp: new Date().toISOString(),
  });
});

// GET /metrics/live — current hour snapshot only
metrics.get('/live', async (c) => {
  const key = hourlyKeys(1)[0];
  const bucket = await c.env.RATE_LIMIT_KV.get(key, 'json') as MetricsBucket | null;

  const requestsThisHour = bucket?.totalRequests ?? 0;
  const avgLatencyMs = requestsThisHour > 0
    ? Math.round((bucket?.latencySum ?? 0) / requestsThisHour)
    : 0;

  const errorCount = Object.entries(bucket?.statusCounts ?? {})
    .filter(([s]) => parseInt(s) >= 500)
    .reduce((sum, [, n]) => sum + n, 0);

  const errorRate = requestsThisHour > 0
    ? Math.round((errorCount / requestsThisHour) * 10000) / 100
    : 0;

  return json({ requestsThisHour, avgLatencyMs, errorRate, timestamp: new Date().toISOString() });
});
