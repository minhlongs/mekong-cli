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

  const model = ['auto', 'fast', 'balanced', 'premium'].includes(body.model || '')
    ? body.model : 'auto';

  // Premium model requires pro+ tier
  if (model === 'premium' && ['free', 'starter'].includes(tenant.tier)) {
    return json(
      { error: 'Premium model requires Pro tier or higher', code: 'TIER_REQUIRED' },
      { status: 403 }
    );
  }

  const missionService = new MissionService(c.env);
  const result = await missionService.submit(
    tenant.tenantId, goal, complexity, body.project, body.callback_url, model
  );

  if (!result.success) {
    const is402 = result.code === 'INSUFFICIENT_CREDITS' || result.code === 'DAILY_LIMIT_REACHED';
    const upgrade = is402 ? {
      creditPacks: {
        'credits-10': 'https://polar.sh/checkout/cd05c250-42dd-4333-a041-4f55b48044fb',
        'credits-50': 'https://polar.sh/checkout/5c0a8be0-b358-47ea-a006-681920f59676',
        'credits-100': 'https://polar.sh/checkout/c81ca25b-eb3a-43be-8224-de2578c64a94',
      },
      subscriptions: {
        starter: 'https://polar.sh/checkout/ce215739-4684-4deb-b257-8321ea4d844d',
        pro: 'https://polar.sh/checkout/b810b7eb-97f9-4ed0-9c26-07f4bfbbf58f',
      },
    } : undefined;
    return json({ error: result.error, code: result.code, upgrade }, { status: is402 ? 402 : 400 });
  }

  return json(result.mission, { status: 201 });
});

/**
 * POST /missions/batch — Submit up to 10 missions at once (pro+ only)
 */
missions.post('/batch', async (c) => {
  const tenant = getTenant(c);

  // Pro+ only
  if (['free', 'starter'].includes(tenant.tier)) {
    return json(
      { error: 'Batch submission requires Pro tier or higher', code: 'TIER_REQUIRED' },
      { status: 403 }
    );
  }

  const body = await c.req.json().catch(() => ({}));
  const goals = body.goals as Array<{ goal: string; complexity?: string; project?: string }>;

  if (!Array.isArray(goals) || goals.length === 0 || goals.length > 10) {
    return json(
      { error: 'Provide 1-10 goals in array', code: 'INVALID_BATCH' },
      { status: 400 }
    );
  }

  const missionService = new MissionService(c.env);
  const results = [];

  for (const item of goals) {
    const complexity = (['simple', 'standard', 'complex'].includes(item.complexity || '')
      ? item.complexity : 'standard') as 'simple' | 'standard' | 'complex';
    const result = await missionService.submit(tenant.tenantId, item.goal, complexity, item.project);
    results.push(result.success
      ? { id: result.mission!.id, status: 'queued', cost: result.mission!.creditsCost }
      : { error: result.error, code: result.code }
    );
  }

  return json({
    submitted: results.filter(r => 'id' in r).length,
    failed: results.filter(r => 'error' in r).length,
    missions: results,
  }, { status: 201 });
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
 * POST /missions/:id/share — Make mission result public + get share URL
 */
missions.post('/:id/share', async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('id');

  const mission = await c.env.DB.prepare(
    "SELECT id, status FROM missions WHERE id = ? AND tenant_id = ?"
  ).bind(missionId, tenant.tenantId).first<{ id: string; status: string }>();

  if (!mission) return json({ error: 'Mission not found' }, { status: 404 });
  if (mission.status !== 'completed') return json({ error: 'Only completed missions can be shared' }, { status: 400 });

  await c.env.DB.prepare('UPDATE missions SET is_public = 1 WHERE id = ?').bind(missionId).run();

  return json({
    shared: true,
    shareUrl: `https://raas-gateway.agencyos-openclaw.workers.dev/share/${missionId}`,
  });
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
