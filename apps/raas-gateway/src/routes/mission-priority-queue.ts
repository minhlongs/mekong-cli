/**
 * Mission Priority Queue routes — enqueue, dequeue, peek, rules, stats, admin
 * Auth: JWT/API key (auth middleware) for tenant routes; X-Admin-Key for admin routes.
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionPriorityQueueService as svc } from '../services/mission-priority-queue-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// ── Admin key guard (inline — used for admin-only endpoints) ──────────────────
function adminOnly(c: any): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// ── Admin endpoints (X-Admin-Key) ────────────────────────────────────────────

app.post('/dequeue', async (c) => {
  if (!adminOnly(c)) return c.json({ error: 'Forbidden' }, 403);
  const body = await c.req.json().catch(() => ({}));
  if (!body.worker_id) return c.json({ error: 'worker_id is required' }, 400);
  try {
    const item = await svc.dequeue(c.env.DB, body.worker_id);
    if (!item) return c.json({ success: true, data: null, message: 'Queue empty' });
    return c.json({ success: true, data: item });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Dequeue failed' }, 500);
  }
});

app.get('/peek', async (c) => {
  if (!adminOnly(c)) return c.json({ error: 'Forbidden' }, 403);
  const limit = Math.min(Number(c.req.query('limit') ?? 10), 100);
  try {
    const data = await svc.peek(c.env.DB, limit);
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Peek failed' }, 500);
  }
});

app.get('/stats', async (c) => {
  if (!adminOnly(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const data = await svc.getQueueStats(c.env.DB);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Stats failed' }, 500);
  }
});

app.get('/admin/overview', async (c) => {
  if (!adminOnly(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Overview failed' }, 500);
  }
});

// ── Tenant endpoints (JWT / API key auth) ────────────────────────────────────

app.use('/enqueue', auth());
app.use('/items/*', auth());
app.use('/rules', auth());
app.use('/rules/*', auth());

app.post('/enqueue', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  if (!body.mission_id) return c.json({ error: 'mission_id is required' }, 400);
  try {
    const data = await svc.enqueue(c.env.DB, tenant.tenantId, body.mission_id, body.priority, body.sla_deadline);
    return c.json({ success: true, data }, 201);
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Enqueue failed' }, 500);
  }
});

app.get('/items/:id', async (c) => {
  const tenant = getTenant(c);
  const item = await svc.getQueueItem(c.env.DB, c.req.param('id'));
  if (!item || item.tenant_id !== tenant.tenantId) return c.json({ error: 'Not found' }, 404);
  return c.json({ success: true, data: item });
});

app.delete('/items/:id', async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await svc.cancelItem(c.env.DB, tenant.tenantId, c.req.param('id'));
    if (!data) return c.json({ error: 'Not found' }, 404);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Cancel failed' }, 400);
  }
});

app.put('/items/:id/priority', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  if (body.priority === undefined) return c.json({ error: 'priority is required' }, 400);
  try {
    const data = await svc.reprioritize(c.env.DB, tenant.tenantId, c.req.param('id'), Number(body.priority));
    if (!data) return c.json({ error: 'Not found' }, 404);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Reprioritize failed' }, 500);
  }
});

app.get('/rules', async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await svc.listRules(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'List rules failed' }, 500);
  }
});

app.post('/rules', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  if (!body.name) return c.json({ error: 'name is required' }, 400);
  try {
    const data = await svc.createRule(c.env.DB, tenant.tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Create rule failed' }, 500);
  }
});

export { app as missionPriorityQueue };
