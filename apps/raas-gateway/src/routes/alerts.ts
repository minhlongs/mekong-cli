/**
 * Alerts routes — credit usage warnings and upgrade nudges
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const alerts = new Hono<{ Bindings: Env }>();

// All alert routes require auth
alerts.use('/*', auth());

/**
 * GET /v1/alerts — list unread alerts for tenant
 */
alerts.get('/', async (c) => {
  const tenant = getTenant(c);

  const results = await c.env.DB.prepare(
    `SELECT id, tenant_id as tenantId, type, message, read, created_at as createdAt
     FROM alerts
     WHERE tenant_id = ? AND read = 0
     ORDER BY created_at DESC
     LIMIT 50`
  )
    .bind(tenant.tenantId)
    .all<{ id: string; tenantId: string; type: string; message: string; read: number; createdAt: string }>();

  return json({ alerts: results.results });
});

/**
 * GET /v1/alerts/count — unread alert count only
 */
alerts.get('/count', async (c) => {
  const tenant = getTenant(c);

  const result = await c.env.DB.prepare(
    'SELECT COUNT(*) as count FROM alerts WHERE tenant_id = ? AND read = 0'
  )
    .bind(tenant.tenantId)
    .first<{ count: number }>();

  return json({ count: result?.count ?? 0 });
});

/**
 * POST /v1/alerts/:id/read — mark alert as read
 */
alerts.post('/:id/read', async (c) => {
  const tenant = getTenant(c);
  const alertId = c.req.param('id');

  const updateResult = await c.env.DB.prepare(
    'UPDATE alerts SET read = 1 WHERE id = ? AND tenant_id = ?'
  )
    .bind(alertId, tenant.tenantId)
    .run();

  if (!updateResult.success || updateResult.meta.changes === 0) {
    return json({ error: 'Alert not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  return json({ success: true, id: alertId });
});
