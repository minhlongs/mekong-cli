/**
 * Webhook Analytics Service — delivery stats, endpoint health, tenant overview
 * Endpoint health CRUD lives in webhook-endpoint-health-service.ts
 */

import {
  updateEndpointHealth,
  listEndpoints,
} from './webhook-endpoint-health-service';

// Re-export endpoint-health functions so callers only need this module
export {
  updateEndpointHealth,
  getEndpointHealth,
  listEndpoints,
  getFailedEndpoints,
  resetEndpointHealth,
} from './webhook-endpoint-health-service';

type DB = D1Database;

/** Today's date in YYYY-MM-DD format */
function todayDate(): string {
  return new Date().toISOString().slice(0, 10);
}

// ── Delivery Recording ──────────────────────────────────────────────────────

/** Record a single webhook delivery attempt — upserts daily stats + endpoint health */
export async function recordDelivery(
  db: DB,
  tenantId: string,
  endpointUrl: string,
  success: boolean,
  retried: boolean,
  latencyMs: number
): Promise<void> {
  const date = todayDate();
  const successVal = success ? 1 : 0;
  const failedVal = success ? 0 : 1;
  const retriedVal = retried ? 1 : 0;

  await db.prepare(`
    INSERT INTO webhook_delivery_stats
      (tenant_id, date, total_deliveries, successful, failed, retried, avg_latency_ms, p95_latency_ms)
    VALUES (?, ?, 1, ?, ?, ?, ?, ?)
    ON CONFLICT(tenant_id, date) DO UPDATE SET
      total_deliveries = total_deliveries + 1,
      successful       = successful + excluded.successful,
      failed           = failed + excluded.failed,
      retried          = retried + excluded.retried,
      avg_latency_ms   = (avg_latency_ms * total_deliveries + excluded.avg_latency_ms) / (total_deliveries + 1),
      p95_latency_ms   = MAX(p95_latency_ms, excluded.p95_latency_ms * 0.95)
  `).bind(tenantId, date, successVal, failedVal, retriedVal, latencyMs, latencyMs).run();

  await updateEndpointHealth(db, tenantId, endpointUrl, success, latencyMs);
}

// ── Delivery Stats ──────────────────────────────────────────────────────────

/** Aggregated delivery stats for a tenant over the last N days */
export async function getDeliveryStats(
  db: DB,
  tenantId: string,
  days = 7
): Promise<Record<string, unknown>> {
  const r = await db.prepare(`
    SELECT
      SUM(total_deliveries) AS total_deliveries,
      SUM(successful)       AS successful,
      SUM(failed)           AS failed,
      SUM(retried)          AS retried,
      AVG(avg_latency_ms)   AS avg_latency_ms,
      MAX(p95_latency_ms)   AS p95_latency_ms
    FROM webhook_delivery_stats
    WHERE tenant_id = ? AND date >= date('now', ?)
  `).bind(tenantId, `-${days} days`).first();
  return (r as Record<string, unknown>) ?? {};
}

/** Day-by-day delivery timeline for a tenant */
export async function getDeliveryTimeline(
  db: DB,
  tenantId: string,
  days = 30
): Promise<Record<string, unknown>[]> {
  const r = await db.prepare(`
    SELECT date, total_deliveries, successful, failed, retried, avg_latency_ms, p95_latency_ms
    FROM webhook_delivery_stats
    WHERE tenant_id = ? AND date >= date('now', ?)
    ORDER BY date ASC
  `).bind(tenantId, `-${days} days`).all();
  return r.results as Record<string, unknown>[];
}

// ── Overview & Admin ────────────────────────────────────────────────────────

/** High-level webhook summary — 30-day stats + endpoint health counts */
export async function getWebhookOverview(
  db: DB,
  tenantId: string
): Promise<Record<string, unknown>> {
  const [stats, endpoints] = await Promise.all([
    getDeliveryStats(db, tenantId, 30),
    listEndpoints(db, tenantId),
  ]);
  const healthy  = endpoints.filter(e => e['status'] === 'healthy').length;
  const degraded = endpoints.filter(e => e['status'] === 'degraded').length;
  const down     = endpoints.filter(e => e['status'] === 'down').length;
  return { stats, endpoint_summary: { total: endpoints.length, healthy, degraded, down } };
}

/** Admin — aggregate webhook analytics across ALL tenants (last 30 days) */
export async function getAdminWebhookAnalytics(
  db: DB
): Promise<Record<string, unknown>> {
  const [deliveries, endpointHealth] = await Promise.all([
    db.prepare(`
      SELECT
        COUNT(DISTINCT tenant_id) AS active_tenants,
        SUM(total_deliveries)     AS total_deliveries,
        SUM(successful)           AS total_successful,
        SUM(failed)               AS total_failed,
        AVG(avg_latency_ms)       AS avg_latency_ms
      FROM webhook_delivery_stats
      WHERE date >= date('now', '-30 days')
    `).first(),
    db.prepare(`
      SELECT status, COUNT(*) AS count
      FROM webhook_endpoint_health
      GROUP BY status
    `).all(),
  ]);
  return {
    last_30_days: deliveries,
    endpoint_health_breakdown: endpointHealth.results,
  };
}
