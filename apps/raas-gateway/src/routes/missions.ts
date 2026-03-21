/**
 * Mission routes — submit, track, cancel agent missions
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { getTenant } from '../middleware/auth';
import { MissionService } from '../services/mission-service';
import { json } from '../utils/response';

export const missions = new Hono<{ Bindings: Env }>();

/**
 * POST /missions — Submit a new mission
 * Deducts credits based on complexity (simple=1, standard=3, complex=5)
 */
missions.post('/', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));

  const goal = body.goal?.trim();
  if (!goal || goal.length < 3) {
    return json(
      { error: 'Goal is required (min 3 characters)', code: 'INVALID_GOAL' },
      { status: 400 }
    );
  }

  if (goal.length > 2000) {
    return json(
      { error: 'Goal too long (max 2000 characters)', code: 'INVALID_GOAL' },
      { status: 400 }
    );
  }

  const complexity = ['simple', 'standard', 'complex'].includes(body.complexity)
    ? body.complexity
    : 'standard';

  const missionService = new MissionService(c.env);
  const result = await missionService.submit(tenant.tenantId, goal, complexity, body.project);

  if (!result.success) {
    const status = result.code === 'INSUFFICIENT_CREDITS' ? 402 : 400;
    return json({ error: result.error, code: result.code }, { status });
  }

  return json(result.mission, { status: 201 });
});

/**
 * GET /missions — List tenant's missions
 */
missions.get('/', async (c) => {
  const tenant = getTenant(c);
  const status = c.req.query('status');
  const limit = parseInt(c.req.query('limit') || '20', 10);
  const offset = parseInt(c.req.query('offset') || '0', 10);

  const missionService = new MissionService(c.env);
  const { missions: list, total } = await missionService.list(tenant.tenantId, {
    status, limit, offset,
  });

  return json({ missions: list, total, pagination: { limit, offset } });
});

/**
 * GET /missions/:id — Get mission details
 */
missions.get('/:id', async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('id');

  const missionService = new MissionService(c.env);
  const mission = await missionService.get(missionId, tenant.tenantId);

  if (!mission) {
    return json({ error: 'Mission not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  return json(mission);
});

/**
 * POST /missions/:id/cancel — Cancel a queued mission (refunds credits)
 */
missions.post('/:id/cancel', async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('id');

  const missionService = new MissionService(c.env);
  const result = await missionService.cancel(missionId, tenant.tenantId);

  if (!result.success) {
    return json({ error: result.error, code: 'CANCEL_FAILED' }, { status: 400 });
  }

  return json({ cancelled: true, missionId });
});
