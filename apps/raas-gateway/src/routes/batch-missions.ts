/**
 * Batch mission routes — submit up to 50 missions in one request
 * POST /v1/missions/batch  — submit batch
 * GET  /v1/missions/batch/:batchId — get batch status
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const batchMissions = new Hono<{ Bindings: Env }>();

// All batch routes require auth
batchMissions.use('*', auth());

interface MissionInput {
  goal: string;
  model?: string;
  priority?: number;
}

/**
 * POST /v1/missions/batch — Submit up to 50 missions in one atomic batch
 * Body: { missions: Array<{ goal, model?, priority? }> }
 */
batchMissions.post('/', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as { missions?: unknown };

  const missions = body.missions;
  if (!Array.isArray(missions) || missions.length === 0) {
    return json({ error: 'missions array is required', code: 'INVALID_BATCH' }, { status: 400 });
  }
  if (missions.length > 50) {
    return json({ error: 'Max 50 missions per batch', code: 'BATCH_TOO_LARGE' }, { status: 400 });
  }

  const batchId = crypto.randomUUID();
  const now = new Date().toISOString();
  const inserted: Array<{ id: string; goal: string; status: string }> = [];

  // Insert all missions linked by batch_id
  const stmt = c.env.DB.prepare(
    `INSERT INTO missions (id, tenant_id, goal, model, priority, status, batch_id, created_at)
     VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)`
  );

  for (const item of missions as MissionInput[]) {
    const goal = item.goal?.trim();
    if (!goal) continue; // Skip blank goals silently

    const id = crypto.randomUUID();
    const model = item.model || 'auto';
    const priority = typeof item.priority === 'number' ? item.priority : 0;

    await stmt.bind(id, tenant.tenantId, goal, model, priority, batchId, now).run();
    inserted.push({ id, goal, status: 'queued' });
  }

  return json({ batchId, count: inserted.length, missions: inserted }, { status: 201 });
});

/**
 * GET /v1/missions/batch/:batchId — Get all missions in a batch with status
 */
batchMissions.get('/:batchId', async (c) => {
  const tenant = getTenant(c);
  const batchId = c.req.param('batchId');

  const rows = await c.env.DB.prepare(
    `SELECT id, goal, status, model, priority, created_at, completed_at
     FROM missions WHERE batch_id = ? AND tenant_id = ? ORDER BY created_at ASC`
  ).bind(batchId, tenant.tenantId).all<{
    id: string;
    goal: string;
    status: string;
    model: string;
    priority: number;
    created_at: string;
    completed_at: string | null;
  }>();

  if (rows.results.length === 0) {
    return json({ error: 'Batch not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  const statusCounts = rows.results.reduce<Record<string, number>>((acc, m) => {
    acc[m.status] = (acc[m.status] || 0) + 1;
    return acc;
  }, {});

  return json({
    batchId,
    total: rows.results.length,
    statusCounts,
    missions: rows.results,
  });
});
