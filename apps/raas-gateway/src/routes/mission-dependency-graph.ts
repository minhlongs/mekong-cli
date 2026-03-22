/**
 * Mission Dependency Graph routes
 * GET  /dependencies      — list dependencies for tenant
 * POST /dependencies      — create dependency
 * GET  /runs              — list execution runs for tenant
 * GET  /admin/overview    — admin cross-tenant stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionDependencyGraphService as svc } from '../services/mission-dependency-graph';

const app = new Hono<{
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
}>();

/** GET /dependencies — list tenant dependencies */
app.get('/dependencies', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await svc.listDependencies(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

/** POST /dependencies — create dependency; body: { mission_id, depends_on_mission_id, dependency_type? } */
app.post('/dependencies', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    const mission_id = String(body.mission_id ?? '').trim();
    const depends_on_mission_id = String(body.depends_on_mission_id ?? '').trim();
    if (!mission_id || !depends_on_mission_id) {
      return c.json({ error: 'mission_id and depends_on_mission_id are required' }, 400);
    }
    const result = await svc.createDependency(c.env.DB, tenantId, {
      mission_id,
      depends_on_mission_id,
      dependency_type: body.dependency_type ? String(body.dependency_type) : undefined,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

/** GET /runs — list dependency runs for tenant */
app.get('/runs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await svc.getRuns(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

/** GET /admin/overview — cross-tenant stats; requires X-Admin-Key header */
app.get('/admin/overview', async (c) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as missionDependencyGraph };
