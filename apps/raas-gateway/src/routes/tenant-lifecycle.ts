/**
 * Tenant Lifecycle routes — stage management and admin controls
 * Auth routes: GET /stage, /history, /risk (tenant-scoped)
 * Admin routes: GET+POST /admin/* (X-Admin-Key protected)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  initLifecycle,
  getLifecycleStage,
  transitionStage,
  calculateRiskScore,
  getTransitionHistory,
  reactivateTenant,
} from '../services/tenant-lifecycle-service';
import {
  getAtRiskTenants,
  getStageDistribution,
  getChurnAnalysis,
  evaluateAutoTransitions,
} from '../services/tenant-lifecycle-analytics-service';

const app = new Hono<{ Bindings: Env }>();

// ─── Admin auth middleware ────────────────────────────────────────────────────

function adminAuth() {
  return async (c: any, next: () => Promise<void>) => {
    const key = c.req.header('X-Admin-Key');
    if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
      return json({ error: 'Unauthorized' }, { status: 401 });
    }
    await next();
  };
}

// ─── Tenant-scoped routes (require auth) ─────────────────────────────────────

/** GET /v1/lifecycle/stage — current stage + health indicators */
app.get('/stage', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const record = await getLifecycleStage(c.env.DB, tenant.tenantId);
    if (!record) return json({ error: 'Lifecycle not initialized' }, { status: 404 });
    return json({ stage: record.stage, riskScore: record.risk_score, record });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** GET /v1/lifecycle/history — transition history for current tenant */
app.get('/history', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const history = await getTransitionHistory(c.env.DB, tenant.tenantId);
    return json({ transitions: history, total: history.length });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** GET /v1/lifecycle/risk — risk score for current tenant */
app.get('/risk', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const score = await calculateRiskScore(c.env.DB, tenant.tenantId);
    return json({ tenantId: tenant.tenantId, riskScore: score });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

// ─── Admin routes ─────────────────────────────────────────────────────────────

/** GET /v1/lifecycle/admin/at-risk — tenants above risk threshold */
app.get('/admin/at-risk', adminAuth(), async (c) => {
  try {
    const threshold = Number(c.req.query('threshold') ?? 70);
    const tenants = await getAtRiskTenants(c.env.DB, threshold);
    return json({ tenants, total: tenants.length, threshold });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** GET /v1/lifecycle/admin/distribution — count per stage */
app.get('/admin/distribution', adminAuth(), async (c) => {
  try {
    const distribution = await getStageDistribution(c.env.DB);
    return json({ distribution });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** GET /v1/lifecycle/admin/churn — recently churned tenants */
app.get('/admin/churn', adminAuth(), async (c) => {
  try {
    const days = Number(c.req.query('days') ?? 30);
    const analysis = await getChurnAnalysis(c.env.DB, days);
    return json({ churned: analysis, total: analysis.length, days });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** POST /v1/lifecycle/admin/transition — manually transition a tenant */
app.post('/admin/transition', adminAuth(), async (c) => {
  try {
    const body = await c.req.json<{ tenantId: string; stage: string; reason?: string }>();
    if (!body.tenantId || !body.stage) {
      return json({ error: 'tenantId and stage are required' }, { status: 400 });
    }
    await transitionStage(c.env.DB, body.tenantId, body.stage as any, body.reason ?? 'Manual admin transition', 'admin');
    return json({ success: true, tenantId: body.tenantId, newStage: body.stage });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** POST /v1/lifecycle/admin/evaluate — run auto-transition evaluation */
app.post('/admin/evaluate', adminAuth(), async (c) => {
  try {
    const transitioned = await evaluateAutoTransitions(c.env.DB);
    return json({ success: true, transitioned });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** POST /v1/lifecycle/admin/reactivate — reactivate a churned tenant */
app.post('/admin/reactivate', adminAuth(), async (c) => {
  try {
    const body = await c.req.json<{ tenantId: string; reason?: string }>();
    if (!body.tenantId) return json({ error: 'tenantId is required' }, { status: 400 });
    await reactivateTenant(c.env.DB, body.tenantId, body.reason ?? 'Admin reactivation');
    return json({ success: true, tenantId: body.tenantId, newStage: 'reactivated' });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** POST /v1/lifecycle/admin/init/:tenantId — initialize lifecycle for a tenant */
app.post('/admin/init/:tenantId', adminAuth(), async (c) => {
  try {
    const tenantId = c.req.param('tenantId');
    const body = await c.req.json<{ trialDays?: number }>().catch(() => ({} as { trialDays?: number }));
    const record = await initLifecycle(c.env.DB, tenantId, body.trialDays);
    return json({ success: true, record }, { status: 201 });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

export { app as tenantLifecycle };
