/**
 * Tenant Quotas Service — resource quota management per tenant, enforced by tier
 * Handles quota init, lookup, enforcement, snapshots, and admin overview
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface TenantQuota {
  id: string;
  tenantId: string;
  maxProjects: number;
  maxTeamMembers: number;
  maxApiKeys: number;
  maxMissionsPerDay: number;
  maxTemplates: number;
  maxWebhooks: number;
  maxStorageMb: number;
  customOverrides: Record<string, number> | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface QuotaCheckResult {
  allowed: boolean;
  resourceType: string;
  currentUsage: number;
  limit: number;
  percentUsed: number;
}

export interface QuotaUsage {
  resourceType: string;
  currentUsage: number;
  limit: number;
  percentUsed: number;
  nearLimit: boolean; // >= 80%
}

export type QuotaRow = {
  id: string; tenant_id: string; max_projects: number; max_team_members: number;
  max_api_keys: number; max_missions_per_day: number; max_templates: number;
  max_webhooks: number; max_storage_mb: number; custom_overrides: string | null;
  created_at: string; updated_at: string | null;
};

export type SnapshotRow = {
  tenant_id: string; resource_type: string; current_usage: number;
  quota_limit: number; snapshot_at: string;
};

/** Default quota values per tier */
export const TIER_DEFAULTS: Record<string, Omit<TenantQuota, 'id' | 'tenantId' | 'customOverrides' | 'createdAt' | 'updatedAt'>> = {
  starter:    { maxProjects: 3,   maxTeamMembers: 2,   maxApiKeys: 3,   maxMissionsPerDay: 50,    maxTemplates: 10,  maxWebhooks: 5,   maxStorageMb: 50    },
  pro:        { maxProjects: 10,  maxTeamMembers: 10,  maxApiKeys: 20,  maxMissionsPerDay: 500,   maxTemplates: 50,  maxWebhooks: 25,  maxStorageMb: 500   },
  enterprise: { maxProjects: 100, maxTeamMembers: 100, maxApiKeys: 100, maxMissionsPerDay: 10000, maxTemplates: 500, maxWebhooks: 100, maxStorageMb: 10000 },
};

export function mapQuota(row: QuotaRow): TenantQuota {
  return {
    id: row.id, tenantId: row.tenant_id,
    maxProjects: row.max_projects, maxTeamMembers: row.max_team_members,
    maxApiKeys: row.max_api_keys, maxMissionsPerDay: row.max_missions_per_day,
    maxTemplates: row.max_templates, maxWebhooks: row.max_webhooks,
    maxStorageMb: row.max_storage_mb,
    customOverrides: row.custom_overrides ? JSON.parse(row.custom_overrides) as Record<string, number> : null,
    createdAt: row.created_at, updatedAt: row.updated_at,
  };
}

/** Return tier defaults (public helper) */
export function getTierDefaults(tier: string) {
  return TIER_DEFAULTS[tier] ?? TIER_DEFAULTS['starter'];
}

/** Create quota record for a new tenant with tier defaults */
export async function initQuotas(db: D1Database, tenantId: string, tier: string): Promise<TenantQuota> {
  const d = getTierDefaults(tier);
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO tenant_quotas
      (id, tenant_id, max_projects, max_team_members, max_api_keys,
       max_missions_per_day, max_templates, max_webhooks, max_storage_mb)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, d.maxProjects, d.maxTeamMembers, d.maxApiKeys,
    d.maxMissionsPerDay, d.maxTemplates, d.maxWebhooks, d.maxStorageMb).run();
  const row = await db.prepare('SELECT * FROM tenant_quotas WHERE id = ?').bind(id).first<QuotaRow>();
  return mapQuota(row!);
}

/** Get current quotas for a tenant */
export async function getQuotas(db: D1Database, tenantId: string): Promise<TenantQuota | null> {
  const row = await db.prepare('SELECT * FROM tenant_quotas WHERE tenant_id = ?').bind(tenantId).first<QuotaRow>();
  return row ? mapQuota(row) : null;
}

/** Admin: update quota fields for a tenant */
export async function updateQuotas(
  db: D1Database, tenantId: string, updates: Partial<Record<string, number | null>>
): Promise<TenantQuota | null> {
  const fields: string[] = [];
  const values: unknown[] = [];
  const fieldMap: Record<string, string> = {
    maxProjects: 'max_projects', maxTeamMembers: 'max_team_members',
    maxApiKeys: 'max_api_keys', maxMissionsPerDay: 'max_missions_per_day',
    maxTemplates: 'max_templates', maxWebhooks: 'max_webhooks', maxStorageMb: 'max_storage_mb',
  };
  for (const [key, col] of Object.entries(fieldMap)) {
    if (key in updates) { fields.push(`${col} = ?`); values.push(updates[key]); }
  }
  if (fields.length === 0) return getQuotas(db, tenantId);
  fields.push("updated_at = datetime('now')");
  values.push(tenantId);
  await db.prepare(`UPDATE tenant_quotas SET ${fields.join(', ')} WHERE tenant_id = ?`).bind(...values).run();
  return getQuotas(db, tenantId);
}

