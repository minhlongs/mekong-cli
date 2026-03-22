/**
 * Tenant Notification Preferences routes
 * Mount at: /v1/notifications
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantNotificationPreferencesService as svc } from '../services/tenant-notification-preferences';

type Bindings = {
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

const app = new Hono<{ Bindings: Bindings }>();

// ── Preferences (tenant-scoped, auth required) ────────────────────────────────

app.use('/preferences', auth());

app.get('/preferences', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.listPreferences(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    console.error('[notifications GET /preferences]', err);
    return c.json({ error: 'Failed to list preferences' }, 500);
  }
});

app.post('/preferences', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.event_type) {
      return c.json({ error: 'event_type is required' }, 400);
    }
    const result = await svc.createPreference(c.env.DB, tenantId, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result, 201);
  } catch (err) {
    console.error('[notifications POST /preferences]', err);
    return c.json({ error: 'Failed to create preference' }, 500);
  }
});

// ── Channels (tenant-scoped, auth required) ───────────────────────────────────

app.use('/channels', auth());

app.get('/channels', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.getChannels(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    console.error('[notifications GET /channels]', err);
    return c.json({ error: 'Failed to get channels' }, 500);
  }
});

// ── Admin overview (admin key required) ──────────────────────────────────────

app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    console.error('[notifications GET /admin/overview]', err);
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantNotificationPreferences };
