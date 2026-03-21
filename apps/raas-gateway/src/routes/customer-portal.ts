/**
 * Customer Portal routes — mounted at /v1/portal
 * All routes require JWT or API key auth.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { getPortalOverview, getUsageSummary, getAccountSettings } from '../services/customer-portal-service';
import { getActivityLog, logActivity } from '../services/customer-portal-ticket-service';
import { getBillingHistory } from '../services/tenant-portal-service';
import { ticketRoutes } from './customer-portal-ticket-routes';

const app = new Hono<{ Bindings: Env }>();

/** GET /overview — dashboard aggregate */
app.get('/overview', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const data = await getPortalOverview(c.env.DB, tenantId);
    await logActivity(c.env.DB, tenantId, 'portal.overview.viewed', {}, c.req.header('CF-Connecting-IP'));
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Failed to fetch overview', code: 'OVERVIEW_ERROR' }, 500);
  }
});

/** GET /usage?period=day|week|month */
app.get('/usage', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const data = await getUsageSummary(c.env.DB, tenantId, { period: c.req.query('period') });
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Failed to fetch usage', code: 'USAGE_ERROR' }, 500);
  }
});

/** GET /account — account settings */
app.get('/account', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const data = await getAccountSettings(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Failed to fetch account', code: 'ACCOUNT_ERROR' }, 500);
  }
});

/** GET /activity?limit= — portal activity log */
app.get('/activity', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const limit = parseInt(c.req.query('limit') ?? '20', 10) || 20;
  try {
    const data = await getActivityLog(c.env.DB, tenantId, { limit });
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Failed to fetch activity', code: 'ACTIVITY_ERROR' }, 500);
  }
});

/** GET /invoices?limit= — billing/invoice history */
app.get('/invoices', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const limit = parseInt(c.req.query('limit') ?? '20', 10) || 20;
  try {
    const data = await getBillingHistory(c.env.DB, tenantId, limit);
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Failed to fetch invoices', code: 'INVOICES_ERROR' }, 500);
  }
});

// Mount ticket sub-routes at /tickets
app.route('/tickets', ticketRoutes);

export const customerPortal = app;
