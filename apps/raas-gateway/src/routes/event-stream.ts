/**
 * SSE Event Stream Routes — real-time mission updates via Server-Sent Events
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createSSEStream,
  publishEvent,
  getActiveStreams,
} from '../services/event-stream-service';

export const eventStream = new Hono<{ Bindings: Env }>();

// SSE headers shared across stream endpoints
const SSE_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
  'X-Accel-Buffering': 'no',
};

// GET /events/stream — tenant-wide SSE stream (auth required)
eventStream.get('/stream', auth(), (c) => {
  const { tenantId } = getTenant(c);
  const stream = createSSEStream(tenantId, c.env.DB);
  return new Response(stream, { headers: SSE_HEADERS });
});

// GET /events/missions/:missionId — SSE stream filtered to a single mission (auth required)
eventStream.get('/missions/:missionId', auth(), (c) => {
  const { tenantId } = getTenant(c);
  const missionId = c.req.param('missionId');
  const stream = createSSEStream(tenantId, c.env.DB, missionId);
  return new Response(stream, { headers: SSE_HEADERS });
});

// POST /events/publish — publish a mission event (auth required, internal use)
eventStream.post('/publish', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json<{ mission_id: string; event_type: string; payload?: unknown }>();
    const { mission_id, event_type, payload } = body;

    if (!mission_id || !event_type) {
      return json({ error: 'mission_id and event_type are required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }

    await publishEvent(c.env.DB, tenantId, mission_id, event_type, payload ?? {});
    return json({ ok: true, tenantId, mission_id, event_type });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return json({ error: message, code: 'PUBLISH_ERROR' }, { status: 500 });
  }
});

// GET /events/active — count active SSE streams (auth required)
eventStream.get('/active', auth(), (c) => {
  const { tenantId } = getTenant(c);
  return json({
    active_streams: getActiveStreams(),
    tenant_streams: getActiveStreams(tenantId),
  });
});
