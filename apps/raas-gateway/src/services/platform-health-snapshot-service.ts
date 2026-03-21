/**
 * Platform Health Snapshot Service — score calculation, history, trend tracking
 * Depends on platform-health-service for getPlatformOverview and getServiceStatuses
 */

import type { D1Database } from '@cloudflare/workers-types';
import { getPlatformOverview, getServiceStatuses } from './platform-health-service';

export interface HealthSnapshot {
  id: string;
  snapshot_type: string;
  metrics: Record<string, unknown>;
  score: number;
  created_at: string;
}

/**
 * Calculate overall platform score (0-100):
 * - 40pts: all services operational
 * - 30pts: mission success rate
 * - 30pts: active tenant ratio (active_7d / total)
 */
export async function takeHealthSnapshot(db: D1Database): Promise<HealthSnapshot> {
  const [overview, services] = await Promise.all([
    getPlatformOverview(db),
    getServiceStatuses(db),
  ]);

  // Service uptime score (40 pts)
  const degraded = services.filter((s) => s.status === 'degraded').length;
  const down = services.filter((s) => s.status === 'down').length;
  const totalServices = Math.max(services.length, 1);
  const serviceScore = Math.round(
    40 * ((totalServices - degraded * 0.5 - down) / totalServices)
  );

  // Mission success score (30 pts)
  const missionScore = Math.round(30 * (overview.missions.success_rate / 100));

  // Active tenant ratio score (30 pts)
  const activeTenantRatio =
    overview.tenants.total > 0
      ? overview.tenants.active_7d / overview.tenants.total
      : 1;
  const tenantScore = Math.round(30 * Math.min(activeTenantRatio, 1));

  const score = Math.max(0, Math.min(100, serviceScore + missionScore + tenantScore));

  const metrics = {
    service_score: serviceScore,
    mission_score: missionScore,
    tenant_score: tenantScore,
    services_total: services.length,
    services_degraded: degraded,
    services_down: down,
    mission_success_rate: overview.missions.success_rate,
    active_tenant_ratio: Math.round(activeTenantRatio * 100),
  };

  const id = crypto.randomUUID();
  await db.prepare(`
    INSERT INTO platform_health_snapshots (id, snapshot_type, metrics, score, created_at)
    VALUES (?, 'platform', ?, ?, datetime('now'))
  `).bind(id, JSON.stringify(metrics), score).run();

  return {
    id,
    snapshot_type: 'platform',
    metrics,
    score,
    created_at: new Date().toISOString(),
  };
}

/**
 * Retrieve health snapshots over the past N days (default 7)
 */
export async function getHealthHistory(
  db: D1Database,
  days = 7,
): Promise<HealthSnapshot[]> {
  const rows = await db.prepare(`
    SELECT * FROM platform_health_snapshots
    WHERE created_at >= datetime('now', ?)
    ORDER BY created_at DESC
    LIMIT 200
  `).bind(`-${days} days`).all<{
    id: string;
    snapshot_type: string;
    metrics: string;
    score: number;
    created_at: string;
  }>();

  return rows.results.map((r) => ({
    ...r,
    metrics: typeof r.metrics === 'string' ? JSON.parse(r.metrics) : r.metrics,
  }));
}
