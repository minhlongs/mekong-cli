/**
 * Mission Timeline routes — execution tracing and performance analytics
 *
 * Authenticated routes (tenant-scoped):
 *   GET /missions/:id/timeline     — list timeline events for a mission
 *   GET /missions/:id/trace        — get trace summary for a mission
 *   GET /traces                    — list tenant traces (query: status, limit)
 *   GET /traces/:traceId           — get trace by trace_id
 *   GET /performance               — performance stats (query: days=7)
 *
 * Internal routes (no auth — for mission-executor service):
 *   POST /internal/timeline        — add timeline event
 *   POST /internal/trace/start     — start a trace
 *   POST /internal/trace/complete  — complete a trace
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { MissionTimelineService } from '../services/mission-timeline-service';
import { json } from '../utils/response';

export const missionTimeline = new Hono<{ Bindings: Env }>();

const svc = new MissionTimelineService();

// ─── Authenticated routes ────────────────────────────────────────────────────

/**
 * GET /missions/:id/timeline
 * Returns all timeline events for the given mission (tenant-scoped).
 */
missionTimeline.get('/missions/:id/timeline', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = parseInt(c.req.param('id'), 10);

  if (isNaN(missionId)) {
    return json({ success: false, error: 'Invalid mission ID' }, { status: 400 });
  }

  try {
    const events = await svc.getTimeline(c.env.DB, missionId, tenant.tenantId);
    return json({ success: true, data: events });
  } catch (err) {
    console.error('[timeline] getTimeline error', err);
    return json({ success: false, error: 'Failed to fetch timeline' }, { status: 500 });
  }
});

/**
 * GET /missions/:id/trace
 * Returns the trace summary for a mission.
 * Validates the trace belongs to this tenant.
 */
missionTimeline.get('/missions/:id/trace', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = parseInt(c.req.param('id'), 10);

  if (isNaN(missionId)) {
    return json({ success: false, error: 'Invalid mission ID' }, { status: 400 });
  }

  try {
    const trace = await svc.getTrace(c.env.DB, missionId);

    if (!trace) {
      return json({ success: false, error: 'Trace not found' }, { status: 404 });
    }

    // Enforce tenant ownership
    if (trace.tenant_id !== tenant.tenantId) {
      return json({ success: false, error: 'Trace not found' }, { status: 404 });
    }

    return json({ success: true, data: trace });
  } catch (err) {
    console.error('[timeline] getTrace error', err);
    return json({ success: false, error: 'Failed to fetch trace' }, { status: 500 });
  }
});

/**
 * GET /traces
 * List all traces for the authenticated tenant.
 * Query params: status (running|completed|failed), limit (default 20, max 100)
 */
missionTimeline.get('/traces', auth(), async (c) => {
  const tenant = getTenant(c);
  const status = c.req.query('status');
  const limit = parseInt(c.req.query('limit') ?? '20', 10);

  try {
    const traces = await svc.getTenantTraces(c.env.DB, tenant.tenantId, {
      status: status || undefined,
      limit: isNaN(limit) ? 20 : limit,
    });
    return json({ success: true, data: traces });
  } catch (err) {
    console.error('[timeline] getTenantTraces error', err);
    return json({ success: false, error: 'Failed to fetch traces' }, { status: 500 });
  }
});

/**
 * GET /traces/:traceId
 * Fetch a specific trace by its trace_id UUID.
 */
missionTimeline.get('/traces/:traceId', auth(), async (c) => {
  const tenant = getTenant(c);
  const traceId = c.req.param('traceId');

  try {
    const row = await c.env.DB
      .prepare('SELECT * FROM mission_traces WHERE trace_id = ? AND tenant_id = ?')
      .bind(traceId, tenant.tenantId)
      .first<Record<string, unknown>>();

    if (!row) {
      return json({ success: false, error: 'Trace not found' }, { status: 404 });
    }

    return json({ success: true, data: row });
  } catch (err) {
    console.error('[timeline] getTraceById error', err);
    return json({ success: false, error: 'Failed to fetch trace' }, { status: 500 });
  }
});

