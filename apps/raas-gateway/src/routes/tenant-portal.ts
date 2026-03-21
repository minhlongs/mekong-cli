/**
 * Tenant Portal routes — self-service account, usage, billing, plan management
 * All routes require JWT or API key auth. Tenant ID sourced from JWT sub.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getAccountOverview,
  getUsageSummary,
  getBillingHistory,
  getCurrentPlan,
  requestPlanChange,
  getApiKeysSummary,
  getNotificationSettings,
  updateNotificationSettings,
} from '../services/tenant-portal-service';

export const tenantPortal = new Hono<{ Bindings: Env }>();

const VALID_TIERS = ['starter', 'pro', 'agency', 'master', 'enterprise'];

/** GET /portal/overview — account overview */
tenantPortal.get('/overview', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await getAccountOverview(c.env.DB, tenant.tenantId);
    return json(data);
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to fetch overview', code: 'OVERVIEW_ERROR' }, { status: 500 });
  }
});

/** GET /portal/usage?period=day|week|month — usage summary */
tenantPortal.get('/usage', auth(), async (c) => {
  const tenant = getTenant(c);
  const rawPeriod = c.req.query('period') ?? 'month';
  const period = (['day', 'week', 'month'].includes(rawPeriod) ? rawPeriod : 'month') as 'day' | 'week' | 'month';

  try {
    const data = await getUsageSummary(c.env.DB, tenant.tenantId, period);
    return json(data);
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to fetch usage', code: 'USAGE_ERROR' }, { status: 500 });
  }
});

/** GET /portal/billing?limit=20 — billing history */
tenantPortal.get('/billing', auth(), async (c) => {
  const tenant = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') ?? '20', 10) || 20, 100);

  try {
    const data = await getBillingHistory(c.env.DB, tenant.tenantId, limit);
    return json({ invoices: data, total: data.length });
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to fetch billing', code: 'BILLING_ERROR' }, { status: 500 });
  }
});

/** GET /portal/plan — current plan + available upgrades */
tenantPortal.get('/plan', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await getCurrentPlan(c.env.DB, tenant.tenantId);
    return json(data);
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to fetch plan', code: 'PLAN_ERROR' }, { status: 500 });
  }
});

/** POST /portal/plan/change — request plan change */
tenantPortal.post('/plan/change', auth(), async (c) => {
  const tenant = getTenant(c);

  let body: { new_tier?: string; reason?: string };
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body', code: 'INVALID_BODY' }, { status: 400 });
  }

  const { new_tier, reason } = body;

  if (!new_tier || !VALID_TIERS.includes(new_tier)) {
    return json(
      { error: `Invalid tier. Must be one of: ${VALID_TIERS.join(', ')}`, code: 'INVALID_TIER' },
      { status: 400 }
    );
  }

  try {
    const result = await requestPlanChange(c.env.DB, tenant.tenantId, new_tier, reason);
    const status = result.auto_approved ? 200 : 202;
    return json(result, { status });
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to request plan change', code: 'PLAN_CHANGE_ERROR' }, { status: 500 });
  }
});

/** GET /portal/api-keys — API keys summary */
tenantPortal.get('/api-keys', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await getApiKeysSummary(c.env.DB, tenant.tenantId);
    return json(data);
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to fetch API keys', code: 'API_KEYS_ERROR' }, { status: 500 });
  }
});

/** GET /portal/notifications — notification settings */
tenantPortal.get('/notifications', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const data = await getNotificationSettings(c.env.DB, tenant.tenantId);
    return json(data);
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to fetch notifications', code: 'NOTIFICATIONS_ERROR' }, { status: 500 });
  }
});

/** PUT /portal/notifications — update notification settings */
tenantPortal.put('/notifications', auth(), async (c) => {
  const tenant = getTenant(c);

  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body', code: 'INVALID_BODY' }, { status: 400 });
  }

  const fields = ['billing_alerts', 'usage_warnings', 'product_updates', 'weekly_digest'];
  const settings: Record<string, boolean> = {};
  for (const field of fields) {
    if (field in body) {
      settings[field] = Boolean(body[field]);
    }
  }

  if (Object.keys(settings).length === 0) {
    return json(
      { error: `At least one setting required: ${fields.join(', ')}`, code: 'MISSING_FIELDS' },
      { status: 400 }
    );
  }

  // Merge with existing settings
  const existing = await getNotificationSettings(c.env.DB, tenant.tenantId);
  const merged = { ...existing, ...settings };

  try {
    const result = await updateNotificationSettings(c.env.DB, tenant.tenantId, merged);
    return json({ ...merged, ...result });
  } catch (err: any) {
    return json({ error: err.message ?? 'Failed to update notifications', code: 'UPDATE_ERROR' }, { status: 500 });
  }
});
