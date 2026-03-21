/**
 * Cron Orchestrator routes — manage and execute scheduled cron jobs
 * Mounted at: /v1/cron
 */

import { Hono } from 'hono';
import type { Context } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  registerJob,
  listJobs,
  updateJobStatus,
  getOverdueJobs,
  executeJob,
  runAllOverdue,
  getExecutionLogs,
  cleanOldLogs,
  getJobStats,
  seedSystemJobs,
  type JobStatus,
  type Schedule,
} from '../services/cron-orchestrator-service';

const app = new Hono<{ Bindings: Env }>();

// ── Admin key guard helper ────────────────────────────────────────────────────
function adminGuard(c: Context<{ Bindings: Env }>): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── GET /stats — aggregate job stats (auth, BEFORE /:id) ─────────────────────
app.get('/stats', auth(), async (c) => {
  try {
    const stats = await getJobStats(c.env.DB);
    return json(stats);
  } catch (err) {
    return json({ error: 'Failed to fetch stats', details: String(err) }, { status: 500 });
  }
});

// ── POST /seed — seed system jobs (auth, BEFORE /:id) ────────────────────────
app.post('/seed', auth(), async (c) => {
  try {
    const result = await seedSystemJobs(c.env.DB);
    return json(result);
  } catch (err) {
    return json({ error: 'Failed to seed jobs', details: String(err) }, { status: 500 });
  }
});

// ── GET /jobs — list jobs (auth, tenant-scoped) ───────────────────────────────
app.get('/jobs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const jobs = await listJobs(c.env.DB, tenantId);
    return json({ jobs, count: jobs.length });
  } catch (err) {
    return json({ error: 'Failed to list jobs', details: String(err) }, { status: 500 });
  }
});

// ── POST /jobs — register job (auth) ─────────────────────────────────────────
app.post('/jobs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const { job_type, schedule, config } = body;

  if (!job_type || !schedule) {
    return json({ error: 'job_type and schedule are required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  const validSchedules: Schedule[] = ['hourly', '6h', '12h', 'daily', 'weekly'];
  if (!validSchedules.includes(schedule as Schedule)) {
    return json({ error: `schedule must be one of: ${validSchedules.join(', ')}`, code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  try {
    const job = await registerJob(
      c.env.DB,
      tenantId,
      String(job_type),
      schedule as Schedule,
      (config as Record<string, unknown>) ?? {}
    );
    return json({ job }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to register job', details: String(err) }, { status: 500 });
  }
});

// ── PUT /jobs/:id/status — pause/resume/disable (auth) ───────────────────────
app.put('/jobs/:id/status', auth(), async (c) => {
  const jobId = c.req.param('id');
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const { status } = body;

  const validStatuses: JobStatus[] = ['active', 'paused', 'disabled'];
  if (!status || !validStatuses.includes(status as JobStatus)) {
    return json({ error: `status must be one of: ${validStatuses.join(', ')}`, code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  try {
    await updateJobStatus(c.env.DB, jobId, status as JobStatus);
    return json({ success: true, job_id: jobId, status });
  } catch (err) {
    return json({ error: 'Failed to update status', details: String(err) }, { status: 500 });
  }
});

// ── GET /jobs/:id/logs — execution logs for a job (auth) ─────────────────────
app.get('/jobs/:id/logs', auth(), async (c) => {
  const jobId = c.req.param('id');
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200);
  try {
    const logs = await getExecutionLogs(c.env.DB, jobId, limit);
    return json({ logs, count: logs.length });
  } catch (err) {
    return json({ error: 'Failed to fetch logs', details: String(err) }, { status: 500 });
  }
});

// ── GET /admin/overdue — list overdue jobs (X-Admin-Key) ─────────────────────
app.get('/admin/overdue', async (c) => {
  if (!adminGuard(c)) return json({ error: 'Admin key required', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const jobs = await getOverdueJobs(c.env.DB);
    return json({ jobs, count: jobs.length });
  } catch (err) {
    return json({ error: 'Failed to fetch overdue jobs', details: String(err) }, { status: 500 });
  }
});

// ── POST /admin/run — execute all overdue jobs (X-Admin-Key) ─────────────────
app.post('/admin/run', async (c) => {
  if (!adminGuard(c)) return json({ error: 'Admin key required', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const result = await runAllOverdue(c.env.DB);
    return json(result);
  } catch (err) {
    return json({ error: 'Failed to run overdue jobs', details: String(err) }, { status: 500 });
  }
});

// ── POST /admin/run/:id — execute single job on-demand (X-Admin-Key) ─────────
app.post('/admin/run/:id', async (c) => {
  if (!adminGuard(c)) return json({ error: 'Admin key required', code: 'FORBIDDEN' }, { status: 403 });
  const jobId = c.req.param('id');
  try {
    const job = await c.env.DB.prepare('SELECT * FROM cron_jobs WHERE id = ?').bind(jobId).first();
    if (!job) return json({ error: 'Job not found', code: 'NOT_FOUND' }, { status: 404 });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await executeJob(c.env.DB, job as any);
    return json({ success: true, job_id: jobId });
  } catch (err) {
    return json({ error: 'Failed to execute job', details: String(err) }, { status: 500 });
  }
});

// ── POST /admin/cleanup — delete old logs (X-Admin-Key) ──────────────────────
app.post('/admin/cleanup', async (c) => {
  if (!adminGuard(c)) return json({ error: 'Admin key required', code: 'FORBIDDEN' }, { status: 403 });
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const daysToKeep = Math.max(Number(body.days_to_keep ?? 30), 1);
  try {
    const deleted = await cleanOldLogs(c.env.DB, daysToKeep);
    return json({ deleted, days_to_keep: daysToKeep });
  } catch (err) {
    return json({ error: 'Failed to clean logs', details: String(err) }, { status: 500 });
  }
});

export { app as cronOrchestrator };