/**
 * GET /performance
 * Returns performance stats for the tenant over the last N days.
 * Query param: days (default 7)
 */
missionTimeline.get('/performance', auth(), async (c) => {
  const tenant = getTenant(c);
  const days = parseInt(c.req.query('days') ?? '7', 10);

  try {
    const stats = await svc.getPerformanceStats(
      c.env.DB,
      tenant.tenantId,
      isNaN(days) || days < 1 ? 7 : days
    );
    return json({ success: true, data: stats });
  } catch (err) {
    console.error('[timeline] getPerformanceStats error', err);
    return json({ success: false, error: 'Failed to compute performance stats' }, { status: 500 });
  }
});

// ─── Internal routes (no auth — called by mission-executor) ─────────────────

/**
 * POST /internal/timeline
 * Add a timeline event for a mission.
 * Body: { mission_id, tenant_id, event_type, event_data?, duration_ms? }
 */
missionTimeline.post('/internal/timeline', async (c) => {
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  const missionId = typeof body.mission_id === 'number' ? body.mission_id : parseInt(String(body.mission_id), 10);
  const tenantId = typeof body.tenant_id === 'string' ? body.tenant_id.trim() : '';
  const eventType = typeof body.event_type === 'string' ? body.event_type.trim() : '';

  if (!missionId || isNaN(missionId) || !tenantId || !eventType) {
    return json(
      { success: false, error: 'mission_id, tenant_id, and event_type are required' },
      { status: 400 }
    );
  }

  const validEventTypes = ['queued','started','step_begin','step_complete','llm_call','tool_call','error','completed','failed'];
  if (!validEventTypes.includes(eventType)) {
    return json(
      { success: false, error: `Invalid event_type. Must be one of: ${validEventTypes.join(', ')}` },
      { status: 400 }
    );
  }

  try {
    await svc.addEvent(c.env.DB, missionId, tenantId, {
      event_type: eventType as any,
      event_data: (typeof body.event_data === 'object' && body.event_data !== null)
        ? body.event_data as Record<string, unknown>
        : {},
      duration_ms: typeof body.duration_ms === 'number' ? body.duration_ms : undefined,
    });
    return json({ success: true });
  } catch (err) {
    console.error('[timeline] addEvent error', err);
    return json({ success: false, error: 'Failed to add timeline event' }, { status: 500 });
  }
});

/**
 * POST /internal/trace/start
 * Start a trace for a mission.
 * Body: { mission_id, tenant_id }
 */
missionTimeline.post('/internal/trace/start', async (c) => {
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  const missionId = typeof body.mission_id === 'number' ? body.mission_id : parseInt(String(body.mission_id), 10);
  const tenantId = typeof body.tenant_id === 'string' ? body.tenant_id.trim() : '';

  if (!missionId || isNaN(missionId) || !tenantId) {
    return json(
      { success: false, error: 'mission_id and tenant_id are required' },
      { status: 400 }
    );
  }

  try {
    const trace = await svc.startTrace(c.env.DB, missionId, tenantId);
    return json({ success: true, data: trace });
  } catch (err) {
    console.error('[timeline] startTrace error', err);
    return json({ success: false, error: 'Failed to start trace' }, { status: 500 });
  }
});

/**
 * POST /internal/trace/complete
 * Mark a trace as completed or failed.
 * Body: { mission_id, status }
 */
missionTimeline.post('/internal/trace/complete', async (c) => {
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  const missionId = typeof body.mission_id === 'number' ? body.mission_id : parseInt(String(body.mission_id), 10);
  const status = typeof body.status === 'string' ? body.status.trim() : '';

  if (!missionId || isNaN(missionId)) {
    return json({ success: false, error: 'mission_id is required' }, { status: 400 });
  }

  if (status !== 'completed' && status !== 'failed') {
    return json(
      { success: false, error: 'status must be "completed" or "failed"' },
      { status: 400 }
    );
  }

  try {
    await svc.completeTrace(c.env.DB, missionId, status);
    return json({ success: true });
  } catch (err) {
    console.error('[timeline] completeTrace error', err);
    return json({ success: false, error: 'Failed to complete trace' }, { status: 500 });
  }
});
