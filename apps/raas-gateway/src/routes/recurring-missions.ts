/**
 * Recurring Missions routes — CRUD + manual trigger for scheduled missions
 * All routes require auth middleware
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { RecurringMissionService } from '../services/recurring-mission-service';
import { json } from '../utils/response';

export const recurringMissions = new Hono<{ Bindings: Env }>();

// Apply auth middleware to all routes
recurringMissions.use('*', auth());

const svc = new RecurringMissionService();

/**
 * POST / — Create a new recurring mission
 * Required: name, type, cron_expression
 */
recurringMissions.post('/', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));

  const name = body.name?.trim();
  const type = body.type?.trim();
  const cronExpr = body.cron_expression?.trim();

  if (!name) return json({ success: false, error: 'name is required', code: 'VALIDATION_ERROR' }, { status: 400 });
  if (!type) return json({ success: false, error: 'type is required', code: 'VALIDATION_ERROR' }, { status: 400 });
  if (!cronExpr) return json({ success: false, error: 'cron_expression is required', code: 'VALIDATION_ERROR' }, { status: 400 });

  try {
    const mission = await svc.create(c.env.DB, tenant.tenantId, {
      name,
      type,
      cron_expression: cronExpr,
      input: body.input ?? {},
      timezone: body.timezone ?? 'UTC',
      max_runs: body.max_runs ?? undefined,
    });
    return json({ success: true, data: mission }, { status: 201 });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to create recurring mission';
    return json({ success: false, error: msg, code: 'CREATE_FAILED' }, { status: 400 });
  }
});

/**
 * GET / — List tenant's recurring missions
 * Query: ?active=true|false (omit for all)
 */
recurringMissions.get('/', async (c) => {
  const tenant = getTenant(c);
  const activeParam = c.req.query('active');

  const opts: { active?: boolean } = {};
  if (activeParam === 'true') opts.active = true;
  else if (activeParam === 'false') opts.active = false;

  try {
    const missions = await svc.list(c.env.DB, tenant.tenantId, opts);
    return json({ success: true, data: missions, total: missions.length });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to list recurring missions';
    return json({ success: false, error: msg, code: 'LIST_FAILED' }, { status: 500 });
  }
});

/**
 * GET /:id — Get a single recurring mission
 */
recurringMissions.get('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = parseInt(c.req.param('id'), 10);

  if (isNaN(id)) {
    return json({ success: false, error: 'Invalid id', code: 'INVALID_ID' }, { status: 400 });
  }

  try {
    const mission = await svc.getById(c.env.DB, id, tenant.tenantId);
    if (!mission) {
      return json({ success: false, error: 'Not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ success: true, data: mission });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to get recurring mission';
    return json({ success: false, error: msg, code: 'GET_FAILED' }, { status: 500 });
  }
});

/**
 * PUT /:id — Update name, cron_expression, is_active, input
 */
recurringMissions.put('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = parseInt(c.req.param('id'), 10);

  if (isNaN(id)) {
    return json({ success: false, error: 'Invalid id', code: 'INVALID_ID' }, { status: 400 });
  }

  const body = await c.req.json().catch(() => ({}));

  try {
    const updated = await svc.update(c.env.DB, id, tenant.tenantId, {
      name: body.name?.trim(),
      cron_expression: body.cron_expression?.trim(),
      is_active: body.is_active,
      input: body.input,
      max_runs: body.max_runs,
    });
    return json({ success: true, data: updated });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to update recurring mission';
    const status = msg.includes('not found') ? 404 : 400;
    return json({ success: false, error: msg, code: 'UPDATE_FAILED' }, { status });
  }
});

/**
 * DELETE /:id — Soft delete (set is_active = 0)
 */
recurringMissions.delete('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = parseInt(c.req.param('id'), 10);

  if (isNaN(id)) {
    return json({ success: false, error: 'Invalid id', code: 'INVALID_ID' }, { status: 400 });
  }

  try {
    await svc.delete(c.env.DB, id, tenant.tenantId);
    return json({ success: true, data: { id, deleted: true } });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to delete recurring mission';
    const status = msg.includes('not found') ? 404 : 400;
    return json({ success: false, error: msg, code: 'DELETE_FAILED' }, { status });
  }
});

/**
 * POST /:id/trigger — Manually trigger a run immediately
 * Inserts a mission into the missions queue right now
 */
recurringMissions.post('/:id/trigger', async (c) => {
  const tenant = getTenant(c);
  const id = parseInt(c.req.param('id'), 10);

  if (isNaN(id)) {
    return json({ success: false, error: 'Invalid id', code: 'INVALID_ID' }, { status: 400 });
  }

  try {
    const rm = await svc.getById(c.env.DB, id, tenant.tenantId);
    if (!rm) {
      return json({ success: false, error: 'Not found', code: 'NOT_FOUND' }, { status: 404 });
    }

    const missionId = crypto.randomUUID();
    const inputData = (() => {
      try { return JSON.parse(rm.input); } catch { return {}; }
    })();

    await c.env.DB.prepare(
      `INSERT INTO missions (id, tenant_id, goal, complexity, status, created_at)
       VALUES (?, ?, ?, 'standard', 'queued', datetime('now'))`
    ).bind(
      missionId,
      rm.tenant_id,
      inputData.goal ?? `[Recurring] ${rm.name} (${rm.type})`
    ).run();

    // Update run stats
    const { getNextRun } = await import('../services/recurring-mission-service');
    const nextRun = getNextRun(rm.cron_expression, rm.timezone);

    await c.env.DB.prepare(
      `UPDATE recurring_missions SET
         last_run_at = datetime('now'),
         next_run_at = ?,
         run_count = run_count + 1,
         updated_at = datetime('now')
       WHERE id = ?`
    ).bind(nextRun, rm.id).run();

    return json({ success: true, data: { missionId, recurringId: id, queued: true } });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to trigger mission';
    return json({ success: false, error: msg, code: 'TRIGGER_FAILED' }, { status: 500 });
  }
});
