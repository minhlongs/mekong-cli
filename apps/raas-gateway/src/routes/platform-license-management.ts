/**
 * Platform License Management routes — admin-only CRUD at /admin/platform-licenses
 * All routes require X-Admin-Key header authentication
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { platformLicenseManagementService as svc } from '../services/platform-license-management-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth guard — 403 on missing/invalid key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /admin/platform-licenses/licenses?tenant_id=&status=
app.get('/licenses', async (c) => {
  try {
    const tenantId = c.req.query('tenant_id');
    const status = c.req.query('status');
    const licenses = await svc.listLicenses(c.env.DB, tenantId, status);
    return c.json({ licenses });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// POST /admin/platform-licenses/licenses
app.post('/licenses', async (c) => {
  try {
    const body = await c.req.json() as any;
    if (!body.license_key) return c.json({ error: 'license_key required' }, 400);
    const id = crypto.randomUUID();
    const license = await svc.createLicense(c.env.DB, { id, ...body });
    return c.json({ license }, 201);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// GET /admin/platform-licenses/activations?license_id=
app.get('/activations', async (c) => {
  try {
    const licenseId = c.req.query('license_id');
    if (!licenseId) return c.json({ error: 'license_id required' }, 400);
    const activations = await svc.getActivations(c.env.DB, licenseId);
    return c.json({ activations });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// GET /admin/platform-licenses/dashboard
app.get('/dashboard', async (c) => {
  try {
    const data = await svc.getDashboard(c.env.DB);
    return c.json(data);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

export { app as platformLicenseManagement };
