/**
 * Platform Analytics Dashboard routes
 * Auth endpoints: widgets + saved queries (JWT/API key via auth middleware)
 * Admin endpoints: snapshots + overview (X-Admin-Key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { platformAnalyticsDashboardService as svc } from '../services/platform-analytics-dashboard-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// ── Auth middleware helper ─────────────────────────────────────────────────────

function requireAdmin(c: any): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ── Widget routes (auth) ───────────────────────────────────────────────────────

app.get('/widgets', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const widgets = await svc.listWidgets(c.env.DB, tenant.tenantId);
    return c.json({ widgets, count: widgets.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.post('/widgets', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{
      name: string;
      widget_type: string;
      query_json?: string;
      config_json?: string;
      position_json?: string;
    }>();
    if (!body.name) return c.json({ error: 'name is required' }, 400);
    if (!body.widget_type) return c.json({ error: 'widget_type is required' }, 400);
    const widget = await svc.createWidget(c.env.DB, tenant.tenantId, body);
    return c.json(widget, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.put('/widgets/:id', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const id = c.req.param('id');
    const body = await c.req.json<{ name?: string; config_json?: string; position_json?: string }>();
    const widget = await svc.updateWidget(c.env.DB, tenant.tenantId, id, body);
    if (!widget) return c.json({ error: 'Widget not found or is a system widget' }, 404);
    return c.json(widget);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.delete('/widgets/:id', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const id = c.req.param('id');
    const deleted = await svc.deleteWidget(c.env.DB, tenant.tenantId, id);
    if (!deleted) return c.json({ error: 'Widget not found or is a system widget' }, 404);
    return c.json({ deleted: true });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// ── Saved query routes (auth) ─────────────────────────────────────────────────

app.get('/queries', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const queries = await svc.listSavedQueries(c.env.DB, tenant.tenantId);
    return c.json({ queries, count: queries.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.post('/queries', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{
      name: string;
      query_type: string;
      parameters_json?: string;
      schedule?: string;
    }>();
    if (!body.name) return c.json({ error: 'name is required' }, 400);
    if (!body.query_type) return c.json({ error: 'query_type is required' }, 400);
    const query = await svc.createQuery(c.env.DB, tenant.tenantId, body);
    return c.json(query, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.post('/queries/:id/run', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const id = c.req.param('id');
    const result = await svc.runQuery(c.env.DB, tenant.tenantId, id);
    if (!result) return c.json({ error: 'Query not found' }, 404);
    return c.json(result);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.delete('/queries/:id', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const id = c.req.param('id');
    const deleted = await svc.deleteQuery(c.env.DB, tenant.tenantId, id);
    if (!deleted) return c.json({ error: 'Query not found' }, 404);
    return c.json({ deleted: true });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// ── Snapshot + admin routes (admin key) ───────────────────────────────────────

app.get('/snapshots', async (c) => {
  if (!requireAdmin(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const type = c.req.query('type') ?? '';
    if (!type) return c.json({ error: 'type query param is required' }, 400);
    const period = c.req.query('period');
    const snapshots = await svc.getSnapshots(c.env.DB, type, period);
    return c.json({ snapshots, count: snapshots.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.post('/snapshots', async (c) => {
  if (!requireAdmin(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const body = await c.req.json<{ snapshot_type: string; data_json: string; period: string }>();
    if (!body.snapshot_type) return c.json({ error: 'snapshot_type is required' }, 400);
    if (!body.period) return c.json({ error: 'period is required' }, 400);
    const snapshot = await svc.createSnapshot(c.env.DB, body);
    return c.json(snapshot, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

app.get('/admin/overview', async (c) => {
  if (!requireAdmin(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as platformAnalyticsDashboard };
