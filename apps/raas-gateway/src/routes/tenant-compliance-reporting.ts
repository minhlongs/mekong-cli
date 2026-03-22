/**
 * Tenant Compliance Reporting routes
 * Mount at: /v1/compliance
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantComplianceReportingService as svc } from '../services/tenant-compliance-reporting';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// ── Reports (tenant-scoped, auth required) ────────────────────────────────────

app.use('/reports', auth());

app.get('/reports', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listReports(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[compliance GET /reports]', err);
    return c.json({ success: false, error: 'Failed to list reports' }, 500);
  }
});

app.post('/reports', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.report_type || !body.period_start || !body.period_end) {
      return c.json({ success: false, error: 'report_type, period_start, and period_end are required' }, 400);
    }
    const data = await svc.createReport(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    console.error('[compliance POST /reports]', err);
    return c.json({ success: false, error: 'Failed to create report' }, 500);
  }
});

// ── Rules (tenant-scoped, auth required) ─────────────────────────────────────

app.use('/rules', auth());

app.get('/rules', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listRules(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[compliance GET /rules]', err);
    return c.json({ success: false, error: 'Failed to list rules' }, 500);
  }
});

// ── Admin overview (admin key required) ──────────────────────────────────────

app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[compliance GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantComplianceReporting };
