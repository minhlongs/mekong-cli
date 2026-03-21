/**
 * Event Bus routes — tenant-facing API for mission lifecycle pub/sub.
 * Supports listing events, stats, subscriptions, and emitting events (admin).
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  emitEvent,
  getEventHistory,
  getEventStats,
  subscribeToEvents,
  getSubscriptions,
  type EventType,
} from '../services/event-bus-service';

export const eventBus = new Hono<{ Bindings: Env }>();
eventBus.use('*', auth());

/** GET /event-bus/events — paginated event history for the authenticated tenant */
eventBus.get('/events', async (c) => {
  try {
    const tenant = getTenant(c);
    const { type, limit = '20', offset = '0' } = c.req.query();
    const result = await getEventHistory(c.env.DB, tenant.tenantId, {
      type: type || undefined,
      limit: Math.min(Number(limit) || 20, 100),
      offset: Number(offset) || 0,
    });
    return json({ ...result, limit: Number(limit), offset: Number(offset) });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to fetch events';
    return json({ error: msg, code: 'FETCH_ERROR' }, { status: 500 });
  }
});

/** GET /event-bus/stats — event count statistics for the authenticated tenant */
eventBus.get('/stats', async (c) => {
  try {
    const tenant = getTenant(c);
    const stats = await getEventStats(c.env.DB, tenant.tenantId);
    return json({ stats });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to fetch stats';
    return json({ error: msg, code: 'FETCH_ERROR' }, { status: 500 });
  }
});

/** POST /event-bus/subscribe — register a webhook subscription for selected event types */
eventBus.post('/subscribe', async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ event_types?: string[]; webhook_url?: string }>();

    if (!Array.isArray(body.event_types) || !body.event_types.length) {
      return json({ error: 'event_types must be a non-empty array', code: 'INVALID_INPUT' }, { status: 400 });
    }
    if (!body.webhook_url || typeof body.webhook_url !== 'string') {
      return json({ error: 'webhook_url is required', code: 'INVALID_INPUT' }, { status: 400 });
    }

    const id = await subscribeToEvents(
      c.env.DB,
      tenant.tenantId,
      body.event_types,
      body.webhook_url,
    );
    return json({ id, message: 'Subscription created' }, { status: 201 });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to create subscription';
    return json({ error: msg, code: 'SUBSCRIBE_ERROR' }, { status: 500 });
  }
});

/** GET /event-bus/subscriptions — list active subscriptions for the authenticated tenant */
eventBus.get('/subscriptions', async (c) => {
  try {
    const tenant = getTenant(c);
    const subscriptions = await getSubscriptions(c.env.DB, tenant.tenantId);
    return json({ subscriptions });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to fetch subscriptions';
    return json({ error: msg, code: 'FETCH_ERROR' }, { status: 500 });
  }
});

/** DELETE /event-bus/subscriptions/:id — deactivate a subscription */
eventBus.delete('/subscriptions/:id', async (c) => {
  try {
    const tenant = getTenant(c);
    const subId = c.req.param('id');

    const result = await c.env.DB
      .prepare(
        `UPDATE event_subscriptions SET active = 0
         WHERE id = ? AND tenant_id = ? AND active = 1`,
      )
      .bind(subId, tenant.tenantId)
      .run();

    if (!result.meta?.changes) {
      return json({ error: 'Subscription not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ message: 'Subscription cancelled' });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to cancel subscription';
    return json({ error: msg, code: 'DELETE_ERROR' }, { status: 500 });
  }
});

/** POST /event-bus/emit — emit a custom event (admin/internal use) */
eventBus.post('/emit', async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ type?: string; payload?: Record<string, any> }>();

    if (!body.type) {
      return json({ error: 'type is required', code: 'INVALID_INPUT' }, { status: 400 });
    }

    const id = await emitEvent(
      c.env.DB,
      body.type as EventType,
      tenant.tenantId,
      body.payload ?? {},
    );
    return json({ id, message: 'Event emitted' }, { status: 201 });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to emit event';
    return json({ error: msg, code: 'EMIT_ERROR' }, { status: 500 });
  }
});
