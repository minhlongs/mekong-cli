/**
 * Admin Incident Management routes — incident tracking, updates, postmortems
 * All endpoints require X-Admin-Key header. Mount path: /admin/incidents
 */

import { Hono } from 'hono';
import {
  listIncidents,
  createIncident,
  getIncident,
  updateIncident,
  addUpdate,
  getUpdates,
  createPostmortem,
  getPostmortem,
  getActiveIncidents,
  getDashboard,
} from '../services/admin-incident-management-service';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET / — list incidents (optional ?status= &severity= &limit=)
app.get('/', async (c) => {
  try {
    const status = c.req.query('status');
    const severity = c.req.query('severity');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const incidents = await listIncidents(c.env.DB, status, severity, limit);
    return c.json({ incidents, count: incidents.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});
// POST / — create incident
app.post('/', async (c) => {
  try {
    const body = await c.req.json<{
      title: string;
      description?: string;
      severity?: string;
      impact?: string;
      affected_services?: string[];
      started_at?: string;
      created_by?: string;
    }>();
    if (!body.title) return c.json({ error: 'title is required' }, 400);
    const incident = await createIncident(c.env.DB, body.title, body.created_by ?? 'admin', {
      description: body.description,
      severity: body.severity,
      impact: body.impact,
      affectedServices: body.affected_services,
      startedAt: body.started_at,
    });
    return c.json(incident, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});
// GET /active — active incidents only
app.get('/active', async (c) => {
  try {
    const incidents = await getActiveIncidents(c.env.DB);
    return c.json({ incidents, count: incidents.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — incident dashboard summary
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /:id — get incident detail
app.get('/:id', async (c) => {
  try {
    const incident = await getIncident(c.env.DB, c.req.param('id'));
    if (!incident) return c.json({ error: 'Incident not found' }, 404);
    return c.json(incident);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /:id — update incident
app.put('/:id', async (c) => {
  try {
    const body = await c.req.json<{
      title?: string;
      description?: string;
      severity?: string;
      status?: string;
      impact?: string;
      affected_services?: string[];
      identified_at?: string;
      resolved_at?: string;
    }>();
    const incident = await updateIncident(c.env.DB, c.req.param('id'), {
      title: body.title,
      description: body.description,
      severity: body.severity,
      status: body.status,
      impact: body.impact,
      affectedServices: body.affected_services,
      identifiedAt: body.identified_at,
      resolvedAt: body.resolved_at,
    });
    if (!incident) return c.json({ error: 'Incident not found' }, 404);
    return c.json(incident);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /:id/updates — add update to incident
app.post('/:id/updates', async (c) => {
  try {
    const body = await c.req.json<{
      message: string;
      update_type?: string;
      new_status?: string;
      created_by?: string;
    }>();
    if (!body.message) return c.json({ error: 'message is required' }, 400);
    const update = await addUpdate(
      c.env.DB,
      c.req.param('id'),
      body.message,
      body.created_by ?? 'admin',
      body.update_type ?? 'note',
      body.new_status
    );
    return c.json(update, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /:id/updates — get updates for incident
app.get('/:id/updates', async (c) => {
  try {
    const updates = await getUpdates(c.env.DB, c.req.param('id'));
    return c.json({ updates, count: updates.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /:id/postmortem — create/update postmortem
app.post('/:id/postmortem', async (c) => {
  try {
    const body = await c.req.json<{
      summary: string;
      root_cause?: string;
      timeline?: unknown[];
      action_items?: string[];
      lessons_learned?: string;
      created_by?: string;
    }>();
    if (!body.summary) return c.json({ error: 'summary is required' }, 400);
    const pm = await createPostmortem(c.env.DB, c.req.param('id'), body.summary, body.created_by ?? 'admin', {
      rootCause: body.root_cause,
      timeline: body.timeline,
      actionItems: body.action_items,
      lessonsLearned: body.lessons_learned,
    });
    return c.json(pm, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /:id/postmortem — get postmortem for incident
app.get('/:id/postmortem', async (c) => {
  try {
    const pm = await getPostmortem(c.env.DB, c.req.param('id'));
    if (!pm) return c.json({ error: 'Postmortem not found' }, 404);
    return c.json(pm);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminIncidentManagement };
