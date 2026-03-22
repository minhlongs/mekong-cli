/**
 * Tenant API Access Control routes
 * Mount at: /v1/access-control
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiAccessControlService as svc } from '../services/tenant-api-access-control-service';

export const tenantApiAccessControl = new Hono<{ Bindings: Env }>();

// ── Rules (tenant-scoped, auth required) ─────────────────────────────────────

tenantApiAccessControl.use('/rules', auth());
tenantApiAccessControl.use('/rules/*', auth());

tenantApiAccessControl.get('/rules', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listRules(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[access-control GET /rules]', err);
    return c.json({ success: false, error: 'Failed to list access rules' }, 500);
  }
});

tenantApiAccessControl.post('/rules', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.resource_pattern) {
      return c.json({ success: false, error: 'resource_pattern is required' }, 400);
    }
    const data = await svc.createRule(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    console.error('[access-control POST /rules]', err);
    return c.json({ success: false, error: 'Failed to create access rule' }, 500);
  }
});

// ── Audit log (tenant-scoped, auth required) ─────────────────────────────────

tenantApiAccessControl.use('/audit', auth());

tenantApiAccessControl.get('/audit', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const data = await svc.getAudit(c.env.DB, tenantId, limit);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[access-control GET /audit]', err);
    return c.json({ success: false, error: 'Failed to get audit log' }, 500);
  }
});

// ── Admin overview (admin key required) ──────────────────────────────────────

tenantApiAccessControl.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[access-control GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to get admin overview' }, 500);
  }
});
