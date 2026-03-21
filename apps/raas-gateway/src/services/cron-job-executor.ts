/**
 * Cron Job Executor — dispatches cron jobs by type, calling existing service functions
 * Imported by cron-orchestrator-service.ts to keep file sizes under 200 lines
 */

import type { D1Database } from '@cloudflare/workers-types';
import type { CronJob } from './cron-orchestrator-service';

type DispatchResult = Record<string, unknown>;

/** Stub: purge data retention records beyond retention window */
async function runDataRetentionPurge(db: D1Database, config: Record<string, unknown>): Promise<DispatchResult> {
  const daysToKeep = Number(config.days_to_keep ?? 90);
  const cutoff = new Date(Date.now() - daysToKeep * 24 * 60 * 60 * 1000).toISOString();
  const r = await db.prepare(
    "DELETE FROM audit_logs WHERE created_at < ?"
  ).bind(cutoff).run();
  return { purged_rows: r.meta.changes ?? 0, cutoff };
}

/** Stub: collect usage forecast snapshot */
async function runUsageForecastCollect(db: D1Database, _config: Record<string, unknown>): Promise<DispatchResult> {
  const snapshot = await db.prepare(
    `SELECT tenant_id, COUNT(*) as total_missions
     FROM missions
     WHERE created_at >= datetime('now', '-1 day')
     GROUP BY tenant_id`
  ).all();
  return { snapshot_rows: snapshot.results.length, collected_at: new Date().toISOString() };
}

/** Stub: check error budgets and flag tenants over threshold */
async function runErrorBudgetCheck(db: D1Database, _config: Record<string, unknown>): Promise<DispatchResult> {
  const r = await db.prepare(
    `SELECT tenant_id, COUNT(*) as errors
     FROM audit_logs
     WHERE action LIKE '%error%' AND created_at >= datetime('now', '-1 hour')
     GROUP BY tenant_id`
  ).all();
  return { tenants_checked: r.results.length, checked_at: new Date().toISOString() };
}

/** Stub: execute a scheduled mission job */
async function runScheduledMission(db: D1Database, config: Record<string, unknown>): Promise<DispatchResult> {
  const missionId = config.mission_id as string | undefined;
  if (!missionId) return { skipped: true, reason: 'no mission_id in config' };
  // Actual execution would call mission-service; here we record intent
  return { mission_id: missionId, triggered_at: new Date().toISOString() };
}

/** Stub: take a KPI snapshot for platform analytics */
async function runKpiSnapshot(db: D1Database, _config: Record<string, unknown>): Promise<DispatchResult> {
  const [tenants, missions] = await Promise.all([
    db.prepare('SELECT COUNT(*) as n FROM tenants').first<{ n: number }>(),
    db.prepare("SELECT COUNT(*) as n FROM missions WHERE created_at >= datetime('now', '-1 day')").first<{ n: number }>(),
  ]);
  return {
    total_tenants: tenants?.n ?? 0,
    missions_last_24h: missions?.n ?? 0,
    snapshot_at: new Date().toISOString(),
  };
}

/** Route a cron job to its executor by job_type */
export async function dispatchJob(db: D1Database, job: CronJob): Promise<DispatchResult> {
  const config = (() => {
    try { return JSON.parse(job.config) as Record<string, unknown>; } catch { return {}; }
  })();

  switch (job.job_type) {
    case 'data_retention_purge':
      return runDataRetentionPurge(db, config);
    case 'usage_forecast_collect':
      return runUsageForecastCollect(db, config);
    case 'error_budget_check':
      return runErrorBudgetCheck(db, config);
    case 'scheduled_mission':
      return runScheduledMission(db, config);
    case 'kpi_snapshot':
      return runKpiSnapshot(db, config);
    default:
      throw new Error(`Unknown job_type: ${job.job_type}`);
  }
}