/** Check if a resource type is within quota limit for a tenant */
export async function checkQuota(
  db: D1Database, tenantId: string, resourceType: string, currentUsage: number
): Promise<QuotaCheckResult> {
  const quotas = await getQuotas(db, tenantId);
  const limitMap: Record<string, keyof TenantQuota> = {
    projects: 'maxProjects', team_members: 'maxTeamMembers', api_keys: 'maxApiKeys',
    missions_today: 'maxMissionsPerDay', templates: 'maxTemplates',
    webhooks: 'maxWebhooks', storage_mb: 'maxStorageMb',
  };
  const field = limitMap[resourceType];
  const limit = field && quotas ? (quotas[field] as number) : 0;
  const allowed = limit > 0 ? currentUsage < limit : false;
  const percentUsed = limit > 0 ? Math.round((currentUsage / limit) * 100) : 100;
  return { allowed, resourceType, currentUsage, limit, percentUsed };
}

/** Get all resource usage vs limits from latest snapshots */
export async function getQuotaUsage(db: D1Database, tenantId: string): Promise<QuotaUsage[]> {
  const rows = await db.prepare(
    `SELECT resource_type, current_usage, quota_limit, MAX(snapshot_at) as snapshot_at
     FROM quota_usage_snapshots WHERE tenant_id = ? GROUP BY resource_type`
  ).bind(tenantId).all<SnapshotRow>();
  return (rows.results ?? []).map((r) => {
    const percentUsed = r.quota_limit > 0 ? Math.round((r.current_usage / r.quota_limit) * 100) : 0;
    return { resourceType: r.resource_type, currentUsage: r.current_usage, limit: r.quota_limit, percentUsed, nearLimit: percentUsed >= 80 };
  });
}

/** Record a usage snapshot for a resource type */
export async function recordUsageSnapshot(
  db: D1Database, tenantId: string, resourceType: string, usage: number, limit: number
): Promise<void> {
  await db.prepare(
    `INSERT INTO quota_usage_snapshots (id, tenant_id, resource_type, current_usage, quota_limit)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(crypto.randomUUID(), tenantId, resourceType, usage, limit).run();
}

/** Admin: get tenants at 75%+ quota utilization across all resource types */
export async function getAdminQuotaOverview(db: D1Database): Promise<{
  tenantId: string; resourceType: string; currentUsage: number; limit: number; percentUsed: number;
}[]> {
  const rows = await db.prepare(
    `SELECT tenant_id, resource_type, current_usage, quota_limit, MAX(snapshot_at) as snapshot_at
     FROM quota_usage_snapshots GROUP BY tenant_id, resource_type
     HAVING quota_limit > 0 AND CAST(current_usage AS REAL) / quota_limit >= 0.75
     ORDER BY CAST(current_usage AS REAL) / quota_limit DESC LIMIT 100`
  ).all<SnapshotRow>();
  return (rows.results ?? []).map((r) => ({
    tenantId: r.tenant_id, resourceType: r.resource_type,
    currentUsage: r.current_usage, limit: r.quota_limit,
    percentUsed: Math.round((r.current_usage / r.quota_limit) * 100),
  }));
}

/** Upgrade a tenant's quotas to match a new tier's defaults */
export async function upgradeQuotasForTier(
  db: D1Database, tenantId: string, newTier: string
): Promise<TenantQuota | null> {
  const d = getTierDefaults(newTier);
  return updateQuotas(db, tenantId, {
    maxProjects: d.maxProjects, maxTeamMembers: d.maxTeamMembers, maxApiKeys: d.maxApiKeys,
    maxMissionsPerDay: d.maxMissionsPerDay, maxTemplates: d.maxTemplates,
    maxWebhooks: d.maxWebhooks, maxStorageMb: d.maxStorageMb,
  });
}

/** Get usage history for a specific resource type */
export async function getQuotaHistory(
  db: D1Database, tenantId: string, resourceType: string, limit = 50
): Promise<{ resourceType: string; currentUsage: number; limit: number; snapshotAt: string }[]> {
  const safeLimit = Math.min(Math.max(1, limit), 200);
  const rows = await db.prepare(
    `SELECT resource_type, current_usage, quota_limit, snapshot_at
     FROM quota_usage_snapshots WHERE tenant_id = ? AND resource_type = ?
     ORDER BY snapshot_at DESC LIMIT ?`
  ).bind(tenantId, resourceType, safeLimit).all<SnapshotRow>();
  return (rows.results ?? []).map((r) => ({
    resourceType: r.resource_type, currentUsage: r.current_usage,
    limit: r.quota_limit, snapshotAt: r.snapshot_at,
  }));
}
