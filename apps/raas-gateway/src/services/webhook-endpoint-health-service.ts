/**
 * Webhook Endpoint Health Service — upsert, query, reset per-endpoint health records
 * Used internally by webhook-analytics-service; also exported for direct use
 */

type DB = D1Database;

/** Derive status label from consecutive failure count */
export function deriveEndpointStatus(failures: number): string {
  if (failures === 0) return 'healthy';
  if (failures < 5) return 'degraded';
  return 'down';
}

/** Upsert endpoint health record after a delivery attempt */
export async function updateEndpointHealth(
  db: DB,
  tenantId: string,
  endpointUrl: string,
  success: boolean,
  latencyMs: number,
  errorMsg?: string
): Promise<void> {
  const now = new Date().toISOString();
  const existing = await db.prepare(`
    SELECT consecutive_failures, total_deliveries, success_rate, avg_response_ms
    FROM webhook_endpoint_health WHERE tenant_id = ? AND endpoint_url = ?
  `).bind(tenantId, endpointUrl).first<{
    consecutive_failures: number; total_deliveries: number;
    success_rate: number; avg_response_ms: number;
  }>();

  if (!existing) {
    const status = success ? 'healthy' : 'degraded';
    await db.prepare(`
      INSERT INTO webhook_endpoint_health
        (tenant_id, endpoint_url, status, consecutive_failures,
         last_success_at, last_failure_at, last_error,
         total_deliveries, success_rate, avg_response_ms, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
    `).bind(
      tenantId, endpointUrl, status, success ? 0 : 1,
      success ? now : null, success ? null : now,
      success ? null : (errorMsg ?? null),
      success ? 100.0 : 0.0, latencyMs, now
    ).run();
    return;
  }

  const newTotal = existing.total_deliveries + 1;
  const prevSuccesses = Math.round(existing.success_rate * existing.total_deliveries / 100);
  const newSuccesses = success ? prevSuccesses + 1 : prevSuccesses;
  const newRate = (newSuccesses / newTotal) * 100;
  const newAvg = (existing.avg_response_ms * existing.total_deliveries + latencyMs) / newTotal;
  const newFailures = success ? 0 : existing.consecutive_failures + 1;
  const newStatus = deriveEndpointStatus(newFailures);

  await db.prepare(`
    UPDATE webhook_endpoint_health SET
      status                = ?,
      consecutive_failures  = ?,
      last_success_at       = CASE WHEN ? THEN ? ELSE last_success_at END,
      last_failure_at       = CASE WHEN ? THEN ? ELSE last_failure_at END,
      last_error            = CASE WHEN ? THEN ? ELSE last_error END,
      total_deliveries      = ?,
      success_rate          = ?,
      avg_response_ms       = ?,
      updated_at            = ?
    WHERE tenant_id = ? AND endpoint_url = ?
  `).bind(
    newStatus, newFailures,
    success ? 1 : 0, now,
    success ? 0 : 1, now,
    success ? 0 : 1, errorMsg ?? null,
    newTotal, newRate, newAvg, now,
    tenantId, endpointUrl
  ).run();
}

/** Get health record for a specific endpoint */
export async function getEndpointHealth(
  db: DB,
  tenantId: string,
  endpointUrl: string
): Promise<Record<string, unknown> | null> {
  return db.prepare(`
    SELECT * FROM webhook_endpoint_health WHERE tenant_id = ? AND endpoint_url = ?
  `).bind(tenantId, endpointUrl).first() as Promise<Record<string, unknown> | null>;
}

/** List all endpoint health records for a tenant, newest first */
export async function listEndpoints(
  db: DB,
  tenantId: string
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT * FROM webhook_endpoint_health WHERE tenant_id = ? ORDER BY updated_at DESC
  `).bind(tenantId).all();
  return r.results as Record<string, unknown>[];
}

/** List endpoints with degraded or down status */
export async function getFailedEndpoints(
  db: DB,
  tenantId: string
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT * FROM webhook_endpoint_health
    WHERE tenant_id = ? AND status IN ('degraded', 'down')
    ORDER BY consecutive_failures DESC
  `).bind(tenantId).all();
  return r.results as Record<string, unknown>[];
}

/** Reset a specific endpoint back to healthy state; returns true if found */
export async function resetEndpointHealth(
  db: DB,
  tenantId: string,
  endpointUrl: string
): Promise<boolean> {
  const now = new Date().toISOString();
  const r = await db.prepare(`
    UPDATE webhook_endpoint_health SET
      status               = 'healthy',
      consecutive_failures = 0,
      last_error           = NULL,
      updated_at           = ?
    WHERE tenant_id = ? AND endpoint_url = ?
  `).bind(now, tenantId, endpointUrl).run();
  return (r.meta?.changes ?? 0) > 0;
}
