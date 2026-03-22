/**
 * API Usage Analytics Service — per-endpoint stats, latency percentiles, error breakdown
 */

type DB = D1Database;

/** Current period key in YYYY-MM-DD format */
function todayPeriod(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Record a single API request — upserts stats for current day period */
export async function recordRequest(
  db: DB,
  tenantId: string,
  endpoint: string,
  method: string,
  statusCode: number,
  latencyMs: number
): Promise<void> {
  const period = todayPeriod();
  const id = `${tenantId}:${endpoint}:${method}:${period}`;
  const isSuccess = statusCode < 400 ? 1 : 0;
  const isError = statusCode >= 400 ? 1 : 0;

  await db.prepare(`
    INSERT INTO api_endpoint_stats
      (id, tenant_id, endpoint, method, period, total_requests, success_count, error_count,
       avg_latency_ms, p50_latency_ms, p95_latency_ms, p99_latency_ms)
    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(tenant_id, endpoint, method, period) DO UPDATE SET
      total_requests = total_requests + 1,
      success_count  = success_count + excluded.success_count,
      error_count    = error_count + excluded.error_count,
      avg_latency_ms = (avg_latency_ms * total_requests + excluded.avg_latency_ms) / (total_requests + 1),
      p50_latency_ms = (p50_latency_ms + excluded.p50_latency_ms) / 2,
      p95_latency_ms = MAX(p95_latency_ms, excluded.p95_latency_ms * 0.95),
      p99_latency_ms = MAX(p99_latency_ms, excluded.p99_latency_ms * 0.99)
  `).bind(id, tenantId, endpoint, method, period, isSuccess, isError,
    latencyMs, latencyMs, latencyMs, latencyMs).run();
}

/** Get aggregated endpoint stats for past N days */
export async function getEndpointStats(
  db: DB, tenantId: string, days = 7
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT endpoint, method,
      SUM(total_requests) AS total_requests,
      SUM(success_count)  AS success_count,
      SUM(error_count)    AS error_count,
      AVG(avg_latency_ms) AS avg_latency_ms,
      AVG(p50_latency_ms) AS p50_latency_ms,
      MAX(p95_latency_ms) AS p95_latency_ms,
      MAX(p99_latency_ms) AS p99_latency_ms
    FROM api_endpoint_stats
    WHERE tenant_id = ? AND period >= date('now', ?)
    GROUP BY endpoint, method
    ORDER BY total_requests DESC
  `).bind(tenantId, `-${days} days`).all();
  return (r.results ?? []) as Record<string, unknown>[];
}

/** Top endpoints by request volume */
export async function getTopEndpoints(
  db: DB, tenantId: string, limit = 10
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT endpoint, method, SUM(total_requests) AS total_requests
    FROM api_endpoint_stats WHERE tenant_id = ?
    GROUP BY endpoint, method ORDER BY total_requests DESC LIMIT ?
  `).bind(tenantId, limit).all();
  return (r.results ?? []) as Record<string, unknown>[];
}

