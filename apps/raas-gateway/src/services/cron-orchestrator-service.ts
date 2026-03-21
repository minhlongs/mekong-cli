/**
 * Cron Orchestrator Service — centralized cron job registry, scheduling, and execution dispatch
 * Job dispatch logic lives in cron-job-executor.ts (split for file-size compliance)
 */

import type { D1Database } from '@cloudflare/workers-types';
import { dispatchJob } from './cron-job-executor';

export type JobStatus = 'active' | 'paused' | 'disabled';
export type Schedule = 'hourly' | '6h' | '12h' | 'daily' | 'weekly';

export interface CronJob {
  id: string;
  tenant_id: string | null;
  job_type: string;
  schedule: Schedule;
  last_run_at: string | null;
  next_run_at: string | null;
  status: JobStatus;
  config: string;
  created_at: string;
}

export interface CronExecLog {
  id: string;
  job_id: string;
  job_type: string;
  started_at: string;
  completed_at: string | null;
  status: 'running' | 'success' | 'failed';
  result: string | null;
  error: string | null;
}

/** Calculate next_run_at from schedule string */
function calcNextRun(schedule: Schedule): string {
  const ms: Record<Schedule, number> = {
    hourly: 60 * 60 * 1000,
    '6h': 6 * 60 * 60 * 1000,
    '12h': 12 * 60 * 60 * 1000,
    daily: 24 * 60 * 60 * 1000,
    weekly: 7 * 24 * 60 * 60 * 1000,
  };
  return new Date(Date.now() + (ms[schedule] ?? ms.daily)).toISOString();
}

export async function registerJob(
  db: D1Database,
  tenantId: string | null,
  jobType: string,
  schedule: Schedule,
  config: Record<string, unknown> = {}
): Promise<CronJob> {
  const id = crypto.randomUUID();
  const nextRunAt = calcNextRun(schedule);
  await db.prepare(
    `INSERT INTO cron_jobs (id, tenant_id, job_type, schedule, next_run_at, config)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, jobType, schedule, nextRunAt, JSON.stringify(config)).run();
  return db.prepare('SELECT * FROM cron_jobs WHERE id = ?').bind(id).first<CronJob>() as Promise<CronJob>;
}

export async function listJobs(db: D1Database, tenantId?: string): Promise<CronJob[]> {
  if (tenantId) {
    const r = await db.prepare('SELECT * FROM cron_jobs WHERE tenant_id = ? ORDER BY created_at DESC').bind(tenantId).all<CronJob>();
    return r.results;
  }
  const r = await db.prepare('SELECT * FROM cron_jobs ORDER BY created_at DESC').all<CronJob>();
  return r.results;
}

export async function updateJobStatus(db: D1Database, jobId: string, status: JobStatus): Promise<void> {
  await db.prepare('UPDATE cron_jobs SET status = ? WHERE id = ?').bind(status, jobId).run();
}

export async function getOverdueJobs(db: D1Database): Promise<CronJob[]> {
  const now = new Date().toISOString();
  const r = await db.prepare(
    `SELECT * FROM cron_jobs WHERE status = 'active' AND (next_run_at IS NULL OR next_run_at <= ?) ORDER BY next_run_at ASC`
  ).bind(now).all<CronJob>();
  return r.results;
}

export async function executeJob(db: D1Database, job: CronJob): Promise<void> {
  const logId = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO cron_execution_logs (id, job_id, job_type) VALUES (?, ?, ?)`
  ).bind(logId, job.id, job.job_type).run();

  try {
    const result = await dispatchJob(db, job);
    await db.prepare(
      `UPDATE cron_execution_logs SET status = 'success', completed_at = datetime('now'), result = ? WHERE id = ?`
    ).bind(JSON.stringify(result), logId).run();
  } catch (err) {
    await db.prepare(
      `UPDATE cron_execution_logs SET status = 'failed', completed_at = datetime('now'), error = ? WHERE id = ?`
    ).bind(String(err), logId).run();
  }
}

export async function runAllOverdue(db: D1Database): Promise<{ ran: number; errors: number }> {
  const jobs = await getOverdueJobs(db);
  let errors = 0;
  for (const job of jobs) {
    try {
      await executeJob(db, job);
    } catch {
      errors++;
    }
    const nextRunAt = calcNextRun(job.schedule as Schedule);
    await db.prepare(
      `UPDATE cron_jobs SET last_run_at = datetime('now'), next_run_at = ? WHERE id = ?`
    ).bind(nextRunAt, job.id).run();
  }
  return { ran: jobs.length, errors };
}

export async function getExecutionLogs(db: D1Database, jobId?: string, limit = 50): Promise<CronExecLog[]> {
  const cap = Math.min(limit, 200);
  if (jobId) {
    const r = await db.prepare(
      'SELECT * FROM cron_execution_logs WHERE job_id = ? ORDER BY started_at DESC LIMIT ?'
    ).bind(jobId, cap).all<CronExecLog>();
    return r.results;
  }
  const r = await db.prepare(
    'SELECT * FROM cron_execution_logs ORDER BY started_at DESC LIMIT ?'
  ).bind(cap).all<CronExecLog>();
  return r.results;
}

export async function cleanOldLogs(db: D1Database, daysToKeep: number): Promise<number> {
  const cutoff = new Date(Date.now() - daysToKeep * 24 * 60 * 60 * 1000).toISOString();
  const r = await db.prepare(
    `DELETE FROM cron_execution_logs WHERE started_at < ?`
  ).bind(cutoff).run();
  return r.meta.changes ?? 0;
}

export async function getJobStats(db: D1Database): Promise<Record<string, number>> {
  const today = new Date().toISOString().slice(0, 10);
  const [total, active, paused, execToday] = await Promise.all([
    db.prepare('SELECT COUNT(*) as n FROM cron_jobs').first<{ n: number }>(),
    db.prepare("SELECT COUNT(*) as n FROM cron_jobs WHERE status = 'active'").first<{ n: number }>(),
    db.prepare("SELECT COUNT(*) as n FROM cron_jobs WHERE status = 'paused'").first<{ n: number }>(),
    db.prepare("SELECT COUNT(*) as n FROM cron_execution_logs WHERE started_at >= ?").bind(today).first<{ n: number }>(),
  ]);
  return {
    total: total?.n ?? 0,
    active: active?.n ?? 0,
    paused: paused?.n ?? 0,
    executions_today: execToday?.n ?? 0,
  };
}

/** Seed default system jobs (idempotent — skip if job_type already exists with no tenant) */
export async function seedSystemJobs(db: D1Database): Promise<{ seeded: number }> {
  const defaults: Array<{ type: string; schedule: Schedule; config: Record<string, unknown> }> = [
    { type: 'data_retention_purge', schedule: 'daily', config: {} },
    { type: 'usage_forecast_collect', schedule: 'daily', config: {} },
    { type: 'error_budget_check', schedule: 'hourly', config: {} },
  ];
  let seeded = 0;
  for (const d of defaults) {
    const existing = await db.prepare(
      "SELECT id FROM cron_jobs WHERE job_type = ? AND tenant_id IS NULL"
    ).bind(d.type).first();
    if (!existing) {
      await registerJob(db, null, d.type, d.schedule, d.config);
      seeded++;
    }
  }
  return { seeded };
}
