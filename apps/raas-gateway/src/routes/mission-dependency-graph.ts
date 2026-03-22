/**
 * Mission Dependency Graph routes — DAG dependencies, execution groups,
 * critical path analysis for RaaS missions.
 * Auth:  POST/DELETE/GET /dependencies, GET /graph/:rootMissionId
 *        GET/POST /groups, PUT /groups/:id/status
 *        POST /analyze/:rootMissionId, GET /analyses
 * Admin: GET /admin/overview (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { missionDependencyGraphService as svc } from '../services/mission-dependency-graph-service';

export const missionDependencyGraph = new Hono<{ Bindings: Env }>();

// ── Dependency routes ────────────────────────────────────────────────────────

/** POST /dependencies — add dependency; body: { parent_mission_id, child_mission_id, dependency_type? } */
missionDependencyGraph.post('/dependencies', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const parent = String(body.parent_mission_id ?? '').trim();
  const child = String(body.child_mission_id ?? '').trim();
  if (!parent || !child) {
    return json({ error: 'parent_mission_id and child_mission_id are required', code: 'INVALID_INPUT' }, { status: 400 });
  }
  try {
    const dep = await svc.addDependency(c.env.DB, tenantId, {
      parent_mission_id: parent,
      child_mission_id: child,
      dependency_type: body.dependency_type ? String(body.dependency_type) : undefined,
    });
    return json({ dependency: dep }, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** DELETE /dependencies/:id — remove dependency */
missionDependencyGraph.delete('/dependencies/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await svc.removeDependency(c.env.DB, tenantId, c.req.param('id'));
    if (!result) return json({ error: 'Dependency not found', code: 'NOT_FOUND' }, { status: 404 });
    return json(result);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** GET /dependencies/:missionId — get all dependencies for a mission */
missionDependencyGraph.get('/dependencies/:missionId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await svc.getDependencies(c.env.DB, tenantId, c.req.param('missionId'));
    return json(result);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** GET /graph/:rootMissionId — full DAG from root mission */
missionDependencyGraph.get('/graph/:rootMissionId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const graph = await svc.getGraph(c.env.DB, tenantId, c.req.param('rootMissionId'));
    return json(graph);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ── Execution group routes ───────────────────────────────────────────────────

/** GET /groups — list execution groups for tenant */
missionDependencyGraph.get('/groups', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    return json(await svc.listGroups(c.env.DB, tenantId));
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** POST /groups — create execution group; body: { name, missions_json?, execution_order? } */
missionDependencyGraph.post('/groups', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const name = String(body.name ?? '').trim();
  if (!name) return json({ error: 'name is required', code: 'INVALID_INPUT' }, { status: 400 });
  try {
    const group = await svc.createGroup(c.env.DB, tenantId, {
      name,
      missions_json: body.missions_json ? String(body.missions_json) : undefined,
      execution_order: body.execution_order ? String(body.execution_order) : undefined,
    });
    return json({ group }, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** PUT /groups/:id/status — update group status; body: { status } */
missionDependencyGraph.put('/groups/:id/status', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const status = String(body.status ?? '').trim();
  if (!status) return json({ error: 'status is required', code: 'INVALID_INPUT' }, { status: 400 });
  try {
    const group = await svc.updateGroupStatus(c.env.DB, tenantId, c.req.param('id'), status);
    if (!group) return json({ error: 'Group not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ group });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ── Critical path routes ─────────────────────────────────────────────────────

/** POST /analyze/:rootMissionId — run critical path analysis */
missionDependencyGraph.post('/analyze/:rootMissionId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const analysis = await svc.analyzeCriticalPath(c.env.DB, tenantId, c.req.param('rootMissionId'));
    return json({ analysis }, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** GET /analyses — list past critical path analyses for tenant */
missionDependencyGraph.get('/analyses', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    return json(await svc.getAnalyses(c.env.DB, tenantId));
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ── Admin route ──────────────────────────────────────────────────────────────

/** GET /admin/overview — cross-tenant stats; requires X-Admin-Key */
missionDependencyGraph.get('/admin/overview', async (c) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden' }, { status: 403 });
  }
  try {
    return json(await svc.getAdminOverview(c.env.DB));
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});
