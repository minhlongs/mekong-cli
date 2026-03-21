/**
 * Platform Health Service — aggregated system status, service checks, capacity metrics
 * Core queries: overview, service status, capacity
 * Feature coverage + endpoint count → platform-feature-registry.ts
 * Snapshot/history → platform-health-snapshot-service.ts
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface ServiceStatus {
  id: string;
  service_name: string;
  status: 'operational' | 'degraded' | 'down';
  last_check_at: string | null;
  response_time_ms: number | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
}

export interface PlatformOverview {
  tenants: { total: number; active_7d: number };
  missions: { total: number; today: number; success_rate: number };
  platform: { total_endpoints: number; total_migrations: number };
}

/**
 * Check D1 connectivity and Cloudflare Worker runtime, return live status for each
 */
export async function checkServiceHealth(db: D1Database): Promise<ServiceStatus[]> {
  const results: ServiceStatus[] = [];
  const now = new Date().toISOString();

  // D1 check
  const d1Start = Date.now();
  try {
    await db.prepare('SELECT 1').run();
    results.push({
      id: 'd1',
      service_name: 'd1_database',
      status: 'operational',
      last_check_at: now,
      response_time_ms: Date.now() - d1Start,
      error_message: null,
      metadata: { type: 'database' },
    });
  } catch (err) {
    results.push({
      id: 'd1',
      service_name: 'd1_database',
      status: 'down',
      last_check_at: now,
      response_time_ms: Date.now() - d1Start,
      error_message: String(err),
      metadata: { type: 'database' },
    });
  }

  // Workers runtime — always operational if we reach this code
  results.push({
    id: 'worker',
    service_name: 'cloudflare_worker',
    status: 'operational',
    last_check_at: now,
    response_time_ms: 0,
    error_message: null,
    metadata: { type: 'runtime' },
  });

  return results;
}

/**
 * Aggregate platform overview: tenants, missions, platform constants
 */
export async function getPlatformOverview(db: D1Database): Promise<PlatformOverview> {
  const [tenantRow, missionRow, todayRow] = await Promise.all([
    db.prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN created_at >= datetime('now','-7 days') THEN 1 ELSE 0 END) as active_7d
      FROM tenants
    `).first<{ total: number; active_7d: number }>(),
    db.prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
      FROM missions
    `).first<{ total: number; completed: number }>(),
    db.prepare(`
      SELECT COUNT(*) as today FROM missions WHERE created_at >= date('now')
    `).first<{ today: number }>(),
  ]);

  const total = missionRow?.total ?? 0;
  const completed = missionRow?.completed ?? 0;

  return {
    tenants: {
      total: tenantRow?.total ?? 0,
      active_7d: tenantRow?.active_7d ?? 0,
    },
    missions: {
      total,
      today: todayRow?.today ?? 0,
      success_rate: total > 0 ? Math.round((completed / total) * 100) : 100,
    },
    platform: {
      total_endpoints: 420,  // ~90 route files × avg 4-5 endpoints
      total_migrations: 78,  // migrations 0001–0078
    },
  };
}

/**
 * Return degraded or down services from service_status table
 */
export async function getDegradedServices(db: D1Database): Promise<ServiceStatus[]> {
  const rows = await db.prepare(`
    SELECT * FROM service_status WHERE status != 'operational'
    ORDER BY last_check_at DESC
  `).all<ServiceStatus>();
  return rows.results.map((r) => ({
    ...r,
    metadata: typeof r.metadata === 'string' ? JSON.parse(r.metadata) : r.metadata,
  }));
}

/**
 * List all service statuses from persistent service_status table
 */
export async function getServiceStatuses(db: D1Database): Promise<ServiceStatus[]> {
  const rows = await db.prepare(
    'SELECT * FROM service_status ORDER BY service_name'
  ).all<ServiceStatus>();
  return rows.results.map((r) => ({
    ...r,
    metadata: typeof r.metadata === 'string' ? JSON.parse(r.metadata) : r.metadata,
  }));
}

/**
 * Upsert a service status entry in service_status table
 */
export async function updateServiceStatus(
  db: D1Database,
  serviceName: string,
  status: 'operational' | 'degraded' | 'down',
  responseTimeMs: number,
  error?: string,
): Promise<void> {
  await db.prepare(`
    INSERT INTO service_status (id, service_name, status, last_check_at, response_time_ms, error_message, metadata)
    VALUES (?, ?, ?, datetime('now'), ?, ?, '{}')
    ON CONFLICT(service_name) DO UPDATE SET
      status=excluded.status,
      last_check_at=excluded.last_check_at,
      response_time_ms=excluded.response_time_ms,
      error_message=excluded.error_message
  `).bind(
    crypto.randomUUID(), serviceName, status, responseTimeMs, error ?? null
  ).run();
}

/**
 * D1 row counts for key tables — system capacity overview
 */
export async function getSystemCapacity(db: D1Database) {
  const [tenants, missions, auditLogs] = await Promise.all([
    db.prepare('SELECT COUNT(*) as count FROM tenants').first<{ count: number }>(),
    db.prepare('SELECT COUNT(*) as count FROM missions').first<{ count: number }>(),
    db.prepare('SELECT COUNT(*) as count FROM audit_logs').first<{ count: number }>(),
  ]);
  return {
    tenants: tenants?.count ?? 0,
    missions: missions?.count ?? 0,
    audit_logs: auditLogs?.count ?? 0,
  };
}
