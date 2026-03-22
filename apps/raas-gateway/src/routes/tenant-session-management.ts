/**
 * Tenant Session Management routes — session lifecycle and event history
 *
 * Tenant (auth):
 *   GET  /sessions  — list tenant sessions
 *   POST /sessions  — create session
 *   GET  /events    — list session events
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview — platform-wide session stats
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantSessionManagementService as svc } from '../services/tenant-session-management';

const app = new Hono<{ Bindings: Env }>();

// GET /sessions — list all sessions for authenticated tenant
app.get('/sessions', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const sessions = await svc.listSessions(c.env.DB, tenant.tenantId);
    return c.json({ sessions, count: sessions.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /sessions — create a new session for authenticated tenant
app.post('/sessions', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const body = await c.req.json<{
      user_id: string;
      device_info?: string;
      ip_address?: string;
      expires_at?: string;
    }>();
    if (!body.user_id) return c.json({ error: 'user_id is required' }, 400);

    const session = await svc.createSession(c.env.DB, tenant.tenantId, body);
    return c.json(session, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /events — list session events for authenticated tenant
app.get('/events', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const events = await svc.getEvents(c.env.DB, tenant.tenantId);
    return c.json({ events, count: events.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — platform-wide session stats (admin only)
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as tenantSessionManagement };
