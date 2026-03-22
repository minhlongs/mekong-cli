/**
 * Admin Incident Response routes — incidents and updates management
 * All endpoints require X-Admin-Key header. Mount path: /admin/incident-response
 */

import { Hono } from 'hono';
import { adminIncidentResponseService } from '../services/admin-incident-response';

type Env = {
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
};

const app = new Hono<Env>();

// Admin auth guard for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /incidents — list incidents, optional ?status= filter
app.get('/incidents', async (c) => {
  try {
    const status = c.req.query('status');
    const incidents = await adminIncidentResponseService.listIncidents(c.env.DB, status);
    return c.json({ incidents, count: incidents.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /incidents — create a new incident
app.post('/incidents', async (c) => {
  try {
    const body = await c.req.json() as {
      title: string;
      severity?: string;
      description?: string;
      assigned_to?: string;
    };
    if (!body.title) return c.json({ error: 'title is required' }, 400);
    const incident = await adminIncidentResponseService.createIncident(c.env.DB, body);
    return c.json(incident, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /updates — get updates for an incident (?incident_id= required)
app.get('/updates', async (c) => {
  try {
    const incidentId = c.req.query('incident_id');
    if (!incidentId) return c.json({ error: 'incident_id is required' }, 400);
    const updates = await adminIncidentResponseService.getUpdates(c.env.DB, incidentId);
    return c.json({ updates, count: updates.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — summary counts by status and severity
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await adminIncidentResponseService.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminIncidentResponse };
