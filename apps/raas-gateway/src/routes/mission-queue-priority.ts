/**
 * Mission Queue Priority routes — queue configs + items management
 * Auth: JWT/API key (auth middleware) for tenant routes; X-Admin-Key for admin routes.
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionQueuePriorityService as svc } from '../services/mission-queue-priority-service';
import type { Env } from '../index';

const app = new Hono<{ Bindings: Env }>();

function adminOnly(c: any): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// ── Tenant routes (JWT / API key auth) ───────────────────────────────────────

app.use('/queues', auth());
app.use('/queues/*', auth());
app.use('/items', auth());
app.use('/items/*', auth());

app.get('/queues', async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await svc.listQueues(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'List queues failed' }, 500);
  }
});

app.post('/queues', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  if (!body.queue_name) return c.json({ error: 'queue_name is required' }, 400);
  try {
    const data = await svc.createQueue(c.env.DB, tenant.tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Create queue failed' }, 500);
  }
});

app.get('/items', async (c) => {
  const tenant = getTenant(c);
  const queueId = c.req.query('queue_id');
  if (!queueId) return c.json({ error: 'queue_id is required' }, 400);
  try {
    const data = await svc.getItems(c.env.DB, tenant.tenantId, queueId);
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Get items failed' }, 500);
  }
});

// ── Admin route (X-Admin-Key) ─────────────────────────────────────────────────

app.get('/admin/overview', async (c) => {
  if (!adminOnly(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Overview failed' }, 500);
  }
});

export { app as missionQueuePriority };
