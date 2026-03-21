/**
 * Audit Export Service — export audit logs, compliance checks, GDPR, data retention
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface AuditExportOptions {
  tenant_id: string;
  format: 'json' | 'csv';
  start_date?: string;
  end_date?: string;
  event_types?: string[];
  limit?: number;
}

export interface ComplianceCheck {
  name: string;
  status: 'pass' | 'fail' | 'warning';
  details: string;
}

interface AuditLogRow {
  id: string;
  timestamp: string;
  event_type: string;
  actor: string;
  details: string;
}

/**
 * Export audit logs as JSON string or CSV string (max 10,000 rows)
 */
export async function exportAuditLogs(
  db: D1Database,
  options: AuditExportOptions
): Promise<string> {
  const { tenant_id, format, start_date, end_date, event_types, limit } = options;
  const maxRows = Math.min(limit ?? 1000, 10000);

  let query = `SELECT id, created_at as timestamp, event_type, actor_id as actor, details
               FROM audit_log WHERE tenant_id = ?`;
  const params: (string | number)[] = [tenant_id];

  if (start_date) { query += ` AND created_at >= ?`; params.push(start_date); }
  if (end_date)   { query += ` AND created_at <= ?`; params.push(end_date); }
  if (event_types?.length) {
    query += ` AND event_type IN (${event_types.map(() => '?').join(',')})`;
    params.push(...event_types);
  }
  query += ` ORDER BY created_at DESC LIMIT ?`;
  params.push(maxRows);

  const result = await db.prepare(query).bind(...params).all<AuditLogRow>();
  const rows = result.results ?? [];

  if (format === 'csv') {
    const header = 'id,timestamp,event_type,actor,details';
    const lines = rows.map(r =>
      [r.id, r.timestamp, r.event_type, r.actor, `"${String(r.details ?? '').replace(/"/g, '""')}"`].join(',')
    );
    return [header, ...lines].join('\n');
  }

  return JSON.stringify({ count: rows.length, data: rows });
}

/**
 * Run compliance checklist for a tenant
 */
export async function getComplianceStatus(
  db: D1Database,
  tenantId: string
): Promise<ComplianceCheck[]> {
  const [tenant, apiKeys, teamMembers, webhooks, retention, auditSetting] = await Promise.all([
    db.prepare(`SELECT settings FROM tenants WHERE id = ?`).bind(tenantId).first<{ settings: string }>(),
    db.prepare(`SELECT last_used_at, revoked FROM api_keys WHERE tenant_id = ? AND revoked = 0`).bind(tenantId).all<{ last_used_at: string | null; revoked: number }>(),
    db.prepare(`SELECT status FROM team_members WHERE tenant_id = ? AND status = 'suspended'`).bind(tenantId).all<{ status: string }>(),
    db.prepare(`SELECT url FROM webhooks WHERE tenant_id = ?`).bind(tenantId).all<{ url: string }>(),
    db.prepare(`SELECT retention_days FROM data_retention_policies WHERE tenant_id = ?`).bind(tenantId).first<{ retention_days: number }>(),
    db.prepare(`SELECT audit_logging FROM tenants WHERE id = ?`).bind(tenantId).first<{ audit_logging: number }>(),
  ]);

  const settings = (() => { try { return JSON.parse(tenant?.settings ?? '{}'); } catch { return {}; } })();
  const cutoff = new Date(Date.now() - 90 * 86400 * 1000).toISOString();
  const activeKeys = apiKeys.results ?? [];
  const staleKeys = activeKeys.filter(k => !k.last_used_at || k.last_used_at < cutoff);
  const suspended = teamMembers.results ?? [];
  const hooks = webhooks.results ?? [];
  const nonHttps = hooks.filter(w => !w.url.startsWith('https://'));

  return [
    {
      name: 'MFA Enabled',
      status: settings.mfa_enabled ? 'pass' : 'warning',
      details: settings.mfa_enabled ? 'MFA is active' : 'MFA not configured for tenant',
    },
    {
      name: 'API Keys Rotated (90 days)',
      status: staleKeys.length === 0 ? 'pass' : 'fail',
      details: staleKeys.length === 0
        ? 'All active keys used within 90 days'
        : `${staleKeys.length} key(s) not rotated within 90 days`,
    },
    {
      name: 'No Suspended Members with Active Keys',
      status: suspended.length === 0 ? 'pass' : 'fail',
      details: suspended.length === 0
        ? 'No suspended members found'
        : `${suspended.length} suspended team member(s) may have active keys`,
    },
    {
      name: 'Webhook Endpoints Use HTTPS',
      status: nonHttps.length === 0 ? 'pass' : 'fail',
      details: nonHttps.length === 0
        ? 'All webhooks use HTTPS'
        : `${nonHttps.length} webhook(s) not using HTTPS`,
    },
    {
      name: 'Data Retention Policy Set',
      status: retention ? 'pass' : 'warning',
      details: retention
        ? `Retention: ${retention.retention_days} days`
        : 'No retention policy configured',
    },
    {
      name: 'Audit Logging Enabled',
      status: auditSetting?.audit_logging ? 'pass' : 'warning',
      details: auditSetting?.audit_logging ? 'Audit logging active' : 'Audit logging not confirmed',
    },
  ];
}

