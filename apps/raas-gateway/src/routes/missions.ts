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
 * GET /missions/templates — List mission templates from DB
 * Supports ?category=content|code|research|marketing|sales|support filter
 */
missions.get('/templates', async (c) => {
  const category = c.req.query('category')?.trim();

  let query = 'SELECT * FROM mission_templates';
  const bindings: string[] = [];

  if (category) {
    query += ' WHERE category = ?';
    bindings.push(category);
  }

  query += ' ORDER BY category, estimated_credits ASC';

  const result = await c.env.DB.prepare(query).bind(...bindings).all<{
    id: string;
    title: string;
    description: string;
    category: string;
    default_complexity: string;
    estimated_credits: number;
    example_goal: string;
    created_at: string;
  }>();

  return json({ templates: result.results, total: result.results.length });
});

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
        'credits-10': 'https://landing.agencyos.network#pricing',
        'credits-50': 'https://landing.agencyos.network#pricing',
        'credits-100': 'https://landing.agencyos.network#pricing',
      },
      subscriptions: {
        starter: 'https://landing.agencyos.network#pricing',
        pro: 'https://landing.agencyos.network#pricing',
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
 * GET /missions — List tenant's missions with search/filter support
 * Supports: ?status=completed, ?from=2026-01-01&to=2026-03-21, ?q=keyword, ?tag=marketing
 */
missions.get('/', async (c) => {
  const tenant = getTenant(c);
  const status = c.req.query('status');
  const limit = Math.min(parseInt(c.req.query('limit') || '20', 10), 100);
  const offset = parseInt(c.req.query('offset') || '0', 10);
  const from = c.req.query('from');
  const to = c.req.query('to');
  const q = c.req.query('q')?.trim();
  const tag = c.req.query('tag')?.trim();

  // Build dynamic query with filters
  let where = 'tenant_id = ?';
  const bindings: (string | number)[] = [tenant.tenantId];

  if (status) { where += ' AND status = ?'; bindings.push(status); }
  if (from) { where += ' AND created_at >= ?'; bindings.push(from); }
  if (to) { where += ' AND created_at <= ?'; bindings.push(to); }
  if (q) { where += ' AND goal LIKE ?'; bindings.push(`%${q}%`); }
  if (tag) { where += ' AND tags LIKE ?'; bindings.push(`%"${tag}"%`); }

  const countRow = await c.env.DB.prepare(
    `SELECT COUNT(*) as total FROM missions WHERE ${where}`
  ).bind(...bindings).first<{ total: number }>();

  const list = await c.env.DB.prepare(
    `SELECT * FROM missions WHERE ${where} ORDER BY created_at DESC LIMIT ? OFFSET ?`
  ).bind(...bindings, limit, offset).all();

  return json({
    missions: list.results,
    total: countRow?.total ?? 0,
    pagination: { limit, offset },
  });
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
 * GET /missions/:id/poll — Lightweight status check (for polling)
 * Returns only status + result availability, no full payload
 */
missions.get('/:id/poll', async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('id');

  const mission = await c.env.DB.prepare(
    "SELECT status, completed_at, created_at, CASE WHEN result IS NOT NULL THEN 1 ELSE 0 END as hasResult FROM missions WHERE id = ? AND tenant_id = ?"
  ).bind(missionId, tenant.tenantId).first<{ status: string; completed_at: string; created_at: string; hasResult: number }>();

  if (!mission) return json({ error: 'Not found' }, { status: 404 });

  // Include queue position for queued missions (count missions submitted before this one)
  let queuePosition: number | undefined;
  if (mission.status === 'queued') {
    const posRow = await c.env.DB.prepare(
      "SELECT COUNT(*) as pos FROM missions WHERE status = 'queued' AND created_at < ?"
    ).bind(mission.created_at).first<{ pos: number }>();
    queuePosition = (posRow?.pos ?? 0) + 1;
  }

  return json({
    id: missionId,
    status: mission.status,
    hasResult: !!mission.hasResult,
    completedAt: mission.completed_at,
    ...(queuePosition !== undefined && { queuePosition }),
  });
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
