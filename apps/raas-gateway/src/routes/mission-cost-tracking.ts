/**
 * Mission Cost Tracking routes — per-mission LLM cost recording and budget management
 * Exposes tenant-scoped cost queries and admin cross-tenant overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { auth, getTenant } from '../middleware/auth';
import { MissionCostTrackingService } from '../services/mission-cost-tracking-service';

export const missionCostTracking = new Hono<{ Bindings: Env }>();

// All tenant routes require auth
missionCostTracking.use('/costs/*', auth());
missionCostTracking.use('/budget*', auth());
missionCostTracking.use('/summary', auth());

// ---------------------------------------------------------------------------
// Cost queries (tenant-scoped)
// ---------------------------------------------------------------------------

/**
 * GET /costs — cost breakdown for tenant over ?days (default 30)
 */
missionCostTracking.get('/costs', async (c) => {
  try {
    const tenant = getTenant(c);
    const days = Math.min(Number(c.req.query('days') ?? 30), 365);
    const svc = new MissionCostTrackingService(c.env);
    const breakdown = await svc.getCostBreakdown(tenant.tenantId, days);
    return json({ costs: breakdown, days });
  } catch (err) {
    return json({ error: 'Failed to fetch cost breakdown' }, { status: 500 });
  }
});

/**
 * GET /costs/by-model — cost aggregated by model over ?days
 */
missionCostTracking.get('/costs/by-model', async (c) => {
  try {
    const tenant = getTenant(c);
    const days = Math.min(Number(c.req.query('days') ?? 30), 365);
    const svc = new MissionCostTrackingService(c.env);
    const byModel = await svc.getCostByModel(tenant.tenantId, days);
    return json({ models: byModel, days });
  } catch (err) {
    return json({ error: 'Failed to fetch cost by model' }, { status: 500 });
  }
});

/**
 * GET /costs/by-day — daily cost totals over ?days
 */
missionCostTracking.get('/costs/by-day', async (c) => {
  try {
    const tenant = getTenant(c);
    const days = Math.min(Number(c.req.query('days') ?? 30), 365);
    const svc = new MissionCostTrackingService(c.env);
    const byDay = await svc.getCostByDay(tenant.tenantId, days);
    return json({ days: byDay, period: days });
  } catch (err) {
    return json({ error: 'Failed to fetch daily costs' }, { status: 500 });
  }
});

/**
 * GET /costs/:missionId — single mission cost record
 */
missionCostTracking.get('/costs/:missionId', async (c) => {
  try {
    const tenant = getTenant(c);
    const missionId = c.req.param('missionId');
    const svc = new MissionCostTrackingService(c.env);
    const cost = await svc.getMissionCost(missionId, tenant.tenantId);
    if (!cost) return json({ error: 'Mission cost not found' }, { status: 404 });
    return json({ cost });
  } catch (err) {
    return json({ error: 'Failed to fetch mission cost' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Budget management (tenant-scoped)
// ---------------------------------------------------------------------------

/**
 * GET /budget — get current budget config and spend status
 */
missionCostTracking.get('/budget', async (c) => {
  try {
    const tenant = getTenant(c);
    const svc = new MissionCostTrackingService(c.env);
    const budget = await svc.getBudget(tenant.tenantId);
    if (!budget) return json({ budget: null, message: 'No budget configured' });
    return json({ budget });
  } catch (err) {
    return json({ error: 'Failed to fetch budget' }, { status: 500 });
  }
});

/**
 * PUT /budget — set or update budget configuration
 * Body: { monthlyBudgetUsd?, dailyBudgetUsd?, alertThresholdPct?, isHardLimit? }
 */
missionCostTracking.put('/budget', async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{
      monthlyBudgetUsd?: number;
      dailyBudgetUsd?: number;
      alertThresholdPct?: number;
      isHardLimit?: number;
    }>();
    const svc = new MissionCostTrackingService(c.env);
    await svc.setBudget(tenant.tenantId, body);
    const budget = await svc.getBudget(tenant.tenantId);
    return json({ budget, message: 'Budget updated' });
  } catch (err) {
    return json({ error: 'Failed to update budget' }, { status: 500 });
  }
});

/**
 * POST /budget/check — pre-flight budget check before starting a mission
 * Body: { estimatedCostUsd: number }
 */
missionCostTracking.post('/budget/check', async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ estimatedCostUsd?: number }>();
    const estimatedCost = body.estimatedCostUsd ?? 0;
    const svc = new MissionCostTrackingService(c.env);
    const result = await svc.checkBudget(tenant.tenantId, estimatedCost);
    return json(result, { status: result.allowed ? 200 : 402 });
  } catch (err) {
    return json({ error: 'Failed to check budget' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Summary (tenant-scoped)
// ---------------------------------------------------------------------------

/**
 * GET /summary — today / this-month / all-time cost summary
 */
missionCostTracking.get('/summary', async (c) => {
  try {
    const tenant = getTenant(c);
    const svc = new MissionCostTrackingService(c.env);
    const summary = await svc.getCostSummary(tenant.tenantId);
    return json({ summary });
  } catch (err) {
    return json({ error: 'Failed to fetch cost summary' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin overview (X-Admin-Key protected)
// ---------------------------------------------------------------------------

/**
 * GET /admin/overview — cross-tenant cost overview, top 100 tenants by spend
 */
missionCostTracking.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return json({ error: 'Unauthorized' }, { status: 401 });
    }
    const svc = new MissionCostTrackingService(c.env);
    const overview = await svc.getAdminCostOverview();
    return json({ tenants: overview, count: overview.length });
  } catch (err) {
    return json({ error: 'Failed to fetch admin overview' }, { status: 500 });
  }
});
