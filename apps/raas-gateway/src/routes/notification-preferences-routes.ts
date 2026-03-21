/**
 * Notification Preferences sub-routes
 * Mounted under /v1/notifications by notifications.ts
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { getTenant } from '../middleware/auth';
import { getPreferences, updatePreferences } from '../services/notification-service';
import type { NotificationChannel } from '../services/notification-types';

const VALID_CHANNELS: NotificationChannel[] = ['in_app', 'email', 'push', 'webhook'];

export const notificationPreferencesRoutes = new Hono<{ Bindings: Env }>();

/**
 * GET /preferences — get all channel preferences for tenant
 */
notificationPreferencesRoutes.get('/', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const prefs = await getPreferences(c.env.DB, tenantId);
    return c.json({ success: true, data: prefs });
  } catch {
    return c.json({ error: 'Failed to fetch preferences' }, 500);
  }
});

/**
 * PUT /preferences/:channel — upsert preference for a specific channel
 * Body: { enabled, quietHoursStart?, quietHoursEnd? }
 */
notificationPreferencesRoutes.put('/:channel', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const channel = c.req.param('channel') as NotificationChannel;

    if (!VALID_CHANNELS.includes(channel)) {
      return c.json({ error: `Invalid channel. Must be one of: ${VALID_CHANNELS.join(', ')}` }, 400);
    }

    const body = await c.req.json<{
      enabled: boolean;
      quietHoursStart?: string;
      quietHoursEnd?: string;
    }>();

    if (typeof body.enabled !== 'boolean') {
      return c.json({ error: 'enabled (boolean) is required' }, 400);
    }

    const pref = await updatePreferences(c.env.DB, tenantId, channel, body);
    return c.json({ success: true, data: pref });
  } catch {
    return c.json({ error: 'Failed to update preference' }, 500);
  }
});