/** Slowest endpoints by average latency */
export async function getSlowestEndpoints(
  db: DB, tenantId: string, limit = 10
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT endpoint, method, AVG(avg_latency_ms) AS avg_latency_ms,
      MAX(p95_latency_ms) AS p95_latency_ms, SUM(total_requests) AS total_requests
    FROM api_endpoint_stats WHERE tenant_id = ?
    GROUP BY endpoint, method ORDER BY avg_latency_ms DESC LIMIT ?
  `).bind(tenantId, limit).all();
  return (r.results ?? []) as Record<string, unknown>[];
}

/** Error breakdown by status code, optionally scoped to one endpoint */
export async function getErrorBreakdown(
  db: DB, tenantId: string, endpoint?: string
): Promise<Record<string, unknown>[]> {
  const sql = endpoint
    ? `SELECT status_code, SUM(count) AS total FROM api_error_logs
       WHERE tenant_id = ? AND endpoint = ? GROUP BY status_code ORDER BY total DESC`
    : `SELECT status_code, SUM(count) AS total FROM api_error_logs
       WHERE tenant_id = ? GROUP BY status_code ORDER BY total DESC`;
  const r = endpoint
    ? await db.prepare(sql).bind(tenantId, endpoint).all()
    : await db.prepare(sql).bind(tenantId).all();
  return (r.results ?? []) as Record<string, unknown>[];
}

/** Daily latency trend for a specific endpoint */
export async function getLatencyTrend(
  db: DB, tenantId: string, endpoint: string, days = 14
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT period, AVG(avg_latency_ms) AS avg_latency_ms,
      MAX(p95_latency_ms) AS p95_latency_ms, MAX(p99_latency_ms) AS p99_latency_ms
    FROM api_endpoint_stats
    WHERE tenant_id = ? AND endpoint = ? AND period >= date('now', ?)
    GROUP BY period ORDER BY period ASC
  `).bind(tenantId, endpoint, `-${days} days`).all();
  return (r.results ?? []) as Record<string, unknown>[];
}

/** Daily request volume trend */
export async function getRequestVolumeTrend(
  db: DB, tenantId: string, days = 14
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT period, SUM(total_requests) AS total_requests,
      SUM(success_count) AS success_count, SUM(error_count) AS error_count
    FROM api_endpoint_stats
    WHERE tenant_id = ? AND period >= date('now', ?)
    GROUP BY period ORDER BY period ASC
  `).bind(tenantId, `-${days} days`).all();
  return (r.results ?? []) as Record<string, unknown>[];
}

/** Upsert error log entry */
export async function recordError(
  db: DB,
  tenantId: string,
  endpoint: string,
  method: string,
  statusCode: number,
  message?: string
): Promise<void> {
  const id = `${tenantId}:${endpoint}:${statusCode}`;
  await db.prepare(`
    INSERT INTO api_error_logs (id, tenant_id, endpoint, method, status_code, error_message)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      count = count + 1,
      last_seen_at = datetime('now'),
      error_message = excluded.error_message
  `).bind(id, tenantId, endpoint, method, statusCode, message ?? null).run();
}

/** Endpoints with highest error rates */
export async function getErrorHotspots(
  db: DB, tenantId: string
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT s.endpoint, s.method,
      SUM(s.total_requests) AS total_requests,
      SUM(s.error_count) AS error_count,
      ROUND(SUM(s.error_count) * 100.0 / MAX(SUM(s.total_requests), 1), 2) AS error_rate_pct
    FROM api_endpoint_stats s WHERE s.tenant_id = ?
    GROUP BY s.endpoint, s.method
    HAVING error_count > 0
    ORDER BY error_rate_pct DESC LIMIT 10
  `).bind(tenantId).all();
  return (r.results ?? []) as Record<string, unknown>[];
}

/** Overall usage summary for a tenant */
export async function getUsageSummary(
  db: DB, tenantId: string
): Promise<Record<string, unknown>> {
  const r = await db.prepare(`
    SELECT SUM(total_requests) AS total_requests,
      SUM(error_count) AS total_errors,
      AVG(avg_latency_ms) AS avg_latency_ms,
      ROUND(SUM(error_count) * 100.0 / MAX(SUM(total_requests), 1), 2) AS error_rate_pct
    FROM api_endpoint_stats WHERE tenant_id = ?
  `).bind(tenantId).first();

  const top = await getTopEndpoints(db, tenantId, 1);
  return {
    total_requests: (r as any)?.total_requests ?? 0,
    total_errors:   (r as any)?.total_errors ?? 0,
    avg_latency_ms: (r as any)?.avg_latency_ms ?? 0,
    error_rate_pct: (r as any)?.error_rate_pct ?? 0,
    top_endpoint:   top[0]?.endpoint ?? null,
  };
}
