/**
 * Tenant Data Classification routes
 * Mount at: /v1/data-classification
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantDataClassificationService as svc } from '../services/tenant-data-classification-service';

const app = new Hono<{ Bindings: Env }>();

// ── Classifications (tenant-scoped, auth required) ─────────────────────────

app.use('/classifications', auth());
app.use('/classifications/*', auth());

/** GET /classifications — list data classifications for tenant */
app.get('/classifications', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listClassifications(c.env.DB, tenantId);
    return c.json({ success: true, ...data });
  } catch (err) {
    console.error('[data-classification GET /classifications]', err);
    return c.json({ error: 'Failed to list classifications' }, 500);
  }
});

/** POST /classifications — create a data classification */
app.post('/classifications', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.field_path) {
      return c.json({ error: 'field_path is required' }, 400);
    }
    const data = await svc.createClassification(c.env.DB, tenantId, body);
    return c.json({ success: true, ...data }, 201);
  } catch (err) {
    console.error('[data-classification POST /classifications]', err);
    return c.json({ error: 'Failed to create classification' }, 500);
  }
});

// ── Scans (tenant-scoped, auth required) ───────────────────────────────────

app.use('/scans', auth());

/** GET /scans — list classification scans for tenant */
app.get('/scans', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const classificationId = c.req.query('classification_id');
    const data = await svc.getScans(c.env.DB, tenantId, classificationId);
    return c.json({ success: true, ...data });
  } catch (err) {
    console.error('[data-classification GET /scans]', err);
    return c.json({ error: 'Failed to get scans' }, 500);
  }
});

// ── Admin (admin key required) ─────────────────────────────────────────────

/** GET /admin/overview — platform-wide classification stats */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, ...data });
  } catch (err) {
    console.error('[data-classification GET /admin/overview]', err);
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantDataClassification };
