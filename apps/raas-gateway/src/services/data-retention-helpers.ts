/**
 * Data Retention Helpers — stats aggregation + policy seeding
 * Separated to keep data-retention-service.ts under 200 lines
 */

import type { D1Database } from '@cloudflare/workers-types';
import { getPolicies, createPolicy, VALID_DATA_TYPES } from './data-retention-service';
import type { RetentionPolicy, RetentionStats } from './data-retention-service';

/** Count records per data type that would be purged under current policies */
export async function getRetentionStats(
  db: D1Database, tenantId: string
): Promise<RetentionStats[]> {
  const DATA_TYPE_TABLES: Record<string, { table: string; dateColumn: string }> = {
    missions:      { table: 'missions',          dateColumn: 'created_at' },
    audit_logs:    { table: 'audit_logs',         dateColumn: 'created_at' },
    analytics:     { table: 'analytics_events',   dateColumn: 'created_at' },
    notifications: { table: 'notifications',      dateColumn: 'created_at' },
    webhooks:      { table: 'webhook_deliveries', dateColumn: 'created_at' },
  };

  const policies = await getPolicies(db, tenantId);
  const stats: RetentionStats[] = [];

  for (const policy of policies) {
    const mapping = DATA_TYPE_TABLES[policy.data_type];
    if (!mapping) continue;
    try {
      const row = await db.prepare(
        `SELECT COUNT(*) as cnt FROM ${mapping.table}
         WHERE tenant_id = ? AND ${mapping.dateColumn} < datetime('now', '-' || ? || ' days')`
      ).bind(tenantId, policy.retention_days).first<{ cnt: number }>();
      stats.push({
        data_type: policy.data_type,
        table: mapping.table,
        retention_days: policy.retention_days,
        records_affected: row?.cnt ?? 0,
      });
    } catch { /* table may not exist yet — skip */ }
  }

  return stats;
}

/** Seed default 90-day policies for all supported data types */
export async function seedDefaultPolicies(
  db: D1Database, tenantId: string
): Promise<RetentionPolicy[]> {
  for (const dataType of VALID_DATA_TYPES) {
    await createPolicy(db, tenantId, dataType, 90, false, true);
  }
  return getPolicies(db, tenantId);
}
