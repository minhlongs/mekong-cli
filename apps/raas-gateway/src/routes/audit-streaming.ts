/**
 * Audit Streaming routes — manage stream destinations and delivery lifecycle.
 * Tenant routes protected by auth middleware; admin routes by X-Admin-Key header.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createStreamConfig,
  getStreamConfigs,
  updateStreamConfig,
  deleteStreamConfig,
  publishEvent,
  getPendingDeliveries,
  markDelivered,
  retryFailedDeliveries,
  getDeliveryStats,
} from '../services/audit-streaming-service';

const app = new Hono<{ Bindings: Env }>();

// Tenant auth on all non-admin routes
app.use('/*', async (c, next) => {
  if (c.req.path.includes('/admin/')) return next();
  return auth()(c, next);
});

/** GET /configs — list stream configs for authenticated tenant */
app.get('/configs', async (c) => {
  try {
    const tenant = getTenant(c);
    const configs = await getStreamConfigs(c.env.DB, tenant.tenantId);
    return c.json({ configs, count: configs.length });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** POST /configs — create a new stream destination */
app.post('/configs', async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{
      stream_type?: string;
      destination_url: string;
      auth_header?: string;
      event_filters?: string[];
    }>();

    if (!body.destination_url) {
      return c.json({ error: 'destination_url is required' }, 400);
    }

    const config = await createStreamConfig(c.env.DB, tenant.tenantId, {
      stream_type: body.stream_type ?? 'webhook',
      destination_url: body.destination_url,
      auth_header: body.auth_header,
      event_filters: body.event_filters ?? [],
    });

    return c.json({ config }, 201);
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** GET /stats — delivery statistics for authenticated tenant */
app.get('/stats', async (c) => {
  try {
    const tenant = getTenant(c);
    const stats = await getDeliveryStats(c.env.DB, tenant.tenantId);
    return c.json({ stats });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** POST /publish — publish an audit event to matching stream configs (internal) */
app.post('/publish', async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ event_type: string; payload: Record<string, unknown> }>();

    if (!body.event_type || !body.payload) {
      return c.json({ error: 'event_type and payload are required' }, 400);
    }

    const deliveryIds = await publishEvent(c.env.DB, tenant.tenantId, body.event_type, body.payload);
    return c.json({ queued: deliveryIds.length, delivery_ids: deliveryIds });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** PUT /configs/:id — update a stream config */
app.put('/configs/:id', async (c) => {
  try {
    const tenant = getTenant(c);
    const configId = c.req.param('id');
    const body = await c.req.json<{
      stream_type?: string;
      destination_url?: string;
      auth_header?: string;
      event_filters?: string[];
      is_active?: number;
    }>();

    const updated = await updateStreamConfig(c.env.DB, tenant.tenantId, configId, body);
    if (!updated) return c.json({ error: 'Config not found' }, 404);

    return c.json({ config: updated });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** DELETE /configs/:id — delete a stream config */
app.delete('/configs/:id', async (c) => {
  try {
    const tenant = getTenant(c);
    const configId = c.req.param('id');
    const deleted = await deleteStreamConfig(c.env.DB, tenant.tenantId, configId);
    if (!deleted) return c.json({ error: 'Config not found' }, 404);
    return c.json({ deleted: true });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** GET /admin/pending — list pending deliveries (admin only) */
app.get('/admin/pending', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);

    const { limit = '50' } = c.req.query();
    const deliveries = await getPendingDeliveries(c.env.DB, parseInt(limit, 10));
    return c.json({ deliveries, count: deliveries.length });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** POST /admin/process/:id — mark a delivery as delivered (admin only) */
app.post('/admin/process/:id', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);

    const deliveryId = c.req.param('id');
    const ok = await markDelivered(c.env.DB, deliveryId);
    if (!ok) return c.json({ error: 'Delivery not found' }, 404);
    return c.json({ delivered: true, id: deliveryId });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/** POST /admin/retry/:configId — reset failed deliveries to pending (admin only) */
app.post('/admin/retry/:configId', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);

    const configId = c.req.param('configId');
    const count = await retryFailedDeliveries(c.env.DB, configId);
    return c.json({ retried: count, config_id: configId });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as auditStreaming };
