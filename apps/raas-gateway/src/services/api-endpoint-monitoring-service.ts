/**
 * API Endpoint Monitoring Service — tracks per-endpoint metrics, availability, and alerts
 * Provides slow endpoint detection and admin dashboard aggregation
 */

/** Record a single request metric for an endpoint */
export async function recordMetric(db: any, data: {
  path: string;
  method: string;
  status_code?: number;
  response_time_ms?: number;
  tenant_id?: string;
  error_message?: string;
}): Promise<void> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO endpoint_metrics (id, path, method, status_code, response_time_ms, tenant_id, error_message)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id, data.path, data.method,
    data.status_code ?? null, data.response_time_ms ?? null,
    data.tenant_id ?? null, data.error_message ?? null
  ).run();
}

/** Fetch recent metrics for a path, with optional filters */
export async function getMetrics(db: any, path: string, filters?: {
  method?: string;
  tenant_id?: string;
  limit?: number;
}): Promise<unknown[]> {
  const limit = Math.min(filters?.limit ?? 100, 500);
  let query = `SELECT * FROM endpoint_metrics WHERE path = ?`;
  const binds: unknown[] = [path];

  if (filters?.method) { query += ` AND method = ?`; binds.push(filters.method); }
  if (filters?.tenant_id) { query += ` AND tenant_id = ?`; binds.push(filters.tenant_id); }

  query += ` ORDER BY recorded_at DESC LIMIT ?`;
  binds.push(limit);

  const rows = await db.prepare(query).bind(...binds).all();
  return rows.results;
}

/** Aggregate stats (avg response, error rate, call count) for a path */
export async function getEndpointStats(db: any, path: string): Promise<{
  path: string;
  total_requests: number;
  error_count: number;
  error_rate_pct: number;
  avg_response_ms: number;
  p95_response_ms: number;
}> {
  const agg = await db.prepare(
    `SELECT COUNT(*) as total,
            SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
            AVG(response_time_ms) as avg_ms
     FROM endpoint_metrics WHERE path = ?`
  ).bind(path).first() as { total: number; errors: number; avg_ms: number } | null;

  const total = agg?.total ?? 0;
  const errors = agg?.errors ?? 0;

  // P95 approximation via sorted fetch
  const latRows = await db.prepare(
    `SELECT response_time_ms FROM endpoint_metrics WHERE path = ? AND response_time_ms IS NOT NULL
     ORDER BY response_time_ms ASC`
  ).bind(path).all();

  const latencies = (latRows.results as { response_time_ms: number }[]).map((r) => r.response_time_ms);
  const p95 = latencies.length
    ? latencies[Math.min(Math.floor(latencies.length * 0.95), latencies.length - 1)]
    : 0;

  return {
    path,
    total_requests: total,
    error_count: errors,
    error_rate_pct: total === 0 ? 0 : Math.round((errors / total) * 10000) / 100,
    avg_response_ms: Math.round(agg?.avg_ms ?? 0),
    p95_response_ms: p95,
  };
}

/** List all tracked endpoint availability records */
export async function listAvailability(db: any): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM endpoint_availability ORDER BY path, method`
  ).all();
  return rows.results;
}

/** Upsert availability record for a path+method */
export async function updateAvailability(db: any, path: string, method: string, data: {
  status?: string;
  last_check_at?: string;
  uptime_pct?: number;
  avg_response_ms?: number;
  check_count?: number;
  fail_count?: number;
}): Promise<void> {
  const existing = await db.prepare(
    `SELECT id FROM endpoint_availability WHERE path = ? AND method = ?`
  ).bind(path, method).first() as { id: string } | null;

  const now = new Date().toISOString();
  if (existing) {
    await db.prepare(
      `UPDATE endpoint_availability SET status=?, last_check_at=?, uptime_pct=?,
       avg_response_ms=?, check_count=?, fail_count=?, updated_at=?
       WHERE path=? AND method=?`
    ).bind(
      data.status ?? 'up', data.last_check_at ?? now,
      data.uptime_pct ?? 100, data.avg_response_ms ?? 0,
      data.check_count ?? 0, data.fail_count ?? 0, now,
      path, method
    ).run();
  } else {
    await db.prepare(
      `INSERT INTO endpoint_availability (id, path, method, status, last_check_at, uptime_pct, avg_response_ms, check_count, fail_count, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      crypto.randomUUID(), path, method,
      data.status ?? 'up', data.last_check_at ?? now,
      data.uptime_pct ?? 100, data.avg_response_ms ?? 0,
      data.check_count ?? 0, data.fail_count ?? 0, now
    ).run();
  }
}

