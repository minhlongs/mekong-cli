/**
 * Pricing Plans routes — admin-managed plans + tenant subscriptions
 * Mount at: /v1/pricing
 *
 * Public:  GET /plans, GET /plans/:id
 * Admin:   POST /plans, PUT /plans/:id, DELETE /plans/:id, POST /plans/seed
 * Auth:    GET /subscription, POST /subscribe, POST /cancel, GET /check-access, GET /check-limit
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createPlan,
  getPlans,
  getPlan,
  updatePlan,
  deletePlan,
  subscribeTenant,
  getTenantSubscription,
  cancelSubscription,
  checkFeatureAccess,
  checkLimit,
  seedDefaultPlans,
} from '../services/pricing-plan-service';

export const pricingPlans = new Hono<{ Bindings: Env }>();

// Admin auth middleware
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  }
  await next();
};

// ── Public routes ──────────────────────────────────────────────────────────

/** GET /v1/pricing/plans — list active public plans */
pricingPlans.get('/plans', async (c) => {
  try {
    const plans = await getPlans(c.env.DB, true);
    return json({ plans });
  } catch (e) {
    return json({ error: 'Failed to fetch plans', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// Mount /plans/seed BEFORE /plans/:id to avoid route shadowing
/** POST /v1/pricing/plans/seed — seed default starter/pro/enterprise plans (admin) */
pricingPlans.post('/plans/seed', adminAuth(), async (c) => {
  try {
    const plans = await seedDefaultPlans(c.env.DB);
    return json({ seeded: plans.length, plans });
  } catch (e) {
    return json({ error: 'Failed to seed plans', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /v1/pricing/plans/:id — get plan details */
pricingPlans.get('/plans/:id', async (c) => {
  try {
    const plan = await getPlan(c.env.DB, c.req.param('id'));
    if (!plan || !plan.is_active) {
      return json({ error: 'Plan not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ plan });
  } catch (e) {
    return json({ error: 'Failed to fetch plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// ── Admin routes ───────────────────────────────────────────────────────────

/** POST /v1/pricing/plans — create a pricing plan */
pricingPlans.post('/plans', adminAuth(), async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    if (!body.name || !body.display_name || body.price_monthly === undefined) {
      return json({ error: 'name, display_name, price_monthly required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const plan = await createPlan(c.env.DB, {
      name: body.name,
      display_name: body.display_name,
      description: body.description ?? null,
      price_monthly: Number(body.price_monthly),
      price_yearly: body.price_yearly ? Number(body.price_yearly) : null,
      currency: body.currency ?? 'USD',
      features: body.features ?? {},
      limits: body.limits ?? { missions_per_month: 0, api_calls_per_day: 0, team_members: 1, storage_mb: 0 },
      is_active: body.is_active !== false,
      is_public: body.is_public !== false,
      sort_order: body.sort_order ?? 0,
    });
    return json({ plan }, { status: 201 });
  } catch (e: any) {
    if (e?.message?.includes('UNIQUE')) {
      return json({ error: 'Plan name already exists', code: 'CONFLICT' }, { status: 409 });
    }
    return json({ error: 'Failed to create plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** PUT /v1/pricing/plans/:id — update a pricing plan */
pricingPlans.put('/plans/:id', adminAuth(), async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const plan = await updatePlan(c.env.DB, c.req.param('id'), body);
    if (!plan) return json({ error: 'Plan not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ plan });
  } catch (e) {
    return json({ error: 'Failed to update plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** DELETE /v1/pricing/plans/:id — soft-delete (set is_active=false) */
pricingPlans.delete('/plans/:id', adminAuth(), async (c) => {
  try {
    const plan = await getPlan(c.env.DB, c.req.param('id'));
    if (!plan) return json({ error: 'Plan not found', code: 'NOT_FOUND' }, { status: 404 });
    await deletePlan(c.env.DB, c.req.param('id'));
    return json({ success: true });
  } catch (e) {
    return json({ error: 'Failed to delete plan', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// ── Auth routes ────────────────────────────────────────────────────────────

/** GET /v1/pricing/subscription — get my current subscription */
pricingPlans.get('/subscription', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const subscription = await getTenantSubscription(c.env.DB, tenantId);
    if (!subscription) return json({ subscription: null });
    return json({ subscription });
  } catch (e) {
    return json({ error: 'Failed to fetch subscription', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** POST /v1/pricing/subscribe — subscribe to a plan */
pricingPlans.post('/subscribe', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({}));
    if (!body.planId) {
      return json({ error: 'planId required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const plan = await getPlan(c.env.DB, body.planId);
    if (!plan || !plan.is_active) {
      return json({ error: 'Plan not found', code: 'NOT_FOUND' }, { status: 404 });
    }
    const billingCycle = body.billingCycle === 'yearly' ? 'yearly' : 'monthly';
    const subscription = await subscribeTenant(c.env.DB, tenantId, body.planId, billingCycle);
    return json({ subscription }, { status: 201 });
  } catch (e) {
    return json({ error: 'Failed to subscribe', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** POST /v1/pricing/cancel — cancel subscription at period end */
pricingPlans.post('/cancel', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const sub = await getTenantSubscription(c.env.DB, tenantId);
    if (!sub) return json({ error: 'No active subscription', code: 'NOT_FOUND' }, { status: 404 });
    await cancelSubscription(c.env.DB, tenantId);
    return json({ success: true, message: 'Subscription will cancel at period end' });
  } catch (e) {
    return json({ error: 'Failed to cancel subscription', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /v1/pricing/check-access?feature=advanced_analytics — check feature gate */
pricingPlans.get('/check-access', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const feature = c.req.query('feature');
    if (!feature) return json({ error: 'feature query param required', code: 'VALIDATION_ERROR' }, { status: 400 });
    const allowed = await checkFeatureAccess(c.env.DB, tenantId, feature);
    return json({ feature, allowed });
  } catch (e) {
    return json({ error: 'Failed to check access', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /v1/pricing/check-limit?limit=missions_per_month — get limit value */
pricingPlans.get('/check-limit', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limitKey = c.req.query('limit');
    if (!limitKey) return json({ error: 'limit query param required', code: 'VALIDATION_ERROR' }, { status: 400 });
    const { limit, unlimited } = await checkLimit(c.env.DB, tenantId, limitKey);
    return json({ limitKey, limit, unlimited });
  } catch (e) {
    return json({ error: 'Failed to check limit', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});
