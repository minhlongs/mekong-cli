/**
 * Notifications Hub routes — multi-channel notification dispatch API
 * Mount at /v1/notifications-hub in parent router
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  addChannel,
  listChannels,
  updateChannel,
  removeChannel,
  sendNotification,
  getNotificationLog,
  getNotificationStats,
  getAdminNotificationOverview,
} from '../services/notifications-hub-service';
import {
  listTemplates,
  upsertTemplate,
  seedDefaultTemplates,
} from '../services/notifications-hub-templates-service';

const app = new Hono<{ Bindings: Env }>();

// ── Channels ───────────────────────────────────────────────────────────────────

/** GET /channels — list tenant's notification channels */
app.get('/channels', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const channels = await listChannels(c.env.DB, tenantId);
    return c.json({ success: true, data: channels });
  } catch {
    return c.json({ error: 'Failed to list channels' }, 500);
  }
});

/** POST /channels — add a notification channel */
app.post('/channels', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ channel_type: string; config: Record<string, unknown> }>();

    if (!body.channel_type || !body.config) {
      return c.json({ error: 'channel_type and config are required' }, 400);
    }

    const validTypes = ['email', 'webhook', 'telegram', 'slack', 'in_app'];
    if (!validTypes.includes(body.channel_type)) {
      return c.json({ error: `channel_type must be one of: ${validTypes.join(', ')}` }, 400);
    }

    const channel = await addChannel(c.env.DB, tenantId, body.channel_type, body.config);
    return c.json({ success: true, data: channel }, 201);
  } catch {
    return c.json({ error: 'Failed to add channel' }, 500);
  }
});

/** PUT /channels/:channelId — update channel config or active state */
app.put('/channels/:channelId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const channelId = c.req.param('channelId');
    const body = await c.req.json<{ config?: Record<string, unknown>; is_active?: boolean }>();

    const updated = await updateChannel(c.env.DB, tenantId, channelId, body);
    if (!updated) return c.json({ error: 'Channel not found' }, 404);

    return c.json({ success: true, data: updated });
  } catch {
    return c.json({ error: 'Failed to update channel' }, 500);
  }
});

/** DELETE /channels/:channelId — remove a channel */
app.delete('/channels/:channelId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const channelId = c.req.param('channelId');

    const removed = await removeChannel(c.env.DB, tenantId, channelId);
    if (!removed) return c.json({ error: 'Channel not found' }, 404);

    return c.json({ success: true, data: { id: channelId, deleted: true } });
  } catch {
    return c.json({ error: 'Failed to remove channel' }, 500);
  }
});

// ── Dispatch ───────────────────────────────────────────────────────────────────

/** POST /send — dispatch notification to all active channels */
app.post('/send', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ event_type: string; data: Record<string, unknown> }>();

    if (!body.event_type) {
      return c.json({ error: 'event_type is required' }, 400);
    }

    const logs = await sendNotification(c.env.DB, tenantId, body.event_type, body.data ?? {});
    return c.json({ success: true, data: { dispatched: logs.length, logs } }, 201);
  } catch {
    return c.json({ error: 'Failed to send notification' }, 500);
  }
});

// ── Log & Stats ────────────────────────────────────────────────────────────────

/** GET /log — notification history, query: limit, event_type */
app.get('/log', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const eventType = c.req.query('event_type');

    const logs = await getNotificationLog(c.env.DB, tenantId, limit, eventType);
    return c.json({ success: true, data: logs });
  } catch {
    return c.json({ error: 'Failed to fetch notification log' }, 500);
  }
});

/** GET /stats — aggregated notification stats for tenant */
app.get('/stats', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const stats = await getNotificationStats(c.env.DB, tenantId);
    return c.json({ success: true, data: stats });
  } catch {
    return c.json({ error: 'Failed to fetch stats' }, 500);
  }
});

// ── Templates ──────────────────────────────────────────────────────────────────

/** GET /templates — list all notification templates */
app.get('/templates', auth(), async (c) => {
  try {
    const templates = await listTemplates(c.env.DB);
    return c.json({ success: true, data: templates });
  } catch {
    return c.json({ error: 'Failed to fetch templates' }, 500);
  }
});

/** PUT /templates/:eventType — create or update a template */
app.put('/templates/:eventType', auth(), async (c) => {
  try {
    const eventType = c.req.param('eventType');
    const body = await c.req.json<{ subject: string; body: string; channels?: string[] }>();

    if (!body.subject || !body.body) {
      return c.json({ error: 'subject and body are required' }, 400);
    }

    const template = await upsertTemplate(
      c.env.DB,
      eventType,
      body.subject,
      body.body,
      body.channels ?? ['in_app']
    );
    return c.json({ success: true, data: template });
  } catch {
    return c.json({ error: 'Failed to upsert template' }, 500);
  }
});

// ── Admin ──────────────────────────────────────────────────────────────────────

/** POST /admin/seed-templates — seed default notification templates */
app.post('/admin/seed-templates', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);

  try {
    const seeded = await seedDefaultTemplates(c.env.DB);
    return c.json({ success: true, data: { seeded } });
  } catch {
    return c.json({ error: 'Failed to seed templates' }, 500);
  }
});

/** GET /admin/overview — platform-wide notification stats */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);

  try {
    const overview = await getAdminNotificationOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export const notificationsHub = app;
