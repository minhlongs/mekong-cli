/**
 * Tenant Resource Quotas Service
 * Manages quota definitions, per-tenant limits, usage tracking, and alerts
 */

import type { D1Database } from '@cloudflare/workers-types';

interface QuotaDefinition {
  id: string;
  resource_type: string;
  display_name: string;
  description: string | null;
  default_limit: number;
  unit: string;
  enforcement: string;
  created_at: string;
}

interface TenantQuota {
  id: string;
  tenant_id: string;
  resource_type: string;
  quota_limit: number;
  current_usage: number;
  last_reset_at: string | null;
  reset_period: string;
  created_at: string;
  updated_at: string;
}

interface QuotaAlert {
  id: string;
  tenant_id: string;
  resource_type: string;
  threshold_pct: number;
  alert_type: string;
  message: string | null;
  triggered_at: string;
  acknowledged_at: string | null;
}

interface CheckResult {
  allowed: boolean;
  usage: number;
  limit: number;
  pct: number;
}

function uid(): string {
  return crypto.randomUUID();
}

function now(): string {
  return new Date().toISOString();
}

export const tenantResourceQuotasService = {
  /** List all quota definitions */
  async listDefinitions(db: D1Database): Promise<QuotaDefinition[]> {
    const res = await db.prepare('SELECT * FROM resource_quota_definitions ORDER BY resource_type').all<QuotaDefinition>();
    return res.results ?? [];
  },

  /** Create a new quota definition */
  async createDefinition(db: D1Database, data: Omit<QuotaDefinition, 'id' | 'created_at'>): Promise<QuotaDefinition> {
    const id = `def_${uid()}`;
    await db
      .prepare(
        `INSERT INTO resource_quota_definitions (id, resource_type, display_name, description, default_limit, unit, enforcement)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, data.resource_type, data.display_name, data.description ?? null, data.default_limit, data.unit ?? 'count', data.enforcement ?? 'soft')
      .run();
    return (await db.prepare('SELECT * FROM resource_quota_definitions WHERE id = ?').bind(id).first<QuotaDefinition>())!;
  },

  /** Update an existing quota definition by resource_type */
  async updateDefinition(db: D1Database, resourceType: string, data: Partial<Omit<QuotaDefinition, 'id' | 'resource_type' | 'created_at'>>): Promise<QuotaDefinition | null> {
    const sets: string[] = [];
    const values: unknown[] = [];
    if (data.display_name !== undefined) { sets.push('display_name = ?'); values.push(data.display_name); }
    if (data.description !== undefined) { sets.push('description = ?'); values.push(data.description); }
    if (data.default_limit !== undefined) { sets.push('default_limit = ?'); values.push(data.default_limit); }
    if (data.unit !== undefined) { sets.push('unit = ?'); values.push(data.unit); }
    if (data.enforcement !== undefined) { sets.push('enforcement = ?'); values.push(data.enforcement); }
    if (sets.length === 0) return null;
    values.push(resourceType);
    await db.prepare(`UPDATE resource_quota_definitions SET ${sets.join(', ')} WHERE resource_type = ?`).bind(...values).run();
    return db.prepare('SELECT * FROM resource_quota_definitions WHERE resource_type = ?').bind(resourceType).first<QuotaDefinition>();
  },

  /** Get all quotas for a tenant (merges with definitions for defaults) */
  async getTenantQuotas(db: D1Database, tenantId: string): Promise<TenantQuota[]> {
    const res = await db.prepare('SELECT * FROM tenant_quotas WHERE tenant_id = ? ORDER BY resource_type').bind(tenantId).all<TenantQuota>();
    return res.results ?? [];
  },

  /** Upsert a tenant quota limit */
  async setTenantQuota(db: D1Database, tenantId: string, resourceType: string, limit: number): Promise<TenantQuota> {
    const id = `tq_${uid()}`;
    await db
      .prepare(
        `INSERT INTO tenant_quotas (id, tenant_id, resource_type, quota_limit, updated_at)
         VALUES (?, ?, ?, ?, ?)
         ON CONFLICT(tenant_id, resource_type) DO UPDATE SET quota_limit = excluded.quota_limit, updated_at = excluded.updated_at`
      )
      .bind(id, tenantId, resourceType, limit, now())
      .run();
    return (await db.prepare('SELECT * FROM tenant_quotas WHERE tenant_id = ? AND resource_type = ?').bind(tenantId, resourceType).first<TenantQuota>())!;
  },

  /** Check if tenant is within quota; falls back to definition default_limit */
  async checkQuota(db: D1Database, tenantId: string, resourceType: string): Promise<CheckResult> {
    const [quota, def] = await Promise.all([
      db.prepare('SELECT * FROM tenant_quotas WHERE tenant_id = ? AND resource_type = ?').bind(tenantId, resourceType).first<TenantQuota>(),
      db.prepare('SELECT default_limit FROM resource_quota_definitions WHERE resource_type = ?').bind(resourceType).first<{ default_limit: number }>(),
    ]);
    const limit = quota?.quota_limit ?? def?.default_limit ?? 0;
    const usage = quota?.current_usage ?? 0;
    const pct = limit > 0 ? Math.round((usage / limit) * 100) : 0;
    return { allowed: limit === 0 || usage < limit, usage, limit, pct };
  },

  /** Increment usage counter for a resource */
  async incrementUsage(db: D1Database, tenantId: string, resourceType: string, amount = 1): Promise<void> {
    const id = `tq_${uid()}`;
    await db
      .prepare(
        `INSERT INTO tenant_quotas (id, tenant_id, resource_type, quota_limit, current_usage, updated_at)
         VALUES (?, ?, ?, 0, ?, ?)
         ON CONFLICT(tenant_id, resource_type) DO UPDATE SET current_usage = current_usage + ?, updated_at = excluded.updated_at`
      )
      .bind(id, tenantId, resourceType, amount, now(), amount)
      .run();
  },

  /** Reset usage to 0 for a resource */
  async resetUsage(db: D1Database, tenantId: string, resourceType: string): Promise<void> {
    await db
      .prepare('UPDATE tenant_quotas SET current_usage = 0, last_reset_at = ?, updated_at = ? WHERE tenant_id = ? AND resource_type = ?')
      .bind(now(), now(), tenantId, resourceType)
      .run();
  },

  /** List alerts for a tenant */
  async listAlerts(db: D1Database, tenantId: string): Promise<QuotaAlert[]> {
    const res = await db.prepare('SELECT * FROM quota_alerts WHERE tenant_id = ? ORDER BY triggered_at DESC').bind(tenantId).all<QuotaAlert>();
    return res.results ?? [];
  },

  /** Acknowledge an alert */
  async acknowledgeAlert(db: D1Database, tenantId: string, alertId: string): Promise<boolean> {
    const result = await db
      .prepare('UPDATE quota_alerts SET acknowledged_at = ? WHERE id = ? AND tenant_id = ?')
      .bind(now(), alertId, tenantId)
      .run();
    return (result.meta?.changes ?? 0) > 0;
  },

  /** Admin overview: global usage stats and top consumers per resource */
  async getAdminOverview(db: D1Database): Promise<Record<string, unknown>> {
    const [defs, totals, topConsumers] = await Promise.all([
      db.prepare('SELECT COUNT(*) as count FROM resource_quota_definitions').first<{ count: number }>(),
      db.prepare(`SELECT resource_type, SUM(current_usage) as total_usage, COUNT(tenant_id) as tenant_count, AVG(current_usage) as avg_usage FROM tenant_quotas GROUP BY resource_type`).all<{ resource_type: string; total_usage: number; tenant_count: number; avg_usage: number }>(),
      db.prepare(`SELECT tenant_id, resource_type, current_usage, quota_limit FROM tenant_quotas ORDER BY current_usage DESC LIMIT 10`).all<{ tenant_id: string; resource_type: string; current_usage: number; quota_limit: number }>(),
    ]);
    return {
      definitionCount: defs?.count ?? 0,
      byResource: totals.results ?? [],
      topConsumers: topConsumers.results ?? [],
      generatedAt: now(),
    };
  },
};
