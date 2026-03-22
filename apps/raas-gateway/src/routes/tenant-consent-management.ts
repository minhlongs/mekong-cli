/**
 * Tenant Consent Management routes — consent records and policy management
 *
 * Tenant (auth):
 *   GET  /records  — list consent records for tenant
 *   POST /records  — create a consent record
 *   GET  /policies — list active consent policies for tenant
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview — platform-wide consent stats
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantConsentManagementService as svc } from '../services/tenant-consent-management-service';

const app = new Hono<{ Bindings: Env }>();

// GET /records — list consent records for authenticated tenant
app.get('/records', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const records = await svc.listRecords(c.env.DB, tenant.tenantId);
    return c.json({ records, count: records.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /records — create a consent record for authenticated tenant
app.post('/records', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const body = await c.req.json<{
      user_id: string;
      consent_type: string;
      purpose?: string;
      granted?: number;
      ip_address?: string;
    }>();
    if (!body.user_id) return c.json({ error: 'user_id is required' }, 400);
    if (!body.consent_type) return c.json({ error: 'consent_type is required' }, 400);

    const record = await svc.createRecord(c.env.DB, tenant.tenantId, body);
    return c.json(record, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /policies — list active consent policies for authenticated tenant
app.get('/policies', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const policies = await svc.getPolicies(c.env.DB, tenant.tenantId);
    return c.json({ policies, count: policies.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — platform-wide consent stats (admin only)
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as tenantConsentManagement };
