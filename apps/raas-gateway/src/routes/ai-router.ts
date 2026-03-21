/**
 * AI Router routes — model selection and usage stats endpoints
 * All routes require authentication via auth() middleware
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  selectModelForMission,
  trackModelUsage,
  getModelStats,
  getModelRecommendation,
} from '../services/ai-mission-router';
import type { MissionInput } from '../services/ai-mission-router';

const aiRouter = new Hono<{ Bindings: Env }>();

// Apply auth to all routes
aiRouter.use('*', auth());

/** GET / — personalized model recommendation for current tenant */
aiRouter.get('/', async (c) => {
  const tenant = getTenant(c);
  const recommendation = await getModelRecommendation(tenant.tenantId, c.env.DB);
  return json({
    recommendation,
    tenantId: tenant.tenantId,
  });
});

/** POST /select — select optimal model for a mission */
aiRouter.post('/select', async (c) => {
  let body: MissionInput;
  try {
    body = await c.req.json<MissionInput>();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { goal, complexity, capabilities, budget } = body;

  if (!goal || !complexity) {
    return json({ error: 'goal and complexity are required' }, { status: 400 });
  }

  const validComplexity = ['simple', 'standard', 'complex'];
  if (!validComplexity.includes(complexity)) {
    return json({ error: `complexity must be one of: ${validComplexity.join(', ')}` }, { status: 400 });
  }

  try {
    const model = selectModelForMission({ goal, complexity, capabilities, budget });
    return json({ model, selected: true });
  } catch (err: any) {
    return json({ error: err.message ?? 'Model selection failed' }, { status: 503 });
  }
});

/** GET /stats — aggregated model usage statistics */
aiRouter.get('/stats', async (c) => {
  const daysParam = c.req.query('days');
  const days = daysParam ? Math.min(Math.max(parseInt(daysParam, 10) || 30, 1), 365) : 30;

  const stats = await getModelStats(c.env.DB, days);
  return json({ stats, days });
});

/** GET /usage — tenant's personal model usage history */
aiRouter.get('/usage', async (c) => {
  const tenant = getTenant(c);
  const daysParam = c.req.query('days');
  const days = daysParam ? Math.min(Math.max(parseInt(daysParam, 10) || 30, 1), 365) : 30;

  try {
    const since = new Date(Date.now() - days * 86_400_000).toISOString();
    const result = await c.env.DB
      .prepare(
        `SELECT model_id, provider, tokens_used, latency_ms, cost_estimate, status, created_at
         FROM mission_model_usage
         WHERE tenant_id = ? AND created_at >= ?
         ORDER BY created_at DESC
         LIMIT 100`
      )
      .bind(tenant.tenantId, since)
      .all();

    return json({ usage: result.results ?? [], days });
  } catch (err: any) {
    return json({ error: 'Failed to fetch usage history', usage: [] }, { status: 500 });
  }
});

export { aiRouter };
