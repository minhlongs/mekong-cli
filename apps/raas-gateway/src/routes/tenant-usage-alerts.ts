/**
 * Tenant Usage Alerts routes — manage alert rules and trigger history
 * Auth: GET /rules, POST /rules, GET /triggers
 * Admin: GET /admin/overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantUsageAlertsService } from '../services/tenant-usage-alerts';

const app = new Hono<{ Bindings: Env }>();

// ── Admin helper ───────────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Auth routes ────────────────────────────────────────────────────────────────

/**
 * GET /rules — list all alert rules for authenticated tenant
 */
app.get('/rules', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const rules = await tenantUsageAlertsService.listRules(c.env.DB, tenantId);
    return json({ rules, total: rules.length });
  } catch (err) {
    return json({ error: 'Failed to list alert rules', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /rules — create a new alert rule for authenticated tenant
 * Body: { metric_name, threshold, comparison?, notification_channel }
 */
app.post('/rules', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  const metricName = String(body.metric_name ?? '').trim();
  const notificationChannel = String(body.notification_channel ?? '').trim();
  const threshold = Number(body.threshold);
  const comparison = String(body.comparison ?? 'gt').trim();

  if (!metricName) {
    return json({ error: 'metric_name is required', code: 'INVALID_INPUT' }, { status: 400 });
  }
  if (!notificationChannel) {
    return json({ error: 'notification_channel is required', code: 'INVALID_INPUT' }, { status: 400 });
  }
  if (!Number.isFinite(threshold)) {
    return json({ error: 'threshold must be a number', code: 'INVALID_INPUT' }, { status: 400 });
  }
  if (!['gt', 'lt', 'gte', 'lte', 'eq'].includes(comparison)) {
    return json({ error: 'comparison must be one of: gt, lt, gte, lte, eq', code: 'INVALID_INPUT' }, { status: 400 });
  }

  try {
    const rule = await tenantUsageAlertsService.createRule(
      c.env.DB, tenantId, metricName, threshold, comparison, notificationChannel
    );
    return json({ rule }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to create alert rule', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /triggers — list recent alert triggers for authenticated tenant
 * Query: limit (default 50, max 200)
 */
app.get('/triggers', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200);

  try {
    const triggers = await tenantUsageAlertsService.getTriggers(c.env.DB, tenantId, limit);
    return json({ triggers, total: triggers.length });
  } catch (err) {
    return json({ error: 'Failed to fetch triggers', details: String(err) }, { status: 500 });
  }
});

// ── Admin route ────────────────────────────────────────────────────────────────

/**
 * GET /admin/overview — platform-wide alert stats (X-Admin-Key required)
 */
app.get('/admin/overview', async (c) => {
  if (!requireAdminKey(c)) {
    return json({ error: 'Forbidden' }, { status: 403 });
  }
  try {
    const overview = await tenantUsageAlertsService.getAdminOverview(c.env.DB);
    return json(overview);
  } catch (err) {
    return json({ error: 'Failed to fetch admin overview', details: String(err) }, { status: 500 });
  }
});

export { app as tenantUsageAlerts };
