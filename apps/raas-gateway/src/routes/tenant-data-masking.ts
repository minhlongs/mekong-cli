/**
 * Tenant Data Masking routes
 * Mount at: /v1/data-masking
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantDataMaskingService as svc } from '../services/tenant-data-masking-service';

const app = new Hono<{ Bindings: Env }>();

// ── Policies (tenant-scoped, auth required) ────────────────────────────────

app.use('/policies', auth());
app.use('/policies/*', auth());

/** GET /policies — list masking policies for tenant */
app.get('/policies', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listPolicies(c.env.DB, tenantId);
    return c.json({ success: true, ...data });
  } catch (err) {
    console.error('[data-masking GET /policies]', err);
    return c.json({ error: 'Failed to list policies' }, 500);
  }
});

/** POST /policies — create a masking policy */
app.post('/policies', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.field_pattern) {
      return c.json({ error: 'field_pattern is required' }, 400);
    }
    const data = await svc.createPolicy(c.env.DB, tenantId, body);
    return c.json({ success: true, ...data }, 201);
  } catch (err) {
    console.error('[data-masking POST /policies]', err);
    return c.json({ error: 'Failed to create policy' }, 500);
  }
});

// ── Events (tenant-scoped, auth required) ──────────────────────────────────

app.use('/events', auth());

/** GET /events — list masking events for tenant */
app.get('/events', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const policyId = c.req.query('policy_id');
    const data = await svc.getEvents(c.env.DB, tenantId, policyId);
    return c.json({ success: true, ...data });
  } catch (err) {
    console.error('[data-masking GET /events]', err);
    return c.json({ error: 'Failed to get events' }, 500);
  }
});

// ── Admin (admin key required) ─────────────────────────────────────────────

/** GET /admin/overview — platform-wide masking stats */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, ...data });
  } catch (err) {
    console.error('[data-masking GET /admin/overview]', err);
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantDataMasking };
