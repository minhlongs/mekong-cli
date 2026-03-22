/**
 * Mission Analytics Dashboard Routes
 * GET  /snapshots       — list snapshots for authenticated tenant
 * POST /snapshots       — create a snapshot for authenticated tenant
 * GET  /widgets         — list widgets for authenticated tenant
 * GET  /admin/overview  — platform-wide overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionAnalyticsDashboardService as svc } from '../services/mission-analytics-dashboard';

const app = new Hono<{ Bindings: Env }>();

// ── GET /snapshots ─────────────────────────────────────────────────────────

app.get('/snapshots', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const period = c.req.query('period');
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;

    const result = await svc.listSnapshots(c.env.DB, tenant.tenantId, { period, limit });
    if (!result.success) return c.json({ error: result.error }, 400);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list snapshots' }, 500);
  }
});

// ── POST /snapshots ────────────────────────────────────────────────────────

app.post('/snapshots', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    if (!body.period?.trim()) {
      return c.json({ error: 'period is required' }, 400);
    }

    const result = await svc.createSnapshot(c.env.DB, tenant.tenantId, {
      period: body.period,
      total_missions: typeof body.total_missions === 'number' ? body.total_missions : undefined,
      completed_missions: typeof body.completed_missions === 'number' ? body.completed_missions : undefined,
      failed_missions: typeof body.failed_missions === 'number' ? body.failed_missions : undefined,
      avg_duration_ms: typeof body.avg_duration_ms === 'number' ? body.avg_duration_ms : undefined,
    });

    if (!result.success) return c.json({ error: result.error }, 400);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create snapshot' }, 500);
  }
});

// ── GET /widgets ───────────────────────────────────────────────────────────

app.get('/widgets', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await svc.getWidgets(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 400);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch widgets' }, 500);
  }
});

// ── GET /admin/overview ────────────────────────────────────────────────────

app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 400);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as missionAnalyticsDashboard };