/** Return metric history rows used as availability history for a path */
export async function getAvailabilityHistory(db: any, path: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT recorded_at, status_code, response_time_ms, error_message
     FROM endpoint_metrics WHERE path = ? ORDER BY recorded_at DESC LIMIT 200`
  ).bind(path).all();
  return rows.results;
}

/** List all configured alerts */
export async function listAlerts(db: any): Promise<unknown[]> {
  const rows = await db.prepare(`SELECT * FROM endpoint_alerts ORDER BY created_at DESC`).all();
  return rows.results;
}

/** Create a new alert rule */
export async function createAlert(db: any, data: {
  path: string;
  alert_type: string;
  condition_json?: string;
  threshold: number;
  severity?: string;
}): Promise<{ id: string }> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO endpoint_alerts (id, path, alert_type, condition_json, threshold, severity)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(
    id, data.path, data.alert_type,
    data.condition_json ?? '{}', data.threshold,
    data.severity ?? 'warning'
  ).run();
  return { id };
}

/** Update an existing alert rule */
export async function updateAlert(db: any, id: string, data: {
  threshold?: number;
  severity?: string;
  enabled?: number;
  condition_json?: string;
}): Promise<void> {
  await db.prepare(
    `UPDATE endpoint_alerts SET threshold=COALESCE(?,threshold), severity=COALESCE(?,severity),
     enabled=COALESCE(?,enabled), condition_json=COALESCE(?,condition_json)
     WHERE id=?`
  ).bind(
    data.threshold ?? null, data.severity ?? null,
    data.enabled ?? null, data.condition_json ?? null, id
  ).run();
}

/** Delete an alert rule by id */
export async function deleteAlert(db: any, id: string): Promise<void> {
  await db.prepare(`DELETE FROM endpoint_alerts WHERE id = ?`).bind(id).run();
}

/** Return endpoints with avg response above thresholdMs (default 1000ms) */
export async function getSlowEndpoints(db: any, thresholdMs = 1000): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT path, method, AVG(response_time_ms) as avg_ms, COUNT(*) as total
     FROM endpoint_metrics
     WHERE response_time_ms IS NOT NULL
     GROUP BY path, method
     HAVING avg_ms >= ?
     ORDER BY avg_ms DESC`
  ).bind(thresholdMs).all();
  return rows.results;
}

/** Admin overview: top paths by volume, error rates, slow endpoints */
export async function getAdminOverview(db: any): Promise<{
  total_requests: number;
  unique_paths: number;
  error_rate_pct: number;
  slow_endpoints: unknown[];
  top_paths: unknown[];
}> {
  const summary = await db.prepare(
    `SELECT COUNT(*) as total,
            COUNT(DISTINCT path) as paths,
            SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
     FROM endpoint_metrics`
  ).first() as { total: number; paths: number; errors: number } | null;

  const topPaths = await db.prepare(
    `SELECT path, COUNT(*) as requests, AVG(response_time_ms) as avg_ms
     FROM endpoint_metrics GROUP BY path ORDER BY requests DESC LIMIT 10`
  ).all();

  const slow = await getSlowEndpoints(db, 1000);

  const total = summary?.total ?? 0;
  const errors = summary?.errors ?? 0;

  return {
    total_requests: total,
    unique_paths: summary?.paths ?? 0,
    error_rate_pct: total === 0 ? 0 : Math.round((errors / total) * 10000) / 100,
    slow_endpoints: slow,
    top_paths: topPaths.results,
  };
}

export const apiEndpointMonitoringService = {
  recordMetric,
  getMetrics,
  getEndpointStats,
  listAvailability,
  updateAvailability,
  getAvailabilityHistory,
  listAlerts,
  createAlert,
  updateAlert,
  deleteAlert,
  getSlowEndpoints,
  getAdminOverview,
};
