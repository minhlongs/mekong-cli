/**
 * SLA Monitoring Service — uptime tracking and SLA compliance reporting
 * Tracks platform uptime, response times, and breach detection per tenant tier
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface SLATarget {
  tier: string;
  uptime_percent: number;
  response_time_p95_ms: number;
  support_response_hours: number;
  data_retention_days: number;
}

export interface UptimeRecord {
  id: string;
  check_type: string;
  status: 'up' | 'down' | 'degraded';
  latency_ms: number;
  checked_at: string;
}

export interface SLAReport {
  tenant_id: string;
  tier: string;
  period_days: number;
  target: SLATarget;
  actual: {
    uptime_percent: number;
    response_time_p95_ms: number;
    total_checks: number;
    failed_checks: number;
  };
  compliant: boolean;
  breaches: string[];
  generated_at: string;
}

// Per-tier SLA targets
const SLA_TARGETS: Record<string, SLATarget> = {
  starter:    { tier: 'starter',    uptime_percent: 99.5,  response_time_p95_ms: 2000, support_response_hours: 48, data_retention_days: 30  },
  pro:        { tier: 'pro',        uptime_percent: 99.9,  response_time_p95_ms: 1000, support_response_hours: 24, data_retention_days: 90  },
  agency:     { tier: 'agency',     uptime_percent: 99.9,  response_time_p95_ms: 500,  support_response_hours: 12, data_retention_days: 180 },
  master:     { tier: 'master',     uptime_percent: 99.95, response_time_p95_ms: 300,  support_response_hours: 4,  data_retention_days: 365 },
  enterprise: { tier: 'enterprise', uptime_percent: 99.99, response_time_p95_ms: 200,  support_response_hours: 1,  data_retention_days: 730 },
};

/** Return SLA target for a tier; defaults to starter if unknown */
export function getSLATarget(tier: string): SLATarget {
  return SLA_TARGETS[tier] ?? SLA_TARGETS['starter'];
}

/** Return all SLA tier targets (public info) */
export function getSLATiers(): Record<string, SLATarget> {
  return SLA_TARGETS;
}

/** Insert a new uptime check row */
export async function recordUptimeCheck(
  db: D1Database,
  checkType: string,
  status: 'up' | 'down' | 'degraded',
  latencyMs: number,
  details?: string
): Promise<void> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO uptime_checks (id, check_type, status, latency_ms, details)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(id, checkType, status, latencyMs, details ?? null).run();
}

/** Calculate uptime percentage from uptime_checks for the given window */
export async function getUptimePercentage(
  db: D1Database,
  days = 30
): Promise<{ uptime_percent: number; total_checks: number; failed_checks: number }> {
  const row = await db.prepare(
    `SELECT COUNT(*) as total,
            SUM(CASE WHEN status != 'up' THEN 1 ELSE 0 END) as failed
     FROM uptime_checks
     WHERE checked_at >= datetime('now', ? || ' days')`
  ).bind(`-${days}`).first<{ total: number; failed: number }>();

  const total = row?.total ?? 0;
  const failed = row?.failed ?? 0;
  const uptime_percent = total === 0 ? 100 : Math.round(((total - failed) / total) * 10000) / 100;
  return { uptime_percent, total_checks: total, failed_checks: failed };
}

/** Approximate P95 latency from stored checks over given window */
export async function getResponseTimeP95(db: D1Database, days = 30): Promise<number> {
  const rows = await db.prepare(
    `SELECT latency_ms FROM uptime_checks
     WHERE checked_at >= datetime('now', ? || ' days')
     ORDER BY latency_ms ASC`
  ).bind(`-${days}`).all<{ latency_ms: number }>();

  const latencies = rows.results.map((r) => r.latency_ms);
  if (!latencies.length) return 0;
  const idx = Math.floor(latencies.length * 0.95);
  return latencies[Math.min(idx, latencies.length - 1)];
}

/** Full SLA compliance report comparing actuals to tier targets */
export async function getSLAReport(
  db: D1Database,
  tenantId: string,
  tier: string,
  days = 30
): Promise<SLAReport> {
  const target = getSLATarget(tier);
  const { uptime_percent, total_checks, failed_checks } = await getUptimePercentage(db, days);
  const p95 = await getResponseTimeP95(db, days);

  const breaches: string[] = [];
  if (uptime_percent < target.uptime_percent) {
    breaches.push(`Uptime ${uptime_percent}% below target ${target.uptime_percent}%`);
  }
  if (p95 > target.response_time_p95_ms) {
    breaches.push(`P95 latency ${p95}ms exceeds target ${target.response_time_p95_ms}ms`);
  }

  return {
    tenant_id: tenantId,
    tier,
    period_days: days,
    target,
    actual: { uptime_percent, response_time_p95_ms: p95, total_checks, failed_checks },
    compliant: breaches.length === 0,
    breaches,
    generated_at: new Date().toISOString(),
  };
}

/** List recorded SLA breaches from sla_breaches table */
export async function getSLABreaches(
  db: D1Database,
  days = 30
): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT id, breach_type, target_value, actual_value, tier, started_at, resolved_at, created_at
     FROM sla_breaches
     WHERE created_at >= datetime('now', ? || ' days')
     ORDER BY created_at DESC`
  ).bind(`-${days}`).all();
  return rows.results;
}

/** Recent uptime check history */
export async function getUptimeHistory(
  db: D1Database,
  days = 30,
  limit = 100
): Promise<UptimeRecord[]> {
  const rows = await db.prepare(
    `SELECT id, check_type, status, latency_ms, checked_at
     FROM uptime_checks
     WHERE checked_at >= datetime('now', ? || ' days')
     ORDER BY checked_at DESC
     LIMIT ?`
  ).bind(`-${days}`, limit).all<UptimeRecord>();
  return rows.results;
}

/** Current platform operational status derived from recent checks */
export async function getCurrentStatus(db: D1Database): Promise<{
  status: 'operational' | 'degraded' | 'outage';
  last_check: string | null;
  uptime_30d: number;
}> {
  const latest = await db.prepare(
    `SELECT status, checked_at FROM uptime_checks ORDER BY checked_at DESC LIMIT 1`
  ).first<{ status: string; checked_at: string }>();

  const { uptime_percent } = await getUptimePercentage(db, 30);

  let status: 'operational' | 'degraded' | 'outage' = 'operational';
  if (latest?.status === 'down') status = 'outage';
  else if (latest?.status === 'degraded') status = 'degraded';

  return { status, last_check: latest?.checked_at ?? null, uptime_30d: uptime_percent };
}
