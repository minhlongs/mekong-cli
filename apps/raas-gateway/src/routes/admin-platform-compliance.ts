/**
 * Admin platform compliance routes — requirements tracking and audit management
 * All endpoints protected by X-Admin-Key header, returns 403 on invalid key
 */

import { Hono } from 'hono';
import { adminPlatformComplianceService } from '../services/admin-platform-compliance';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin auth guard — X-Admin-Key required on all routes
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /requirements — list all compliance requirements, optional ?status= filter
app.get('/requirements', async (c) => {
  try {
    const status = c.req.query('status');
    const result = await adminPlatformComplianceService.listRequirements(c.env.DB, status);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ data: result.data });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Internal error' }, 500);
  }
});

// POST /requirements — create a new compliance requirement
app.post('/requirements', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.id || !body.requirement_name || !body.regulation) {
      return c.json({ error: 'id, requirement_name, and regulation are required' }, 400);
    }
    const result = await adminPlatformComplianceService.createRequirement(c.env.DB, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ data: result.data }, 201);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Internal error' }, 500);
  }
});

// GET /audits — list audits, optional ?requirement_id= filter
app.get('/audits', async (c) => {
  try {
    const requirement_id = c.req.query('requirement_id');
    const result = await adminPlatformComplianceService.getAudits(c.env.DB, requirement_id);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ data: result.data });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Internal error' }, 500);
  }
});

// GET /dashboard — compliance status summary and overdue count
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformComplianceService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ data: result.data });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Internal error' }, 500);
  }
});

export { app as adminPlatformCompliance };
