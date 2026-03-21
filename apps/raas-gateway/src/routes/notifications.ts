/**
 * Notifications routes — Notification Center API
 * Mount at /v1/notifications in parent router
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  sendNotification,
  getNotifications,
  markAsRead,
  markAllRead,
  getUnreadCount,
} from '../services/notification-service';
import { notificationPreferencesRoutes } from './notification-preferences-routes';
import {
  createTemplate,
  getTemplates,
  sendFromTemplate,
} from '../services/notification-template-service';
import type { NotificationChannel, NotificationStatus } from '../services/notification-types';

const app = new Hono<{ Bindings: Env }>();

// All notification routes require JWT auth
app.use('/*', auth());

/**
 * GET /v1/notifications — list notifications with optional filters
 * Query: status, limit, offset
 */
app.get('/', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const status = c.req.query('status') as NotificationStatus | undefined;
    const limit = parseInt(c.req.query('limit') ?? '20', 10);
    const offset = parseInt(c.req.query('offset') ?? '0', 10);

    const result = await getNotifications(c.env.DB, tenantId, { status, limit, offset });
    return c.json({ success: true, data: result });
  } catch (err) {
    return c.json({ error: 'Failed to fetch notifications' }, 500);
  }
});

/**
 * POST /v1/notifications/send — send a notification directly
 * Body: { channel, recipient, subject?, body, templateId?, metadata? }
 */
app.post('/send', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      channel: NotificationChannel;
      recipient: string;
      subject?: string;
      body: string;
      templateId?: string;
      metadata?: Record<string, unknown>;
    }>();

    if (!body.channel || !body.recipient || !body.body) {
      return c.json({ error: 'channel, recipient, and body are required' }, 400);
    }

    const notification = await sendNotification(c.env.DB, tenantId, body);
    return c.json({ success: true, data: notification }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to send notification' }, 500);
  }
});

/**
 * GET /v1/notifications/unread-count — count unread notifications
 */
app.get('/unread-count', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const count = await getUnreadCount(c.env.DB, tenantId);
    return c.json({ success: true, data: { count } });
  } catch (err) {
    return c.json({ error: 'Failed to get unread count' }, 500);
  }
});

/**
 * PUT /v1/notifications/read-all — mark all notifications as read
 */
app.put('/read-all', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const updated = await markAllRead(c.env.DB, tenantId);
    return c.json({ success: true, data: { updated } });
  } catch (err) {
    return c.json({ error: 'Failed to mark all as read' }, 500);
  }
});

/**
 * PUT /v1/notifications/:id/read — mark a single notification as read
 */
app.put('/:id/read', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const id = c.req.param('id');
    const updated = await markAsRead(c.env.DB, tenantId, id);

    if (!updated) {
      return c.json({ error: 'Notification not found or already read' }, 404);
    }

    return c.json({ success: true, data: { id, status: 'read' } });
  } catch (err) {
    return c.json({ error: 'Failed to mark as read' }, 500);
  }
});

/**
 * POST /v1/notifications/templates — create a notification template
 * Body: { name, channel, subject?, bodyTemplate, variables? }
 */
app.post('/templates', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name: string;
      channel: NotificationChannel;
      subject?: string;
      bodyTemplate: string;
      variables?: string[];
    }>();

    if (!body.name || !body.channel || !body.bodyTemplate) {
      return c.json({ error: 'name, channel, and bodyTemplate are required' }, 400);
    }

    const template = await createTemplate(c.env.DB, tenantId, body);
    return c.json({ success: true, data: template }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create template' }, 500);
  }
});

/**
 * GET /v1/notifications/templates — list all templates for tenant
 */
app.get('/templates', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const templates = await getTemplates(c.env.DB, tenantId);
    return c.json({ success: true, data: templates });
  } catch (err) {
    return c.json({ error: 'Failed to fetch templates' }, 500);
  }
});

/**
 * POST /v1/notifications/templates/:id/send — send from template
 * Body: { recipient, variables? }
 */
app.post('/templates/:id/send', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const templateId = c.req.param('id');
    const body = await c.req.json<{
      recipient: string;
      variables?: Record<string, string>;
    }>();

    if (!body.recipient) {
      return c.json({ error: 'recipient is required' }, 400);
    }

    const notification = await sendFromTemplate(c.env.DB, tenantId, {
      templateId,
      recipient: body.recipient,
      variables: body.variables,
    });

    return c.json({ success: true, data: notification }, 201);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to send from template';
    const status = message === 'Template not found' ? 404 : 500;
    return c.json({ error: message }, status);
  }
});

// Mount preferences sub-router
app.route('/preferences', notificationPreferencesRoutes);

export const notifications = app;
