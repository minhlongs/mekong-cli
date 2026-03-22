/**
 * Mission Replay & Debug routes — execution trace, debug sessions, replay
 *
 * Mount path: /v1/mission-debug
 *
 * Tenant (auth):
 *   GET  /missions/:missionId/steps   — execution steps
 *   GET  /missions/:missionId/trace   — full trace
 *   POST /sessions                    — create debug session
 *   GET  /sessions/:id                — get debug session
 *   PUT  /sessions/:id                — update debug session
 *   POST /replay                      — start replay
 *   GET  /replay/:id                  — replay status
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview              — platform overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  getExecutionSteps,
  getMissionTrace,
  createDebugSession,
  getDebugSession,
  updateDebugSession,
  startReplay,
  getReplayStatus,
  getAdminOverview,
} from '../services/mission-replay-debug-service';

type HonoEnv = { Bindings: Env };

const app = new Hono<HonoEnv>();

// ---------------------------------------------------------------------------
// Tenant routes
// ---------------------------------------------------------------------------

/** GET /missions/:missionId/steps — execution step list */
app.get('/missions/:missionId/steps', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('missionId');
  try {
    const steps = await getExecutionSteps(c.env.DB, tenant.tenantId, missionId);
    return c.json({ success: true, data: { mission_id: missionId, steps, count: steps.length } });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

/** GET /missions/:missionId/trace — full mission trace (steps + sessions + replays) */
app.get('/missions/:missionId/trace', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('missionId');
  try {
    const trace = await getMissionTrace(c.env.DB, tenant.tenantId, missionId);
    return c.json({ success: true, data: { mission_id: missionId, ...trace } });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

/** POST /sessions — create debug session */
app.post('/sessions', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, 400);
  }
  if (!body.mission_id) return c.json({ error: 'mission_id required', code: 'BAD_REQUEST' }, 400);
  try {
    const session = await createDebugSession(c.env.DB, tenant.tenantId, {
      mission_id: body.mission_id as string,
      debug_mode: body.debug_mode as string | undefined,
      breakpoints: body.breakpoints as number[] | undefined,
      notes: body.notes as string | undefined,
    });
    return c.json({ success: true, data: session }, 201);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

/** GET /sessions/:id — get debug session */
app.get('/sessions/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  try {
    const session = await getDebugSession(c.env.DB, tenant.tenantId, id);
    if (!session) return c.json({ error: 'Session not found', code: 'NOT_FOUND' }, 404);
    return c.json({ success: true, data: session });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

/** PUT /sessions/:id — update debug session */
app.put('/sessions/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, 400);
  }
  try {
    const session = await updateDebugSession(c.env.DB, tenant.tenantId, id, {
      current_step: body.current_step as number | undefined,
      session_status: body.session_status as string | undefined,
      notes: body.notes as string | undefined,
      breakpoints: body.breakpoints as number[] | undefined,
    });
    if (!session) return c.json({ error: 'Session not found', code: 'NOT_FOUND' }, 404);
    return c.json({ success: true, data: session });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

/** POST /replay — start a mission replay */
app.post('/replay', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, 400);
  }
  if (!body.mission_id) return c.json({ error: 'mission_id required', code: 'BAD_REQUEST' }, 400);
  try {
    const replay = await startReplay(c.env.DB, tenant.tenantId, body.mission_id as string);
    return c.json({ success: true, data: replay }, 201);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

/** GET /replay/:id — get replay status */
app.get('/replay/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  try {
    const replay = await getReplayStatus(c.env.DB, tenant.tenantId, id);
    if (!replay) return c.json({ error: 'Replay not found', code: 'NOT_FOUND' }, 404);
    return c.json({ success: true, data: replay });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

// ---------------------------------------------------------------------------
// Admin routes
// ---------------------------------------------------------------------------

/** GET /admin/overview — platform-wide debug stats */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, 401);
  }
  try {
    const overview = await getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'DB error' }, 500);
  }
});

export { app as missionReplayDebug };
