/**
 * Dunning management routes — admin-only endpoints for failed payment recovery
 * Handles active dunning cases, win-back email campaigns, and manual resolution
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

export const dunning = new Hono<{ Bindings: Env }>();

// Admin auth middleware
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
};

dunning.use('/*', adminAuth());

/**
 * GET /admin/dunning/active — List active dunning cases (status != 'resolved')
 */
dunning.get('/active', async (c) => {
  const { results } = await c.env.DB.prepare(
    `SELECT d.*, t.name as tenant_name, t.email as tenant_email
     FROM dunning_events d
     LEFT JOIN tenants t ON t.id = d.tenant_id
     WHERE d.status != 'resolved'
     ORDER BY d.created_at DESC
     LIMIT 100`
  ).all();
  return json({ cases: results, count: results.length });
});

/**
 * GET /admin/dunning/stats — Summary: active cases, at-risk revenue, avg resolution time
 */
dunning.get('/stats', async (c) => {
  const [active, resolved] = await Promise.all([
    c.env.DB.prepare(
      `SELECT COUNT(*) as count, COALESCE(SUM(amount_cents), 0) as at_risk_cents
       FROM dunning_events WHERE status != 'resolved'`
    ).first<{ count: number; at_risk_cents: number }>(),
    c.env.DB.prepare(
      `SELECT AVG(
         (julianday(resolved_at) - julianday(created_at)) * 24
       ) as avg_resolution_hours
       FROM dunning_events WHERE status = 'resolved' AND resolved_at IS NOT NULL`
    ).first<{ avg_resolution_hours: number | null }>(),
  ]);

  return json({
    active_cases: active?.count ?? 0,
    at_risk_revenue_cents: active?.at_risk_cents ?? 0,
    at_risk_revenue_usd: ((active?.at_risk_cents ?? 0) / 100).toFixed(2),
    avg_resolution_hours: resolved?.avg_resolution_hours
      ? Math.round(resolved.avg_resolution_hours * 10) / 10
      : null,
  });
});

/**
 * POST /admin/dunning/resolve/:id — Manually resolve a dunning case
 */
dunning.post('/resolve/:id', async (c) => {
  const id = c.req.param('id');
  const now = new Date().toISOString();

  const result = await c.env.DB.prepare(
    `UPDATE dunning_events
     SET status = 'resolved', resolved_at = ?, updated_at = ?
     WHERE id = ? AND status != 'resolved'`
  ).bind(now, now, id).run();

  if (!result.meta.changes) {
    return json({ error: 'Dunning case not found or already resolved' }, { status: 404 });
  }
  return json({ resolved: true, id, resolved_at: now });
});

/**
 * GET /admin/dunning/win-back — List win-back email campaign stats
 */
dunning.get('/win-back', async (c) => {
  const { results } = await c.env.DB.prepare(
    `SELECT w.*, t.name as tenant_name, t.email as tenant_email
     FROM win_back_emails w
     LEFT JOIN tenants t ON t.id = w.tenant_id
     ORDER BY w.sent_at DESC
     LIMIT 100`
  ).all();

  const stats = await c.env.DB.prepare(
    `SELECT
       COUNT(*) as total_sent,
       COUNT(opened_at) as total_opened,
       COUNT(clicked_at) as total_clicked,
       COUNT(converted_at) as total_converted
     FROM win_back_emails`
  ).first<{ total_sent: number; total_opened: number; total_clicked: number; total_converted: number }>();

  return json({ emails: results, stats });
});

/**
 * POST /admin/dunning/win-back/:tenantId — Trigger win-back email for churned tenant
 */
dunning.post('/win-back/:tenantId', async (c) => {
  const tenantId = c.req.param('tenantId');
  const body = await c.req.json().catch(() => ({}));
  const emailType = body.email_type || 'win_back_30d';

  const tenant = await c.env.DB.prepare(
    'SELECT id FROM tenants WHERE id = ?'
  ).bind(tenantId).first();

  if (!tenant) {
    return json({ error: 'Tenant not found' }, { status: 404 });
  }

  await c.env.DB.prepare(
    `INSERT INTO win_back_emails (id, tenant_id, email_type, sent_at)
     VALUES (?, ?, ?, datetime('now'))`
  ).bind(crypto.randomUUID(), tenantId, emailType).run();

  return json({ queued: true, tenantId, emailType });
});
