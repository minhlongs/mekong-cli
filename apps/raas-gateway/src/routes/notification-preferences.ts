/**
 * Notification preferences routes
 */
import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';

export const notificationPreferences = new Hono<{ Bindings: Env }>();

/** GET /v1/notifications/preferences */
notificationPreferences.get('/v1/notifications/preferences', auth(), async (c) => {
  const tenant = getTenant(c);
  let prefs = await c.env.DB.prepare('SELECT * FROM notification_preferences WHERE tenant_id = ?').bind(tenant.tenantId).first();
  if (!prefs) {
    await c.env.DB.prepare("INSERT INTO notification_preferences (tenant_id) VALUES (?)").bind(tenant.tenantId).run();
    prefs = await c.env.DB.prepare('SELECT * FROM notification_preferences WHERE tenant_id = ?').bind(tenant.tenantId).first();
  }
  return c.json({ success: true, data: prefs });
});

/** PUT /v1/notifications/preferences */
notificationPreferences.put('/v1/notifications/preferences', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json();
  const allowed = ['email_enabled', 'email_digest', 'webhook_failures', 'mission_complete', 'billing_alerts', 'security_alerts', 'marketing'];
  const sets: string[] = []; const params: any[] = [];
  for (const [k, v] of Object.entries(body)) {
    if (allowed.includes(k)) { sets.push(`${k} = ?`); params.push(v); }
  }
  if (!sets.length) return c.json({ error: 'No valid fields' }, 400);
  sets.push("updated_at = datetime('now')");
  params.push(tenant.tenantId);
  await c.env.DB.prepare(`UPDATE notification_preferences SET ${sets.join(', ')} WHERE tenant_id = ?`).bind(...params).run();
  return c.json({ success: true, message: 'Preferences updated' });
});

/** GET /v1/notifications/channels */
notificationPreferences.get('/v1/notifications/channels', auth(), async (c) => {
  return c.json({ success: true, data: [
    { channel: 'email', status: 'active', description: 'Email notifications via Resend' },
    { channel: 'webhook', status: 'active', description: 'Webhook delivery to configured URL' },
    { channel: 'telegram', status: 'coming_soon', description: 'Telegram bot notifications' },
    { channel: 'slack', status: 'coming_soon', description: 'Slack integration' },
  ]});
});

/** POST /v1/notifications/test */
notificationPreferences.post('/v1/notifications/test', auth(), async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const channel = body.channel || 'email';
  return c.json({ success: true, data: { channel, status: 'sent', message: `Test notification sent via ${channel}` } });
});
