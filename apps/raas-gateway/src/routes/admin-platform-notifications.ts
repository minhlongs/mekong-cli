/**
 * Admin Platform Notifications routes — broadcast notifications + delivery tracking
 * All endpoints: X-Admin-Key required (403 on missing/invalid)
 * GET  /notifications          — list notifications (optional ?notification_type=)
 * POST /notifications          — create a new platform notification
 * GET  /deliveries             — list delivery records (optional ?notification_id=)
 * GET  /dashboard              — aggregated notifications dashboard
 */

import { Hono } from 'hono';
import { adminPlatformNotificationsService } from '../services/admin-platform-notifications';

// Inline Bindings — no import from index to avoid circular deps
interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
}

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard — all routes require valid X-Admin-Key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /notifications — list all platform notifications, optional ?notification_type= filter
app.get('/notifications', async (c) => {
  try {
    const notification_type = c.req.query('notification_type');
    const result = await adminPlatformNotificationsService.listNotifications(
      c.env.DB,
      notification_type
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// POST /notifications — create a new platform notification
// Body: { id, title, message, notification_type?, target_audience?, published_at? }
app.post('/notifications', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const { id, title, message, notification_type, target_audience, published_at } = body as {
      id?: string;
      title?: string;
      message?: string;
      notification_type?: string;
      target_audience?: string;
      published_at?: string;
    };
    if (!id || !title || !message) {
      return c.json({ error: 'id, title, and message are required' }, 400);
    }
    const result = await adminPlatformNotificationsService.createNotification(c.env.DB, {
      id,
      title,
      message,
      notification_type,
      target_audience,
      published_at,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /deliveries — list delivery records, optional ?notification_id= filter
app.get('/deliveries', async (c) => {
  try {
    const notification_id = c.req.query('notification_id');
    const result = await adminPlatformNotificationsService.getDeliveries(
      c.env.DB,
      notification_id
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /dashboard — aggregated platform notifications dashboard summary
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformNotificationsService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminPlatformNotifications };
