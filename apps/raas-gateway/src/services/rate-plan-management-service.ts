/**
 * Rate Plan Management Service — CRUD for rate plans + tenant assignments
 * Handles plan lifecycle, tenant assignment, effective limit resolution
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface RatePlan {
  id: string;
  name: string;
  description: string | null;
  tier: string;
  requestsPerMinute: number;
  requestsPerHour: number;
  requestsPerDay: number;
  burstLimit: number;
  concurrentLimit: number;
  isDefault: boolean;
  isActive: boolean;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface TenantAssignment {
  id: string;
  tenantId: string;
  ratePlanId: string;
  overrideRpm: number | null;
  overrideRph: number | null;
  overrideRpd: number | null;
  assignedAt: string;
  expiresAt: string | null;
  assignedBy: string | null;
}

export interface EffectiveLimits {
  tenantId: string;
  ratePlanId: string | null;
  planName: string | null;
  requestsPerMinute: number;
  requestsPerHour: number;
  requestsPerDay: number;
  burstLimit: number;
  concurrentLimit: number;
  hasOverrides: boolean;
}

type PlanRow = {
  id: string; name: string; description: string | null; tier: string;
  requests_per_minute: number; requests_per_hour: number; requests_per_day: number;
  burst_limit: number; concurrent_limit: number; is_default: number; is_active: number;
  metadata: string; created_at: string; updated_at: string;
};

type AssignmentRow = {
  id: string; tenant_id: string; rate_plan_id: string;
  override_rpm: number | null; override_rph: number | null; override_rpd: number | null;
  assigned_at: string; expires_at: string | null; assigned_by: string | null;
};

function mapPlan(row: PlanRow): RatePlan {
  return {
    id: row.id, name: row.name, description: row.description, tier: row.tier,
    requestsPerMinute: row.requests_per_minute, requestsPerHour: row.requests_per_hour,
    requestsPerDay: row.requests_per_day, burstLimit: row.burst_limit,
    concurrentLimit: row.concurrent_limit, isDefault: row.is_default === 1,
    isActive: row.is_active === 1,
    metadata: row.metadata ? JSON.parse(row.metadata) as Record<string, unknown> : {},
    createdAt: row.created_at, updatedAt: row.updated_at,
  };
}

function mapAssignment(row: AssignmentRow): TenantAssignment {
  return {
    id: row.id, tenantId: row.tenant_id, ratePlanId: row.rate_plan_id,
    overrideRpm: row.override_rpm, overrideRph: row.override_rph,
    overrideRpd: row.override_rpd, assignedAt: row.assigned_at,
    expiresAt: row.expires_at, assignedBy: row.assigned_by,
  };
}

/** Create a new rate plan */
export async function createPlan(db: D1Database, input: {
  name: string; description?: string; tier?: string;
  requestsPerMinute?: number; requestsPerHour?: number; requestsPerDay?: number;
  burstLimit?: number; concurrentLimit?: number; isDefault?: boolean; metadata?: Record<string, unknown>;
}): Promise<RatePlan> {
  const row = await db.prepare(`
    INSERT INTO rate_plans (name, description, tier, requests_per_minute, requests_per_hour,
      requests_per_day, burst_limit, concurrent_limit, is_default, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    RETURNING *
  `).bind(
    input.name, input.description ?? null, input.tier ?? 'custom',
    input.requestsPerMinute ?? 60, input.requestsPerHour ?? 1000,
    input.requestsPerDay ?? 10000, input.burstLimit ?? 100, input.concurrentLimit ?? 10,
    input.isDefault ? 1 : 0, JSON.stringify(input.metadata ?? {}),
  ).first<PlanRow>();
  return mapPlan(row!);
}

/** List all rate plans (optionally filter by active only) */
export async function listPlans(db: D1Database, activeOnly = false): Promise<RatePlan[]> {
  const sql = activeOnly
    ? 'SELECT * FROM rate_plans WHERE is_active = 1 ORDER BY tier, name'
    : 'SELECT * FROM rate_plans ORDER BY tier, name';
  const { results } = await db.prepare(sql).all<PlanRow>();
  return results.map(mapPlan);
}

/** Get a single rate plan by ID */
export async function getPlan(db: D1Database, planId: string): Promise<RatePlan | null> {
  const row = await db.prepare('SELECT * FROM rate_plans WHERE id = ?').bind(planId).first<PlanRow>();
  return row ? mapPlan(row) : null;
}