/**
 * Get data retention policy for tenant
 */
export async function getDataRetentionPolicy(
  db: D1Database,
  tenantId: string
): Promise<{ retention_days: number; auto_delete: boolean; last_purge: string | null }> {
  const row = await db.prepare(
    `SELECT retention_days, auto_delete, last_purge_at FROM data_retention_policies WHERE tenant_id = ?`
  ).bind(tenantId).first<{ retention_days: number; auto_delete: number; last_purge_at: string | null }>();

  return {
    retention_days: row?.retention_days ?? 365,
    auto_delete: Boolean(row?.auto_delete),
    last_purge: row?.last_purge_at ?? null,
  };
}

/**
 * Set or update data retention policy
 */
export async function setDataRetentionPolicy(
  db: D1Database,
  tenantId: string,
  days: number,
  autoDelete: boolean
): Promise<void> {
  await db.prepare(
    `INSERT INTO data_retention_policies (tenant_id, retention_days, auto_delete, updated_at)
     VALUES (?, ?, ?, datetime('now'))
     ON CONFLICT(tenant_id) DO UPDATE SET
       retention_days = excluded.retention_days,
       auto_delete = excluded.auto_delete,
       updated_at = datetime('now')`
  ).bind(tenantId, days, autoDelete ? 1 : 0).run();
}

/**
 * Purge audit logs and mission results beyond retention period
 */
export async function purgeExpiredData(
  db: D1Database,
  tenantId: string
): Promise<{ deleted_count: number; tables_affected: string[] }> {
  const policy = await getDataRetentionPolicy(db, tenantId);
  const cutoff = new Date(Date.now() - policy.retention_days * 86400 * 1000).toISOString();

  const [auditDel, missionDel] = await Promise.all([
    db.prepare(`DELETE FROM audit_log WHERE tenant_id = ? AND created_at < ?`).bind(tenantId, cutoff).run(),
    db.prepare(`DELETE FROM missions WHERE tenant_id = ? AND created_at < ? AND status IN ('completed','failed')`).bind(tenantId, cutoff).run(),
  ]);

  await db.prepare(
    `UPDATE data_retention_policies SET last_purge_at = datetime('now') WHERE tenant_id = ?`
  ).bind(tenantId).run();

  const deletedCount = (auditDel.meta?.changes ?? 0) + (missionDel.meta?.changes ?? 0);
  const tables = [];
  if ((auditDel.meta?.changes ?? 0) > 0) tables.push('audit_log');
  if ((missionDel.meta?.changes ?? 0) > 0) tables.push('missions');

  return { deleted_count: deletedCount, tables_affected: tables };
}

/**
 * GDPR full data export for a tenant
 */
export async function getGDPRExport(db: D1Database, tenantId: string): Promise<Record<string, unknown>> {
  const [profile, missions, apiKeys, teamMembers, billing] = await Promise.all([
    db.prepare(`SELECT id, name, email, tier, created_at FROM tenants WHERE id = ?`).bind(tenantId).first(),
    db.prepare(`SELECT id, title, status, credits_cost, created_at FROM missions WHERE tenant_id = ? LIMIT 1000`).bind(tenantId).all(),
    db.prepare(`SELECT id, name, created_at, last_used_at FROM api_keys WHERE tenant_id = ? AND revoked = 0`).bind(tenantId).all(),
    db.prepare(`SELECT id, email, role, status, created_at FROM team_members WHERE tenant_id = ?`).bind(tenantId).all(),
    db.prepare(`SELECT id, amount, currency, status, created_at FROM billing_events WHERE tenant_id = ? LIMIT 500`).bind(tenantId).all(),
  ]);

  return {
    exported_at: new Date().toISOString(),
    tenant_id: tenantId,
    profile,
    missions: missions.results ?? [],
    api_keys: apiKeys.results ?? [],
    team_members: teamMembers.results ?? [],
    billing_events: billing.results ?? [],
  };
}

/**
 * Queue a GDPR right-to-be-forgotten request
 */
export async function requestDataDeletion(
  db: D1Database,
  tenantId: string,
  reason: string
): Promise<{ request_id: string; status: 'pending' }> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO data_deletion_requests (id, tenant_id, reason, status) VALUES (?, ?, ?, 'pending')`
  ).bind(id, tenantId, reason).run();
  return { request_id: id, status: 'pending' };
}

/**
 * List past export history for a tenant
 */
export async function getExportHistory(
  db: D1Database,
  tenantId: string
): Promise<{ id: string; format: string; row_count: number; status: string; created_at: string }[]> {
  const result = await db.prepare(
    `SELECT id, format, row_count, status, created_at FROM audit_exports
     WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50`
  ).bind(tenantId).all<{ id: string; format: string; row_count: number; status: string; created_at: string }>();
  return result.results ?? [];
}
