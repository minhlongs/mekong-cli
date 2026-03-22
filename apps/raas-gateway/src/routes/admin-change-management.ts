/**
 * Admin Change Management routes — change requests and logs management
 * All endpoints require X-Admin-Key header. Mount path: /admin/change-management
 */

import { Hono } from 'hono';
import { adminChangeManagementService } from '../services/admin-change-management';

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

// GET /changes — list change requests, optional ?status= filter
app.get('/changes', async (c) => {
  try {
    const status = c.req.query('status');
    const changes = await adminChangeManagementService.listChanges(c.env.DB, status);
    return c.json({ changes, count: changes.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /changes — create a new change request
app.post('/changes', async (c) => {
  try {
    const body = await c.req.json() as {
      title: string;
      change_type: string;
      description?: string;
      priority?: string;
      requested_by?: string;
      scheduled_at?: string;
    };
    if (!body.title) return c.json({ error: 'title is required' }, 400);
    if (!body.change_type) return c.json({ error: 'change_type is required' }, 400);
    const change = await adminChangeManagementService.createChange(c.env.DB, body);
    return c.json(change, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /logs — get logs for a change request (?change_id= required)
app.get('/logs', async (c) => {
  try {
    const changeId = c.req.query('change_id');
    if (!changeId) return c.json({ error: 'change_id is required' }, 400);
    const logs = await adminChangeManagementService.getLogs(c.env.DB, changeId);
    return c.json({ logs, count: logs.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — summary counts by status, priority, recent logs
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await adminChangeManagementService.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminChangeManagement };
