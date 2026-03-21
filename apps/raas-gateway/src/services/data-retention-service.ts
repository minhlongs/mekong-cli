/**
 * Data Retention Service — CRUD for retention policies + purge execution
 * Supports: missions, audit_logs, analytics, notifications, webhooks
 */

import type { D1Database } from '@cloudflare/workers-types';

/** Map data type to its physical table and date column */
const DATA_TYPE_TABLES: Record<string, { table: string; dateColumn: string }> = {
  missions:      { table: 'missions',           dateColumn: 'created_at' },
  audit_logs:    { table: 'audit_logs',          dateColumn: 'created_at' },
  analytics:     { table: 'analytics_events',    dateColumn: 'created_at' },
  notifications: { table: 'notifications',       dateColumn: 'created_at' },
  webhooks:      { table: 'webhook_deliveries',  dateColumn: 'created_at' },
};

export const VALID_DATA_TYPES = Object.keys(DATA_TYPE_TABLES);

export interface RetentionPolicy {
  id: string;
  tenant_id: string;
  data_type: string;
  retention_days: number;
  auto_purge: number;
  archive_before_purge: number;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface PurgeLog {
  id: string;
  tenant_id: string;
  policy_id: string;
  data_type: string;
  records_purged: number;
  records_archived: number;
  purged_at: string;
}

export interface RetentionStats {
  data_type: string;
  table: string;
  retention_days: number;
  records_affected: number;
}

/** Upsert retention policy for tenant + data_type */
export async function createPolicy(
  db: D1Database,
  tenantId: string,
  dataType: string,
  retentionDays: number,
  autoPurge = false,
  archiveBeforePurge = true,
): Promise<RetentionPolicy> {
  const id = crypto.randomUUID();
  await db.prepare(`
    INSERT INTO retention_policies
      (id, tenant_id, data_type, retention_days, auto_purge, archive_before_purge)
    VALUES (?,?,?,?,?,?)
    ON CONFLICT(tenant_id, data_type) DO UPDATE SET
      retention_days = excluded.retention_days,
      auto_purge = excluded.auto_purge,
      archive_before_purge = excluded.archive_before_purge,
      updated_at = datetime('now')
  `).bind(id, tenantId, dataType, retentionDays, autoPurge ? 1 : 0, archiveBeforePurge ? 1 : 0).run();

  return getPolicy(db, tenantId, dataType) as Promise<RetentionPolicy>;
}

/** List all retention policies for a tenant */
export async function getPolicies(db: D1Database, tenantId: string): Promise<RetentionPolicy[]> {
  const { results } = await db.prepare(
    'SELECT * FROM retention_policies WHERE tenant_id = ? ORDER BY data_type'
  ).bind(tenantId).all<RetentionPolicy>();
  return results;
}

/** Get single policy by data type */
export async function getPolicy(
  db: D1Database, tenantId: string, dataType: string
): Promise<RetentionPolicy | null> {
  return db.prepare(
    'SELECT * FROM retention_policies WHERE tenant_id = ? AND data_type = ?'
  ).bind(tenantId, dataType).first<RetentionPolicy>();
}

/** Get policy by id (for update/delete authorization) */
export async function getPolicyById(
  db: D1Database, tenantId: string, policyId: string
): Promise<RetentionPolicy | null> {
  return db.prepare(
    'SELECT * FROM retention_policies WHERE id = ? AND tenant_id = ?'
  ).bind(policyId, tenantId).first<RetentionPolicy>();
}

export interface UpdatePolicyInput {
  retention_days?: number;
  auto_purge?: boolean;
  archive_before_purge?: boolean;
  is_active?: boolean;
}

/** Partial update for a policy — only provided fields are changed */
export async function updatePolicy(
  db: D1Database, tenantId: string, policyId: string, updates: UpdatePolicyInput
): Promise<RetentionPolicy | null> {
  const fields: string[] = ["updated_at = datetime('now')"];
  const values: unknown[] = [];

  if (updates.retention_days !== undefined)      { fields.push('retention_days = ?');      values.push(updates.retention_days); }
  if (updates.auto_purge !== undefined)          { fields.push('auto_purge = ?');          values.push(updates.auto_purge ? 1 : 0); }
  if (updates.archive_before_purge !== undefined){ fields.push('archive_before_purge = ?'); values.push(updates.archive_before_purge ? 1 : 0); }
  if (updates.is_active !== undefined)           { fields.push('is_active = ?');           values.push(updates.is_active ? 1 : 0); }

  values.push(policyId, tenantId);
  await db.prepare(
    `UPDATE retention_policies SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`
  ).bind(...values).run();

  return getPolicyById(db, tenantId, policyId);
}

/** Remove a policy */
export async function deletePolicy(
  db: D1Database, tenantId: string, policyId: string
): Promise<boolean> {
  const { meta } = await db.prepare(
    'DELETE FROM retention_policies WHERE id = ? AND tenant_id = ?'
  ).bind(policyId, tenantId).run();
  return (meta.changes ?? 0) > 0;
}

/** Execute purge for a single policy — deletes old rows, logs result */
export async function executePurge(
  db: D1Database, tenantId: string, policyId: string
): Promise<PurgeLog> {
  const policy = await getPolicyById(db, tenantId, policyId);
  if (!policy) throw new Error('Policy not found');

  const mapping = DATA_TYPE_TABLES[policy.data_type];
  if (!mapping) throw new Error(`Unknown data type: ${policy.data_type}`);

  // Count records that will be purged
  const countRow = await db.prepare(
    `SELECT COUNT(*) as cnt FROM ${mapping.table}
     WHERE tenant_id = ? AND ${mapping.dateColumn} < datetime('now', '-' || ? || ' days')`
  ).bind(tenantId, policy.retention_days).first<{ cnt: number }>();
  const count = countRow?.cnt ?? 0;

  // Delete expired records
  await db.prepare(
    `DELETE FROM ${mapping.table}
     WHERE tenant_id = ? AND ${mapping.dateColumn} < datetime('now', '-' || ? || ' days')`
  ).bind(tenantId, policy.retention_days).run();

  // Write purge log
  const logId = crypto.randomUUID();
  await db.prepare(`
    INSERT INTO retention_purge_logs
      (id, tenant_id, policy_id, data_type, records_purged, records_archived)
    VALUES (?,?,?,?,?,?)
  `).bind(logId, tenantId, policyId, policy.data_type, count, 0).run();

  return db.prepare(
    'SELECT * FROM retention_purge_logs WHERE id = ?'
  ).bind(logId).first<PurgeLog>() as Promise<PurgeLog>;
}

/** Admin: list all active auto-purge policies (for cron jobs) */
export async function getDuePolicies(db: D1Database): Promise<RetentionPolicy[]> {
  const { results } = await db.prepare(
    'SELECT * FROM retention_policies WHERE auto_purge = 1 AND is_active = 1'
  ).all<RetentionPolicy>();
  return results;
}

/** Get purge history for a tenant */
export async function getPurgeLogs(db: D1Database, tenantId: string): Promise<PurgeLog[]> {
  const { results } = await db.prepare(
    'SELECT * FROM retention_purge_logs WHERE tenant_id = ? ORDER BY purged_at DESC LIMIT 100'
  ).bind(tenantId).all<PurgeLog>();
  return results;
}

// getRetentionStats + seedDefaultPolicies → see data-retention-helpers.ts
