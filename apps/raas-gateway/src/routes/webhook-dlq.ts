/**
 * Webhook Dead Letter Queue routes.
 * Admin routes: X-Admin-Key auth, full visibility across tenants.
 * Tenant routes: auth middleware, scoped to own data.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { WebhookRetryService } from '../services/webhook-retry-service';
import { json } from '../utils/response';

export const webhookDLQ = new Hono<{ Bindings: Env }>();

const svc = new WebhookRetryService();

// ---------------------------------------------------------------------------
// Admin helpers
// ---------------------------------------------------------------------------

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

function adminGuard(c: any): Response | null {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'ADMIN_REQUIRED' }, { status: 401 });
  return null;
}

// ---------------------------------------------------------------------------
// Admin routes — /admin/dlq/*
// ---------------------------------------------------------------------------

/** GET /admin/dlq — list DLQ entries with optional filters */
webhookDLQ.get('/admin/dlq', async (c) => {
  const guard = adminGuard(c);
  if (guard) return guard;

  const tenantId = c.req.query('tenant_id');
  const eventType = c.req.query('event_type');
  const unresolvedOnly = c.req.query('unresolved_only') !== 'false';

  let query = 'SELECT * FROM webhook_dead_letters WHERE 1=1';
  const params: (string | number)[] = [];

  if (tenantId) { query += ' AND tenant_id = ?'; params.push(tenantId); }
  if (eventType) { query += ' AND event_type = ?'; params.push(eventType); }
  if (unresolvedOnly) { query += ' AND resolved_at IS NULL'; }

  query += ' ORDER BY moved_at DESC LIMIT 100';

  const { results } = await c.env.DB.prepare(query).bind(...params).all();
  return json({ success: true, data: results });
});

/** POST /admin/dlq/:id/replay — replay a single DLQ entry */
webhookDLQ.post('/admin/dlq/:id/replay', async (c) => {
  const guard = adminGuard(c);
  if (guard) return guard;

  const id = Number(c.req.param('id'));
  if (isNaN(id)) return json({ error: 'Invalid id', code: 'INVALID_PARAM' }, { status: 400 });

  const result = await svc.replayFromDLQ(c.env.DB, id);
  if (!result.success) {
    return json({ error: 'DLQ entry not found or missing original URL', code: 'NOT_FOUND' }, { status: 404 });
  }
  return json({ success: true, data: { replayed: true, dlq_id: id } });
});

/** POST /admin/dlq/replay-all — replay all unresolved entries for a tenant */
webhookDLQ.post('/admin/dlq/replay-all', async (c) => {
  const guard = adminGuard(c);
  if (guard) return guard;

  const tenantId = c.req.query('tenant_id');
  if (!tenantId) {
    return json({ error: 'tenant_id query param required', code: 'MISSING_PARAM' }, { status: 400 });
  }

  const { results } = await c.env.DB
    .prepare(
      `SELECT id FROM webhook_dead_letters
       WHERE tenant_id = ? AND resolved_at IS NULL ORDER BY moved_at ASC`,
    )
    .bind(tenantId)
    .all<{ id: number }>();

  let replayed = 0;
  let failed = 0;
  for (const row of results) {
    const r = await svc.replayFromDLQ(c.env.DB, row.id);
    r.success ? replayed++ : failed++;
  }

  return json({ success: true, data: { replayed, failed, tenant_id: tenantId } });
});

/** GET /admin/dlq/stats — global DLQ statistics */
webhookDLQ.get('/admin/dlq/stats', async (c) => {
  const guard = adminGuard(c);
  if (guard) return guard;

  const tenantId = c.req.query('tenant_id');
  const stats = await svc.getDLQStats(c.env.DB, tenantId);
  return json({ success: true, data: stats });
});

// ---------------------------------------------------------------------------
// Tenant routes — scoped to authenticated tenant
// ---------------------------------------------------------------------------

webhookDLQ.use('/v1/dlq', auth());
webhookDLQ.use('/v1/dlq/stats', auth());

/** GET /v1/dlq — list tenant's own DLQ entries */
webhookDLQ.get('/v1/dlq', async (c) => {
  const tenant = getTenant(c);

  const unresolvedOnly = c.req.query('unresolved_only') !== 'false';
  const eventType = c.req.query('event_type');

  let query = 'SELECT * FROM webhook_dead_letters WHERE tenant_id = ?';
  const params: (string | number)[] = [tenant.tenantId];

  if (eventType) { query += ' AND event_type = ?'; params.push(eventType); }
  if (unresolvedOnly) { query += ' AND resolved_at IS NULL'; }
  query += ' ORDER BY moved_at DESC LIMIT 50';

  const { results } = await c.env.DB.prepare(query).bind(...params).all();
  return json({ success: true, data: results });
});

/** GET /v1/dlq/stats — tenant's DLQ statistics */
webhookDLQ.get('/v1/dlq/stats', async (c) => {
  const tenant = getTenant(c);
  const stats = await svc.getDLQStats(c.env.DB, tenant.tenantId);
  return json({ success: true, data: stats });
});
