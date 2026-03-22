/**
 * Platform Notification Center Routes
 * Tenant: list, create, mark-read notifications + preferences
 * Admin:  overview stats
 * Public: list templates
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { notificationCenterService } from '../services/platform-notification-center-service';

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

// ── Notifications ────────────────────────────────────────────────────────────

/** GET /notifications — paginated list for tenant */
app.get('/notifications', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const { status, channel, limit, offset } = c.req.query();
    const data = await notificationCenterService.listNotifications(c.env.DB, tenantId, {
      status,
      channel,
      limit: limit ? Number(limit) : undefined,
      offset: offset ? Number(offset) : undefined,
    });
    return c.json(data);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to list notifications' }, 500);
  }
});

/** POST /notifications — create notification for tenant */
app.post('/notifications', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      title: string;
      body?: string;
      notification_type?: string;
      channel?: string;
    }>();
    if (!body.title) return c.json({ error: 'title is required' }, 400);
    const notification = await notificationCenterService.createNotification(c.env.DB, tenantId, body);
    return c.json({ notification }, 201);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to create notification' }, 500);
  }
});

/** PUT /notifications/:id/read — mark single notification as read */
app.put('/notifications/:id/read', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const id = c.req.param('id');
    const result = await notificationCenterService.markAsRead(c.env.DB, tenantId, id);
    if (!result.success) return c.json({ error: 'Notification not found' }, 404);
    return c.json(result);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to mark as read' }, 500);
  }
});

/** POST /notifications/read-all — bulk mark all as read */
app.post('/notifications/read-all', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await notificationCenterService.markAllAsRead(c.env.DB, tenantId);
    return c.json(result);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to mark all as read' }, 500);
  }
});

// ── Preferences ──────────────────────────────────────────────────────────────

/** GET /preferences — list notification preferences for tenant */
app.get('/preferences', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const preferences = await notificationCenterService.getPreferences(c.env.DB, tenantId);
    return c.json({ preferences });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to get preferences' }, 500);
  }
});

/** PUT /preferences/:channel — upsert preference for a channel */
app.put('/preferences/:channel', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const channel = c.req.param('channel');
    const body = await c.req.json<{ enabled?: number; config_json?: string }>();
    const result = await notificationCenterService.updatePreferences(c.env.DB, tenantId, channel, body);
    return c.json({ preference: result });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to update preference' }, 500);
  }
});

// ── Templates (public) ───────────────────────────────────────────────────────

/** GET /templates — list all notification templates (no auth) */
app.get('/templates', async (c) => {
  try {
    const templates = await notificationCenterService.listTemplates(c.env.DB);
    return c.json({ templates });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to list templates' }, 500);
  }
});

// ── Admin ────────────────────────────────────────────────────────────────────

/** GET /admin/overview — platform-wide notification stats (admin key required) */
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    if (!key || key !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Unauthorized' }, 401);
    }
    const overview = await notificationCenterService.getAdminOverview(c.env.DB);
    return c.json({ overview });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to get admin overview' }, 500);
  }
});

export { app as platformNotificationCenter };
