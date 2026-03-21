/**
 * Scheduled Missions routes — CRUD and run history for cron-based mission scheduling
 * Mounted at: /v1/scheduled-missions
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createScheduledMission,
  getScheduledMissions,
  getScheduledMission,
  updateScheduledMission,
  deleteScheduledMission,
  pauseScheduledMission,
  resumeScheduledMission,
  recordRun,
  getRunHistory,
  getDueScheduledMissions,
} from '../services/scheduled-mission-service';

export const scheduledMissions = new Hono<{ Bindings: Env }>();

// ── Admin: GET /due — missions ready to execute (X-Admin-Key required) ────────

scheduledMissions.get('/due', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin key required', code: 'FORBIDDEN' }, { status: 403 });
  }

  try {
    const missions = await getDueScheduledMissions(c.env.DB);
    return json({ missions, count: missions.length });
  } catch (err) {
    return json({ error: 'Failed to fetch due missions', details: String(err) }, { status: 500 });
  }
});

// ── GET / — list scheduled missions ──────────────────────────────────────────

scheduledMissions.get('/', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const status = c.req.query('status') as 'active' | 'paused' | 'completed' | 'failed' | undefined;
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 100);
  const offset = Number(c.req.query('offset') ?? 0);

  try {
    const missions = await getScheduledMissions(c.env.DB, tenantId, { status, limit, offset });
    return json({ missions, count: missions.length });
  } catch (err) {
    return json({ error: 'Failed to list scheduled missions', details: String(err) }, { status: 500 });
  }
});

// ── POST / — create scheduled mission ────────────────────────────────────────

scheduledMissions.post('/', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => null);

  if (!body?.name || !body?.cronExpression || !body?.missionConfig) {
    return json({ error: 'name, cronExpression, and missionConfig are required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  if (!body.missionConfig.goal) {
    return json({ error: 'missionConfig.goal is required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  try {
    const mission = await createScheduledMission(c.env.DB, tenantId, {
      name: body.name,
      description: body.description,
      cronExpression: body.cronExpression,
      timezone: body.timezone,
      missionConfig: body.missionConfig,
      maxRuns: body.maxRuns,
    });
    return json({ mission }, { status: 201 });
  } catch (err) {
    const msg = String(err);
    if (msg.includes('Invalid cron')) {
      return json({ error: msg, code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    return json({ error: 'Failed to create scheduled mission', details: msg }, { status: 500 });
  }
});

// ── GET /:id — get single scheduled mission ───────────────────────────────────

scheduledMissions.get('/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const { id } = c.req.param();

  try {
    const mission = await getScheduledMission(c.env.DB, tenantId, id);
    if (!mission) {
      return json({ error: 'Scheduled mission not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ mission });
  } catch (err) {
    return json({ error: 'Failed to fetch scheduled mission', details: String(err) }, { status: 500 });
  }
});

// ── PUT /:id — update scheduled mission ──────────────────────────────────────

scheduledMissions.put('/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const { id } = c.req.param();
  const body = await c.req.json().catch(() => null);

  if (!body) {
    return json({ error: 'Request body required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  try {
    const mission = await updateScheduledMission(c.env.DB, tenantId, id, {
      name: body.name,
      description: body.description,
      cronExpression: body.cronExpression,
      timezone: body.timezone,
      missionConfig: body.missionConfig,
      status: body.status,
      maxRuns: body.maxRuns,
    });
    if (!mission) {
      return json({ error: 'Scheduled mission not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ mission });
  } catch (err) {
    const msg = String(err);
    if (msg.includes('Invalid cron')) {
      return json({ error: msg, code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    return json({ error: 'Failed to update scheduled mission', details: msg }, { status: 500 });
  }
});

// ── DELETE /:id — soft-delete scheduled mission ───────────────────────────────

scheduledMissions.delete('/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const { id } = c.req.param();

  try {
    const deleted = await deleteScheduledMission(c.env.DB, tenantId, id);
    if (!deleted) {
      return json({ error: 'Scheduled mission not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ success: true });
  } catch (err) {
    return json({ error: 'Failed to delete scheduled mission', details: String(err) }, { status: 500 });
  }
});

// ── POST /:id/pause — pause scheduled mission ─────────────────────────────────

scheduledMissions.post('/:id/pause', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const { id } = c.req.param();

  try {
    const mission = await pauseScheduledMission(c.env.DB, tenantId, id);
    if (!mission) {
      return json({ error: 'Scheduled mission not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ mission });
  } catch (err) {
    return json({ error: 'Failed to pause scheduled mission', details: String(err) }, { status: 500 });
  }
});

// ── POST /:id/resume — resume scheduled mission ───────────────────────────────

scheduledMissions.post('/:id/resume', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const { id } = c.req.param();

  try {
    const mission = await resumeScheduledMission(c.env.DB, tenantId, id);
    if (!mission) {
      return json({ error: 'Scheduled mission not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ mission });
  } catch (err) {
    return json({ error: 'Failed to resume scheduled mission', details: String(err) }, { status: 500 });
  }
});

// ── GET /:id/runs — get run history ──────────────────────────────────────────

scheduledMissions.get('/:id/runs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const { id } = c.req.param();

  // Verify mission belongs to tenant
  const mission = await getScheduledMission(c.env.DB, tenantId, id);
  if (!mission) {
    return json({ error: 'Scheduled mission not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  const limit = Math.min(Number(c.req.query('limit') ?? 50), 100);
  const offset = Number(c.req.query('offset') ?? 0);

  try {
    const runs = await getRunHistory(c.env.DB, id, { limit, offset });
    return json({ runs, count: runs.length });
  } catch (err) {
    return json({ error: 'Failed to fetch run history', details: String(err) }, { status: 500 });
  }
});

// ── POST /:id/runs — record a run (internal/admin use) ───────────────────────

scheduledMissions.post('/:id/runs', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin key required', code: 'FORBIDDEN' }, { status: 403 });
  }

  const { id } = c.req.param();
  const body = await c.req.json().catch(() => null);

  if (!body?.status) {
    return json({ error: 'status is required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  // Resolve tenantId from the mission record
  const missionRow = await c.env.DB.prepare(
    'SELECT tenant_id FROM scheduled_missions WHERE id = ?'
  ).bind(id).first() as { tenant_id: string } | null;

  if (!missionRow) {
    return json({ error: 'Scheduled mission not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  try {
    const run = await recordRun(c.env.DB, id, missionRow.tenant_id, {
      missionId: body.missionId,
      status: body.status,
      error: body.error,
    });
    return json({ run }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to record run', details: String(err) }, { status: 500 });
  }
});
