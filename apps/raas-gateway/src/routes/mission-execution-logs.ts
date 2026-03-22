/**
 * Mission Execution Logs routes — per-step log entries and summaries
 *
 * Authenticated routes (tenant-scoped):
 *   GET  /logs        — list execution log entries for the authenticated tenant
 *   POST /logs        — create a new execution log entry
 *   GET  /summaries   — list execution summaries for the authenticated tenant
 *
 * Admin route (X-Admin-Key header):
 *   GET  /admin/overview — aggregated stats across all tenants
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionExecutionLogsService } from '../services/mission-execution-logs';

// Inline Bindings type — avoids importing from index.ts
type Bindings = {
  DB: any;
  ADMIN_KEY?: string;
  [key: string]: unknown;
};

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /logs
 * List execution log entries for the authenticated tenant.
 * Query params: mission_id (optional), limit (default 50, max 200)
 */
app.get('/logs', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.query('mission_id');
  const limit = parseInt(c.req.query('limit') ?? '50', 10);

  try {
    const result = await missionExecutionLogsService.listLogs(c.env.DB, tenant.tenantId, {
      missionId: missionId || undefined,
      limit: isNaN(limit) ? 50 : limit,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /logs
 * Create a new execution log entry for a mission step.
 * Body: { mission_id, step_name, message, log_level?, metadata?, duration_ms? }
 */
app.post('/logs', auth(), async (c) => {
  const tenant = getTenant(c);

  try {
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

    const missionId = typeof body.mission_id === 'string' ? body.mission_id.trim() : '';
    const stepName = typeof body.step_name === 'string' ? body.step_name.trim() : '';
    const message = typeof body.message === 'string' ? body.message.trim() : '';

    if (!missionId || !stepName || !message) {
      return c.json({ error: 'mission_id, step_name, and message are required' }, 400);
    }

    const result = await missionExecutionLogsService.createLog(c.env.DB, {
      tenant_id: tenant.tenantId,
      mission_id: missionId,
      step_name: stepName,
      log_level: typeof body.log_level === 'string' ? body.log_level : undefined,
      message,
      metadata: typeof body.metadata === 'string' ? body.metadata : undefined,
      duration_ms: typeof body.duration_ms === 'number' ? body.duration_ms : undefined,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /summaries
 * List execution summaries for the authenticated tenant.
 * Query params: mission_id (optional), limit (default 20, max 100)
 */
app.get('/summaries', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.query('mission_id');
  const limit = parseInt(c.req.query('limit') ?? '20', 10);

  try {
    const result = await missionExecutionLogsService.getSummaries(c.env.DB, tenant.tenantId, {
      missionId: missionId || undefined,
      limit: isNaN(limit) ? 20 : limit,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /admin/overview
 * Aggregated stats across all tenants.
 * Requires X-Admin-Key header matching ADMIN_KEY env var.
 */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await missionExecutionLogsService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as missionExecutionLogs };
