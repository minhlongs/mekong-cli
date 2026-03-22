/**
 * Admin Platform Audit Trail routes — entries, policies, dashboard
 * All endpoints require X-Admin-Key header. Mount path: /admin/platform-audit
 */

import { Hono } from 'hono';
import { adminPlatformAuditTrailService as svc } from '../services/admin-platform-audit-trail';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard: all routes require valid X-Admin-Key
app.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /entries — list audit entries; optional ?actor= &action= &resource_type= &limit=
app.get('/entries', async (c) => {
  try {
    const actor = c.req.query('actor');
    const action = c.req.query('action');
    const resource_type = c.req.query('resource_type');
    const limitRaw = c.req.query('limit');
    const limit = limitRaw ? parseInt(limitRaw, 10) : undefined;

    const result = await svc.listEntries(c.env.DB, { actor, action, resource_type, limit });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// POST /entries — create a new audit entry
app.post('/entries', async (c) => {
  try {
    const body = await c.req.json();

    if (!body.actor?.trim()) return c.json({ error: 'actor is required' }, 400);
    if (!body.action?.trim()) return c.json({ error: 'action is required' }, 400);
    if (!body.resource_type?.trim()) return c.json({ error: 'resource_type is required' }, 400);

    const result = await svc.createEntry(c.env.DB, {
      actor: body.actor.trim(),
      action: body.action.trim(),
      resource_type: body.resource_type.trim(),
      resource_id: body.resource_id,
      details: body.details,
      ip_address: body.ip_address,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /policies — list all audit policies
app.get('/policies', async (c) => {
  try {
    const result = await svc.getPolicies(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /dashboard — aggregated counts by action, resource_type, 7-day activity, policy summary
app.get('/dashboard', async (c) => {
  try {
    const result = await svc.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminPlatformAuditTrail };
