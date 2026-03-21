/**
 * Pricing Plan Service — admin-defined plans with feature gates
 * Manages pricing_plans and plan_subscriptions tables
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface PricingPlan {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  price_monthly: number;
  price_yearly: number | null;
  currency: string;
  features: Record<string, boolean>;
  limits: PlanLimits;
  is_active: boolean;
  is_public: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface PlanLimits {
  missions_per_month: number;
  api_calls_per_day: number;
  team_members: number;
  storage_mb: number;
}

export interface PlanSubscription {
  id: string;
  tenant_id: string;
  plan_id: string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing';
  billing_cycle: 'monthly' | 'yearly';
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  created_at: string;
  updated_at: string;
  plan?: PricingPlan;
}

// Default plans seeded on first run
const DEFAULT_PLANS = [
  {
    name: 'starter',
    display_name: 'Starter',
    description: 'Perfect for individuals and small teams',
    price_monthly: 49,
    price_yearly: 470,
    features: { advanced_analytics: false, custom_branding: false, priority_support: false, sso: false, audit_logs: false },
    limits: { missions_per_month: 200, api_calls_per_day: 10000, team_members: 3, storage_mb: 1024 },
    sort_order: 1,
  },
  {
    name: 'pro',
    display_name: 'Pro',
    description: 'For growing teams that need more power',
    price_monthly: 149,
    price_yearly: 1430,
    features: { advanced_analytics: true, custom_branding: true, priority_support: false, sso: false, audit_logs: true },
    limits: { missions_per_month: 1000, api_calls_per_day: 100000, team_members: 10, storage_mb: 10240 },
    sort_order: 2,
  },
  {
    name: 'enterprise',
    display_name: 'Enterprise',
    description: 'Unlimited scale for large organizations',
    price_monthly: 499,
    price_yearly: 4790,
    features: { advanced_analytics: true, custom_branding: true, priority_support: true, sso: true, audit_logs: true },
    limits: { missions_per_month: -1, api_calls_per_day: -1, team_members: -1, storage_mb: 102400 },
    sort_order: 3,
  },
];

function parsePlan(row: any): PricingPlan {
  return {
    ...row,
    features: typeof row.features === 'string' ? JSON.parse(row.features) : row.features,
    limits: typeof row.limits === 'string' ? JSON.parse(row.limits) : row.limits,
    is_active: Boolean(row.is_active),
    is_public: Boolean(row.is_public),
  };
}

export async function createPlan(db: D1Database, input: Omit<PricingPlan, 'id' | 'created_at' | 'updated_at'>): Promise<PricingPlan> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO pricing_plans (id, name, display_name, description, price_monthly, price_yearly, currency, features, limits, is_active, is_public, sort_order, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))`
  ).bind(
    id, input.name, input.display_name, input.description ?? null,
    input.price_monthly, input.price_yearly ?? null, input.currency ?? 'USD',
    JSON.stringify(input.features), JSON.stringify(input.limits),
    input.is_active ? 1 : 0, input.is_public ? 1 : 0, input.sort_order ?? 0
  ).run();
  return getPlan(db, id) as Promise<PricingPlan>;
}

export async function getPlans(db: D1Database, publicOnly = true): Promise<PricingPlan[]> {
  const query = publicOnly
    ? `SELECT * FROM pricing_plans WHERE is_active=1 AND is_public=1 ORDER BY sort_order ASC`
    : `SELECT * FROM pricing_plans ORDER BY sort_order ASC`;
  const { results } = await db.prepare(query).all();
  return results.map(parsePlan);
}

export async function getPlan(db: D1Database, planId: string): Promise<PricingPlan | null> {
  const row = await db.prepare('SELECT * FROM pricing_plans WHERE id=?').bind(planId).first();
  return row ? parsePlan(row) : null;
}

export async function updatePlan(db: D1Database, planId: string, input: Partial<Omit<PricingPlan, 'id' | 'created_at' | 'updated_at'>>): Promise<PricingPlan | null> {
  const sets: string[] = [];
  const vals: any[] = [];
  if (input.name !== undefined) { sets.push('name=?'); vals.push(input.name); }
  if (input.display_name !== undefined) { sets.push('display_name=?'); vals.push(input.display_name); }
  if (input.description !== undefined) { sets.push('description=?'); vals.push(input.description); }
  if (input.price_monthly !== undefined) { sets.push('price_monthly=?'); vals.push(input.price_monthly); }
  if (input.price_yearly !== undefined) { sets.push('price_yearly=?'); vals.push(input.price_yearly); }
  if (input.currency !== undefined) { sets.push('currency=?'); vals.push(input.currency); }
  if (input.features !== undefined) { sets.push('features=?'); vals.push(JSON.stringify(input.features)); }
  if (input.limits !== undefined) { sets.push('limits=?'); vals.push(JSON.stringify(input.limits)); }
  if (input.is_active !== undefined) { sets.push('is_active=?'); vals.push(input.is_active ? 1 : 0); }
  if (input.is_public !== undefined) { sets.push('is_public=?'); vals.push(input.is_public ? 1 : 0); }
  if (input.sort_order !== undefined) { sets.push('sort_order=?'); vals.push(input.sort_order); }
  if (!sets.length) return getPlan(db, planId);
  sets.push("updated_at=datetime('now')");
  await db.prepare(`UPDATE pricing_plans SET ${sets.join(',')} WHERE id=?`).bind(...vals, planId).run();
  return getPlan(db, planId);
}

export async function deletePlan(db: D1Database, planId: string): Promise<void> {
  await db.prepare(`UPDATE pricing_plans SET is_active=0, updated_at=datetime('now') WHERE id=?`).bind(planId).run();
}

export async function subscribeTenant(db: D1Database, tenantId: string, planId: string, billingCycle: 'monthly' | 'yearly' = 'monthly'): Promise<PlanSubscription> {
  const existing = await db.prepare('SELECT id FROM plan_subscriptions WHERE tenant_id=?').bind(tenantId).first<{ id: string }>();
  const now = new Date();
  const periodEnd = new Date(now);
  billingCycle === 'yearly' ? periodEnd.setFullYear(periodEnd.getFullYear() + 1) : periodEnd.setMonth(periodEnd.getMonth() + 1);

  if (existing) {
    await db.prepare(
      `UPDATE plan_subscriptions SET plan_id=?, billing_cycle=?, status='active', current_period_start=?, current_period_end=?, cancel_at_period_end=0, updated_at=datetime('now') WHERE tenant_id=?`
    ).bind(planId, billingCycle, now.toISOString(), periodEnd.toISOString(), tenantId).run();
  } else {
    await db.prepare(
      `INSERT INTO plan_subscriptions (id, tenant_id, plan_id, status, billing_cycle, current_period_start, current_period_end, cancel_at_period_end, created_at, updated_at)
       VALUES (?, ?, ?, 'active', ?, ?, ?, 0, datetime('now'), datetime('now'))`
    ).bind(crypto.randomUUID(), tenantId, planId, billingCycle, now.toISOString(), periodEnd.toISOString()).run();
  }
  return getTenantSubscription(db, tenantId) as Promise<PlanSubscription>;
}

export async function getTenantSubscription(db: D1Database, tenantId: string): Promise<PlanSubscription | null> {
  const row = await db.prepare(
    `SELECT s.*, p.name as plan_name, p.display_name, p.price_monthly, p.price_yearly, p.currency, p.features, p.limits, p.sort_order
     FROM plan_subscriptions s JOIN pricing_plans p ON s.plan_id=p.id WHERE s.tenant_id=?`
  ).bind(tenantId).first<any>();
  if (!row) return null;
  const { plan_name, display_name, price_monthly, price_yearly, currency, features, limits, sort_order, ...sub } = row;
  return {
    ...sub,
    cancel_at_period_end: Boolean(sub.cancel_at_period_end),
    plan: parsePlan({ id: sub.plan_id, name: plan_name, display_name, price_monthly, price_yearly, currency, features, limits, sort_order, is_active: true, is_public: true }),
  };
}

export async function cancelSubscription(db: D1Database, tenantId: string): Promise<void> {
  await db.prepare(`UPDATE plan_subscriptions SET cancel_at_period_end=1, updated_at=datetime('now') WHERE tenant_id=?`).bind(tenantId).run();
}

export async function checkFeatureAccess(db: D1Database, tenantId: string, featureKey: string): Promise<boolean> {
  const sub = await getTenantSubscription(db, tenantId);
  if (!sub?.plan) return false;
  return Boolean(sub.plan.features[featureKey]);
}

export async function checkLimit(db: D1Database, tenantId: string, limitKey: string): Promise<{ limit: number; unlimited: boolean }> {
  const sub = await getTenantSubscription(db, tenantId);
  const limit = sub?.plan?.limits?.[limitKey as keyof PlanLimits] ?? 0;
  return { limit, unlimited: limit === -1 };
}

export async function seedDefaultPlans(db: D1Database): Promise<PricingPlan[]> {
  const results: PricingPlan[] = [];
  for (const plan of DEFAULT_PLANS) {
    const existing = await db.prepare('SELECT id FROM pricing_plans WHERE name=?').bind(plan.name).first<{ id: string }>();
    if (!existing) {
      const created = await createPlan(db, { ...plan, currency: 'USD', is_active: true, is_public: true });
      results.push(created);
    } else {
      const p = await getPlan(db, existing.id);
      if (p) results.push(p);
    }
  }
  return results;
}
