/**
 * Rate Plan Management routes — plan CRUD + tenant assignment + effective limits
 * Mount at: /v1/rate-plans
 *
 * Public: GET /plans, GET /plans/:planId
 * Auth:   GET /my-plan, GET /my-limits
 * Admin:  POST /admin/plans, PUT /admin/plans/:planId, DELETE /admin/plans/:planId
 *         POST /admin/assign, DELETE /admin/assign/:tenantId, GET /admin/overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createPlan,
  listPlans,
  getPlan,
  updatePlan,
  deletePlan,
  assignPlanToTenant,
  getTenantPlan,
  removeTenantPlan,
  getEffectiveLimits,
  getAdminRatePlanOverview,
} from '../services/rate-plan-management-service';

export const ratePlanManagement = new Hono<{ Bindings: Env }>();

// ── Admin auth guard ────────────────────────────────────────────────────────

function requireAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }) {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) return true; // unauthorized
  return false;
}

// ── Public routes ───────────────────────────────────────────────────────────

/** GET /v1/rate-plans/plans — list all active rate plans */
ratePlanManagement.get('/plans', async (c) => {
  try {
    const plans = await listPlans(c.env.DB, true);
    return json({ plans });
  } catch {
    return json({ error: 'Failed to fetch plans', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /v1/rate-plans/plans/:planId — get a single rate plan */
ratePlanManagement.get('/plans/:planId', async (c) => {
  try {
    const plan = await getPlan(c.env.DB, c.req.param('planId'));
    if (!plan || !plan.isActive) {
      return json({ error: 'Rate plan not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ plan });
  } catch {
    return json({ error: 'Failed to fetch plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// ── Auth routes ─────────────────────────────────────────────────────────────

/** GET /v1/rate-plans/my-plan — get current tenant's assigned rate plan */
ratePlanManagement.get('/my-plan', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await getTenantPlan(c.env.DB, tenantId);
    if (!result) return json({ assignment: null, plan: null });
    return json({ assignment: result.assignment, plan: result.plan });
  } catch {
    return json({ error: 'Failed to fetch plan assignment', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /v1/rate-plans/my-limits — get effective rate limits for current tenant */
ratePlanManagement.get('/my-limits', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limits = await getEffectiveLimits(c.env.DB, tenantId);
    return json({ limits });
  } catch {
    return json({ error: 'Failed to fetch effective limits', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// ── Admin routes ────────────────────────────────────────────────────────────

/** POST /v1/rate-plans/admin/plans — create a new rate plan */
ratePlanManagement.post('/admin/plans', async (c) => {
  if (requireAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    if (!body.name || typeof body.name !== 'string') {
      return json({ error: 'name is required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const validTiers = ['starter', 'pro', 'enterprise', 'custom'];
    const tier = typeof body.tier === 'string' && validTiers.includes(body.tier) ? body.tier : 'custom';
    const plan = await createPlan(c.env.DB, {
      name: body.name,
      description: body.description as string | undefined,
      tier,
      requestsPerMinute: body.requestsPerMinute ? Number(body.requestsPerMinute) : undefined,
      requestsPerHour: body.requestsPerHour ? Number(body.requestsPerHour) : undefined,
      requestsPerDay: body.requestsPerDay ? Number(body.requestsPerDay) : undefined,
      burstLimit: body.burstLimit ? Number(body.burstLimit) : undefined,
      concurrentLimit: body.concurrentLimit ? Number(body.concurrentLimit) : undefined,
      isDefault: Boolean(body.isDefault),
      metadata: body.metadata as Record<string, unknown> | undefined,
    });
    return json({ plan }, { status: 201 });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '';
    if (msg.includes('UNIQUE')) {
      return json({ error: 'Plan name already exists', code: 'CONFLICT' }, { status: 409 });
    }
    return json({ error: 'Failed to create plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** PUT /v1/rate-plans/admin/plans/:planId — update a rate plan */
ratePlanManagement.put('/admin/plans/:planId', async (c) => {
  if (requireAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    const plan = await updatePlan(c.env.DB, c.req.param('planId'), {
      name: body.name as string | undefined,
      description: body.description as string | undefined,
      tier: body.tier as string | undefined,
      requestsPerMinute: body.requestsPerMinute !== undefined ? Number(body.requestsPerMinute) : undefined,
      requestsPerHour: body.requestsPerHour !== undefined ? Number(body.requestsPerHour) : undefined,
      requestsPerDay: body.requestsPerDay !== undefined ? Number(body.requestsPerDay) : undefined,
      burstLimit: body.burstLimit !== undefined ? Number(body.burstLimit) : undefined,
      concurrentLimit: body.concurrentLimit !== undefined ? Number(body.concurrentLimit) : undefined,
      isDefault: body.isDefault !== undefined ? Boolean(body.isDefault) : undefined,
      isActive: body.isActive !== undefined ? Boolean(body.isActive) : undefined,
      metadata: body.metadata as Record<string, unknown> | undefined,
    });
    if (!plan) return json({ error: 'Rate plan not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ plan });
  } catch {
    return json({ error: 'Failed to update plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** DELETE /v1/rate-plans/admin/plans/:planId — soft-delete a rate plan */
ratePlanManagement.delete('/admin/plans/:planId', async (c) => {
  if (requireAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const planId = c.req.param('planId');
    const existing = await getPlan(c.env.DB, planId);
    if (!existing) return json({ error: 'Rate plan not found', code: 'NOT_FOUND' }, { status: 404 });
    await deletePlan(c.env.DB, planId);
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to delete plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** POST /v1/rate-plans/admin/assign — assign a rate plan to a tenant */
ratePlanManagement.post('/admin/assign', async (c) => {
  if (requireAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
    if (!body.tenantId || !body.ratePlanId) {
      return json({ error: 'tenantId and ratePlanId are required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const plan = await getPlan(c.env.DB, String(body.ratePlanId));
    if (!plan || !plan.isActive) {
      return json({ error: 'Rate plan not found or inactive', code: 'NOT_FOUND' }, { status: 404 });
    }
    const assignment = await assignPlanToTenant(c.env.DB, {
      tenantId: String(body.tenantId),
      ratePlanId: String(body.ratePlanId),
      overrideRpm: body.overrideRpm !== undefined ? Number(body.overrideRpm) : undefined,
      overrideRph: body.overrideRph !== undefined ? Number(body.overrideRph) : undefined,
      overrideRpd: body.overrideRpd !== undefined ? Number(body.overrideRpd) : undefined,
      expiresAt: body.expiresAt as string | undefined,
      assignedBy: body.assignedBy as string | undefined,
    });
    return json({ assignment }, { status: 201 });
  } catch {
    return json({ error: 'Failed to assign plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** DELETE /v1/rate-plans/admin/assign/:tenantId — remove a tenant's rate plan assignment */
ratePlanManagement.delete('/admin/assign/:tenantId', async (c) => {
  if (requireAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const removed = await removeTenantPlan(c.env.DB, c.req.param('tenantId'));
    if (!removed) return json({ error: 'No assignment found for tenant', code: 'NOT_FOUND' }, { status: 404 });
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to remove assignment', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /v1/rate-plans/admin/overview — admin stats across all plans and assignments */
ratePlanManagement.get('/admin/overview', async (c) => {
  if (requireAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const overview = await getAdminRatePlanOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch overview', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});