/** Update rate plan fields (partial update) */
export async function updatePlan(db: D1Database, planId: string, updates: Partial<{
  name: string; description: string; tier: string;
  requestsPerMinute: number; requestsPerHour: number; requestsPerDay: number;
  burstLimit: number; concurrentLimit: number; isDefault: boolean; isActive: boolean;
  metadata: Record<string, unknown>;
}>): Promise<RatePlan | null> {
  const sets: string[] = ['updated_at = datetime(\'now\')'];
  const vals: unknown[] = [];
  if (updates.name !== undefined)             { sets.push('name = ?');                vals.push(updates.name); }
  if (updates.description !== undefined)      { sets.push('description = ?');         vals.push(updates.description); }
  if (updates.tier !== undefined)             { sets.push('tier = ?');                vals.push(updates.tier); }
  if (updates.requestsPerMinute !== undefined){ sets.push('requests_per_minute = ?'); vals.push(updates.requestsPerMinute); }
  if (updates.requestsPerHour !== undefined)  { sets.push('requests_per_hour = ?');   vals.push(updates.requestsPerHour); }
  if (updates.requestsPerDay !== undefined)   { sets.push('requests_per_day = ?');    vals.push(updates.requestsPerDay); }
  if (updates.burstLimit !== undefined)       { sets.push('burst_limit = ?');         vals.push(updates.burstLimit); }
  if (updates.concurrentLimit !== undefined)  { sets.push('concurrent_limit = ?');    vals.push(updates.concurrentLimit); }
  if (updates.isDefault !== undefined)        { sets.push('is_default = ?');          vals.push(updates.isDefault ? 1 : 0); }
  if (updates.isActive !== undefined)         { sets.push('is_active = ?');           vals.push(updates.isActive ? 1 : 0); }
  if (updates.metadata !== undefined)         { sets.push('metadata = ?');            vals.push(JSON.stringify(updates.metadata)); }

  if (sets.length === 1) return getPlan(db, planId);
  vals.push(planId);
  const row = await db.prepare(`UPDATE rate_plans SET ${sets.join(', ')} WHERE id = ? RETURNING *`)
    .bind(...vals).first<PlanRow>();
  return row ? mapPlan(row) : null;
}

/** Soft-delete: mark plan inactive */
export async function deletePlan(db: D1Database, planId: string): Promise<boolean> {
  const info = await db.prepare(
    `UPDATE rate_plans SET is_active = 0, updated_at = datetime('now') WHERE id = ?`
  ).bind(planId).run();
  return (info.meta.changes ?? 0) > 0;
}

/** Assign a rate plan to a tenant (upsert via REPLACE) */
export async function assignPlanToTenant(db: D1Database, input: {
  tenantId: string; ratePlanId: string; overrideRpm?: number; overrideRph?: number;
  overrideRpd?: number; expiresAt?: string; assignedBy?: string;
}): Promise<TenantAssignment> {
  // Remove existing assignment first (UNIQUE index on tenant_id)
  await db.prepare('DELETE FROM tenant_rate_plan_assignments WHERE tenant_id = ?')
    .bind(input.tenantId).run();
  const row = await db.prepare(`
    INSERT INTO tenant_rate_plan_assignments
      (tenant_id, rate_plan_id, override_rpm, override_rph, override_rpd, expires_at, assigned_by)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    RETURNING *
  `).bind(
    input.tenantId, input.ratePlanId,
    input.overrideRpm ?? null, input.overrideRph ?? null, input.overrideRpd ?? null,
    input.expiresAt ?? null, input.assignedBy ?? null,
  ).first<AssignmentRow>();
  return mapAssignment(row!);
}

/** Get tenant's current rate plan assignment */
export async function getTenantPlan(db: D1Database, tenantId: string): Promise<{
  assignment: TenantAssignment; plan: RatePlan;
} | null> {
  const row = await db.prepare(`
    SELECT a.*, p.id as p_id, p.name as p_name, p.description as p_desc, p.tier,
      p.requests_per_minute, p.requests_per_hour, p.requests_per_day,
      p.burst_limit, p.concurrent_limit, p.is_default, p.is_active,
      p.metadata, p.created_at as p_created, p.updated_at as p_updated
    FROM tenant_rate_plan_assignments a
    JOIN rate_plans p ON p.id = a.rate_plan_id
    WHERE a.tenant_id = ?
  `).bind(tenantId).first<Record<string, unknown>>();
  if (!row) return null;

  const assignment = mapAssignment({
    id: row['id'] as string, tenant_id: row['tenant_id'] as string,
    rate_plan_id: row['rate_plan_id'] as string, override_rpm: row['override_rpm'] as number | null,
    override_rph: row['override_rph'] as number | null, override_rpd: row['override_rpd'] as number | null,
    assigned_at: row['assigned_at'] as string, expires_at: row['expires_at'] as string | null,
    assigned_by: row['assigned_by'] as string | null,
  });
  const plan = mapPlan({
    id: row['p_id'] as string, name: row['p_name'] as string, description: row['p_desc'] as string | null,
    tier: row['tier'] as string, requests_per_minute: row['requests_per_minute'] as number,
    requests_per_hour: row['requests_per_hour'] as number, requests_per_day: row['requests_per_day'] as number,
    burst_limit: row['burst_limit'] as number, concurrent_limit: row['concurrent_limit'] as number,
    is_default: row['is_default'] as number, is_active: row['is_active'] as number,
    metadata: row['metadata'] as string, created_at: row['p_created'] as string,
    updated_at: row['p_updated'] as string,
  });
  return { assignment, plan };
}

