/**
 * Mission Dependencies routes — DAG-based mission chain API
 * Auth:  GET/POST /chains, GET /chains/:id, POST /chains/:id/missions,
 *        DELETE /chains/:id/missions/:depId, POST /chains/:id/start,
 *        POST /chains/:id/missions/:missionId/complete|fail, GET /chains/:id/ready
 * Admin: GET /admin/overview (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createChain, listChains, getChain,
  addDependency, removeDependency,
  startChain, completeMission, failMission,
  getReadyMissions, getAdminChainOverview,
} from '../services/mission-dependencies-service';

export const missionDependencies = new Hono<{ Bindings: Env }>();

// ── Auth routes ─────────────────────────────────────────────────────────────

/** GET /chains — list tenant chains; query: status */
missionDependencies.get('/chains', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const chains = await listChains(c.env.DB, tenantId, c.req.query('status'));
    return json({ chains, total: chains.length });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** POST /chains — create chain; body: { name, description? } */
missionDependencies.post('/chains', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const name = String(body.name ?? '').trim();
  if (!name) return json({ error: 'name is required', code: 'INVALID_INPUT' }, { status: 400 });
  try {
    const chain = await createChain(
      c.env.DB, tenantId, name,
      body.description ? String(body.description) : undefined
    );
    return json({ chain }, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** GET /chains/:chainId — get chain with DAG nodes */
missionDependencies.get('/chains/:chainId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await getChain(c.env.DB, c.req.param('chainId'), tenantId);
    if (!result) return json({ error: 'Chain not found', code: 'NOT_FOUND' }, { status: 404 });
    return json(result);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** POST /chains/:chainId/missions — add mission node; body: { mission_id, depends_on?, config? } */
missionDependencies.post('/chains/:chainId/missions', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const chainId = c.req.param('chainId');
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const missionId = String(body.mission_id ?? '').trim();
  if (!missionId) return json({ error: 'mission_id is required', code: 'INVALID_INPUT' }, { status: 400 });
  try {
    const dep = await addDependency(
      c.env.DB, chainId, tenantId, missionId,
      body.depends_on ? String(body.depends_on) : undefined,
      body.config as Record<string, unknown> | undefined,
    );
    return json({ dependency: dep }, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** DELETE /chains/:chainId/missions/:depId — remove dependency node */
missionDependencies.delete('/chains/:chainId/missions/:depId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const removed = await removeDependency(c.env.DB, c.req.param('depId'), tenantId);
    if (!removed) return json({ error: 'Dependency not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ success: true });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** POST /chains/:chainId/start — activate chain, mark root nodes ready */
missionDependencies.post('/chains/:chainId/start', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const chain = await startChain(c.env.DB, c.req.param('chainId'), tenantId);
    if (!chain) return json({ error: 'Chain not found or not in draft status', code: 'INVALID_STATE' }, { status: 400 });
    return json({ chain });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** POST /chains/:chainId/missions/:missionId/complete — mark mission done; body: { result? } */
missionDependencies.post('/chains/:chainId/missions/:missionId/complete', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  try {
    const result = await completeMission(
      c.env.DB, c.req.param('chainId'), c.req.param('missionId'),
      tenantId, (body.result as Record<string, unknown>) ?? {}
    );
    return json(result);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** POST /chains/:chainId/missions/:missionId/fail — mark mission failed; body: { error? } */
missionDependencies.post('/chains/:chainId/missions/:missionId/fail', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  try {
    const chain = await failMission(
      c.env.DB, c.req.param('chainId'), c.req.param('missionId'),
      tenantId, String(body.error ?? 'Mission failed')
    );
    if (!chain) return json({ error: 'Chain or mission not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ chain });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

/** GET /chains/:chainId/ready — get missions with all dependencies satisfied */
missionDependencies.get('/chains/:chainId/ready', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const missions = await getReadyMissions(c.env.DB, c.req.param('chainId'), tenantId);
    return json({ missions, total: missions.length });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ── Admin routes ────────────────────────────────────────────────────────────

/** GET /admin/overview — platform-wide chain stats (X-Admin-Key required) */
missionDependencies.get('/admin/overview', async (c) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 401 });
  }
  try {
    const overview = await getAdminChainOverview(c.env.DB);
    return json(overview);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});
