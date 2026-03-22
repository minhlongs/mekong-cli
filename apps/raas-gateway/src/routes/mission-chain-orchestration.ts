/**
 * Mission Chain Orchestration routes — manage chains and runs per tenant
 * Auth endpoints require JWT/API-key. Admin endpoint requires X-Admin-Key.
 * Mount path: /v1/mission-chains
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionChainOrchestrationService as svc } from '../services/mission-chain-orchestration-service';

const app = new Hono<{ Bindings: Env }>();

// GET /chains — list all chains for tenant
app.get('/chains', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listChains(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /chains — create a new mission chain
app.post('/chains', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ chain_name: string; steps?: unknown[]; max_retries?: number }>();
    if (!body.chain_name) return c.json({ error: 'chain_name is required' }, 400);
    const chain = await svc.createChain(c.env.DB, tenantId, body.chain_name, {
      stepsJson:  body.steps ? JSON.stringify(body.steps) : undefined,
      maxRetries: body.max_retries,
    });
    return c.json({ success: true, data: chain }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /runs — list runs for tenant (?chain_id= &limit=)
app.get('/runs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const chainId = c.req.query('chain_id');
    const limit   = parseInt(c.req.query('limit') ?? '50', 10);
    const data    = await svc.getRuns(c.env.DB, tenantId, chainId, limit);
    return c.json({ success: true, data, count: data.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — platform-wide chain + run stats (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as missionChainOrchestration };
