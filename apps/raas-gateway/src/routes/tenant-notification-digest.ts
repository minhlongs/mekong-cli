/**
 * Tenant Notification Digest Routes
 * Per-tenant digest configuration and delivery inspection.
 *
 * GET  /configs        — list digest configs (auth)
 * POST /configs        — create digest config (auth)
 * GET  /deliveries     — list delivery records (auth)
 * GET  /admin/overview — cross-tenant stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantNotificationDigestService } from '../services/tenant-notification-digest-service';

export const tenantNotificationDigest = new Hono<{ Bindings: Env }>();

// GET /configs — list digest configs for authenticated tenant
tenantNotificationDigest.get('/configs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const configs = await tenantNotificationDigestService.listConfigs(c.env.DB, tenantId);
    return c.json({ configs, total: configs.length });
  } catch (err) {
    return c.json({ error: 'Failed to list digest configs' }, 500);
  }
});

// POST /configs — create a new digest config for authenticated tenant
tenantNotificationDigest.post('/configs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json().catch(() => ({})) as {
      digest_frequency?: string;
      channels_json?: string;
      include_types?: string;
    };
    const config = await tenantNotificationDigestService.createConfig(c.env.DB, tenantId, body);
    return c.json(config, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create digest config' }, 500);
  }
});

// GET /deliveries — list delivery records for authenticated tenant
tenantNotificationDigest.get('/deliveries', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const deliveries = await tenantNotificationDigestService.getDeliveries(c.env.DB, tenantId);
    return c.json({ deliveries, total: deliveries.length });
  } catch (err) {
    return c.json({ error: 'Failed to list deliveries' }, 500);
  }
});

// GET /admin/overview — cross-tenant stats (X-Admin-Key required)
tenantNotificationDigest.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden', code: 'FORBIDDEN' }, 403);
  }
  try {
    const overview = await tenantNotificationDigestService.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (err) {
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});
