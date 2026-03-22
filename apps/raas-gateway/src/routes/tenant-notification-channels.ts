/**
 * Tenant Notification Channels routes — channel management and delivery tracking
 * Mount at: /v1/notification-channels
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  listChannels,
  createChannel,
  getDeliveries,
  getAdminOverview,
} from '../services/tenant-notification-channels-service';

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

/** GET /channels — list notification channels for authenticated tenant */
app.get('/channels', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const channels = await listChannels(c.env.DB, tenantId);
    return json({ channels });
  } catch {
    return json({ error: 'Failed to fetch channels' }, { status: 500 });
  }
});

/** POST /channels — create a notification channel for authenticated tenant */
app.post('/channels', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json().catch(() => ({}));
    const { channel_type, config_json, is_active } = body as {
      channel_type?: string;
      config_json?: string;
      is_active?: number;
    };

    if (!channel_type || typeof channel_type !== 'string') {
      return json({ error: 'channel_type is required', code: 'INVALID_INPUT' }, { status: 400 });
    }

    const channel = await createChannel(c.env.DB, tenantId, { channel_type, config_json, is_active });
    return json({ channel }, { status: 201 });
  } catch {
    return json({ error: 'Failed to create channel' }, { status: 500 });
  }
});

/** GET /deliveries — list notification deliveries for authenticated tenant */
app.get('/deliveries', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const deliveries = await getDeliveries(c.env.DB, tenantId);
    return json({ deliveries });
  } catch {
    return json({ error: 'Failed to fetch deliveries' }, { status: 500 });
  }
});

/** GET /admin/overview — aggregate stats (X-Admin-Key required) */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  }
  try {
    const overview = await getAdminOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch admin overview' }, { status: 500 });
  }
});

export { app as tenantNotificationChannels };
