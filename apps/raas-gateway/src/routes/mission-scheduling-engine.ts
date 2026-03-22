/**
 * Mission Scheduling Engine routes
 * CRUD for scheduled jobs, executions, skip rules + admin overview
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionSchedulingService as svc } from '../services/mission-scheduling-engine-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// --- Admin (no tenant auth — admin key only) ---

app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Unauthorized', code: 'ADMIN_KEY_REQUIRED' }, 401);
  }
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to get overview';
    return c.json({ success: false, error: msg }, 500);
  }
});

// --- All job routes require tenant auth ---

app.use('/jobs/*', auth());

app.get('/jobs', async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await svc.listJobs(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to list jobs';
    return c.json({ success: false, error: msg }, 500);
  }
});

app.post('/jobs', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  if (!body.name?.trim()) return c.json({ error: 'name is required' }, 400);
  if (!body.cron_expression?.trim()) return c.json({ error: 'cron_expression is required' }, 400);
  try {
    const data = await svc.createJob(c.env.DB, tenant.tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to create job';
    return c.json({ success: false, error: msg }, 400);
  }
});

app.get('/jobs/:id', async (c) => {
  const tenant = getTenant(c);
  const data = await svc.getJob(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!data) return c.json({ error: 'Not found' }, 404);
  return c.json({ success: true, data });
});

app.put('/jobs/:id', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  try {
    const data = await svc.updateJob(c.env.DB, tenant.tenantId, c.req.param('id'), body);
    if (!data) return c.json({ error: 'Not found' }, 404);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to update job';
    return c.json({ success: false, error: msg }, 400);
  }
});

app.delete('/jobs/:id', async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await svc.deleteJob(c.env.DB, tenant.tenantId, c.req.param('id'));
    return c.json({ success: true, data });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to delete job';
    return c.json({ success: false, error: msg }, 500);
  }
});

app.post('/jobs/:id/pause', async (c) => {
  const tenant = getTenant(c);
  const data = await svc.pauseJob(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!data) return c.json({ error: 'Not found' }, 404);
  return c.json({ success: true, data });
});

app.post('/jobs/:id/resume', async (c) => {
  const tenant = getTenant(c);
  const data = await svc.resumeJob(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!data) return c.json({ error: 'Not found' }, 404);
  return c.json({ success: true, data });
});

app.post('/jobs/:id/trigger', async (c) => {
  const tenant = getTenant(c);
  const data = await svc.triggerJob(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!data) return c.json({ error: 'Not found' }, 404);
  return c.json({ success: true, data });
});

app.get('/jobs/:id/executions', async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await svc.listExecutions(c.env.DB, tenant.tenantId, c.req.param('id'));
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to list executions';
    return c.json({ success: false, error: msg }, 500);
  }
});

app.get('/jobs/:id/skip-rules', async (c) => {
  const tenant = getTenant(c);
  // Verify job belongs to tenant before listing rules
  const job = await svc.getJob(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!job) return c.json({ error: 'Not found' }, 404);
  const data = await svc.listSkipRules(c.env.DB, c.req.param('id'));
  return c.json({ success: true, data, total: data.length });
});

app.post('/jobs/:id/skip-rules', async (c) => {
  const tenant = getTenant(c);
  const job = await svc.getJob(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!job) return c.json({ error: 'Not found' }, 404);
  const body = await c.req.json().catch(() => ({}));
  if (!body.rule_type?.trim()) return c.json({ error: 'rule_type is required' }, 400);
  try {
    const data = await svc.addSkipRule(c.env.DB, c.req.param('id'), body);
    return c.json({ success: true, data }, 201);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to add skip rule';
    return c.json({ success: false, error: msg }, 400);
  }
});

// Executions by execution ID (not job-scoped)
app.use('/executions/*', auth());

app.get('/executions/:id', async (c) => {
  const tenant = getTenant(c);
  const data = await svc.getExecution(c.env.DB, tenant.tenantId, c.req.param('id'));
  if (!data) return c.json({ error: 'Not found' }, 404);
  return c.json({ success: true, data });
});

export { app as missionSchedulingEngine };