/** Remove a tenant's rate plan assignment */
export async function removeTenantPlan(db: D1Database, tenantId: string): Promise<boolean> {
  const info = await db.prepare(
    'DELETE FROM tenant_rate_plan_assignments WHERE tenant_id = ?'
  ).bind(tenantId).run();
  return (info.meta.changes ?? 0) > 0;
}

/** Resolve effective rate limits for a tenant (applies overrides, falls back to default plan) */
export async function getEffectiveLimits(db: D1Database, tenantId: string): Promise<EffectiveLimits> {
  const result = await getTenantPlan(db, tenantId);
  if (result) {
    const { assignment, plan } = result;
    return {
      tenantId, ratePlanId: plan.id, planName: plan.name,
      requestsPerMinute: assignment.overrideRpm ?? plan.requestsPerMinute,
      requestsPerHour: assignment.overrideRph ?? plan.requestsPerHour,
      requestsPerDay: assignment.overrideRpd ?? plan.requestsPerDay,
      burstLimit: plan.burstLimit, concurrentLimit: plan.concurrentLimit,
      hasOverrides: !!(assignment.overrideRpm || assignment.overrideRph || assignment.overrideRpd),
    };
  }

  // Fall back to default active plan
  const defaultPlan = await db.prepare(
    'SELECT * FROM rate_plans WHERE is_default = 1 AND is_active = 1 LIMIT 1'
  ).first<PlanRow>();
  if (defaultPlan) {
    const p = mapPlan(defaultPlan);
    return {
      tenantId, ratePlanId: p.id, planName: p.name,
      requestsPerMinute: p.requestsPerMinute, requestsPerHour: p.requestsPerHour,
      requestsPerDay: p.requestsPerDay, burstLimit: p.burstLimit,
      concurrentLimit: p.concurrentLimit, hasOverrides: false,
    };
  }

  // No plan configured — return permissive defaults
  return {
    tenantId, ratePlanId: null, planName: null,
    requestsPerMinute: 60, requestsPerHour: 1000, requestsPerDay: 10000,
    burstLimit: 100, concurrentLimit: 10, hasOverrides: false,
  };
}

/** Admin overview: plan stats and assignment counts */
export async function getAdminRatePlanOverview(db: D1Database): Promise<{
  totalPlans: number; activePlans: number; totalAssignments: number;
  planBreakdown: Array<{ planId: string; planName: string; tier: string; assignedCount: number }>;
}> {
  const [totalRow, activeRow, assignRow, breakdown] = await Promise.all([
    db.prepare('SELECT COUNT(*) as cnt FROM rate_plans').first<{ cnt: number }>(),
    db.prepare('SELECT COUNT(*) as cnt FROM rate_plans WHERE is_active = 1').first<{ cnt: number }>(),
    db.prepare('SELECT COUNT(*) as cnt FROM tenant_rate_plan_assignments').first<{ cnt: number }>(),
    db.prepare(`
      SELECT p.id as plan_id, p.name as plan_name, p.tier,
        COUNT(a.id) as assigned_count
      FROM rate_plans p
      LEFT JOIN tenant_rate_plan_assignments a ON a.rate_plan_id = p.id
      GROUP BY p.id ORDER BY assigned_count DESC
    `).all<{ plan_id: string; plan_name: string; tier: string; assigned_count: number }>(),
  ]);

  return {
    totalPlans: totalRow?.cnt ?? 0,
    activePlans: activeRow?.cnt ?? 0,
    totalAssignments: assignRow?.cnt ?? 0,
    planBreakdown: (breakdown.results ?? []).map(r => ({
      planId: r.plan_id, planName: r.plan_name, tier: r.tier, assignedCount: r.assigned_count,
    })),
  };
}
