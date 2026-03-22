// Admin Incident Management routes — platform incidents, outages, resolution tracking
// All endpoints require X-Admin-Key header. Mount path: /admin/incidents

import { Hono } from 'hono';
import { adminIncidentManagementService } from '../services/admin-incident-management';

const app = new Hono<{
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
}>();

// Admin auth check on every request
app.use('*', async (c, next) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /incidents — list all platform incidents
app.get('/incidents', async (c) => {
  try {
    const result = await adminIncidentManagementService.listIncidents(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ incidents: result.data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /incidents — create a new platform incident
app.post('/incidents', async (c) => {
  try {
    const body = await c.req.json<{
      title: string;
      description?: string;
      severity?: string;
      status?: string;
      affected_services?: string;
      started_at?: string;
    }>();
    if (!body.title) return c.json({ error: 'title is required' }, 400);
    const id = crypto.randomUUID();
    const result = await adminIncidentManagementService.createIncident(c.env.DB, { id, ...body });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /updates — list all platform incident updates
app.get('/updates', async (c) => {
  try {
    const result = await adminIncidentManagementService.getUpdates(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ updates: result.data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — incident counts by status + recent incidents
app.get('/dashboard', async (c) => {
  try {
    const result = await adminIncidentManagementService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminIncidentManagement };
