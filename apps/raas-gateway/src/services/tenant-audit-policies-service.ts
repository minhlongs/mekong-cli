/**
 * Tenant Audit Policies Service — policy CRUD, event enforcement, violation tracking, admin overview
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface AuditPolicy {
  id: string;
  tenantId: string;
  policyName: string;
  eventTypes: string[];
  retentionDays: number;
  logLevel: 'minimal' | 'standard' | 'verbose';
  includeRequestBody: boolean;
  includeResponseBody: boolean;
  exportEnabled: boolean;
  exportDestination: string | null;
  exportConfig: Record<string, unknown>;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AuditPolicyViolation {
  id: string;
  tenantId: string;
  policyId: string;
  eventType: string;
  violationType: 'retention_exceeded' | 'unauthorized_access' | 'policy_breach';
  details: Record<string, unknown>;
  severity: 'info' | 'warning' | 'critical';
  resolved: boolean;
  resolvedAt: string | null;
  createdAt: string;
}

type PolicyRow = {
  id: string; tenant_id: string; policy_name: string; event_types: string;
  retention_days: number; log_level: string; include_request_body: number;
  include_response_body: number; export_enabled: number; export_destination: string | null;
  export_config: string; is_active: number; created_at: string; updated_at: string;
};

type ViolationRow = {
  id: string; tenant_id: string; policy_id: string; event_type: string;
  violation_type: string; details: string; severity: string;
  resolved: number; resolved_at: string | null; created_at: string;
};

function mapPolicy(row: PolicyRow): AuditPolicy {
  return {
    id: row.id, tenantId: row.tenant_id, policyName: row.policy_name,
    eventTypes: JSON.parse(row.event_types) as string[],
    retentionDays: row.retention_days,
    logLevel: row.log_level as AuditPolicy['logLevel'],
    includeRequestBody: row.include_request_body === 1,
    includeResponseBody: row.include_response_body === 1,
    exportEnabled: row.export_enabled === 1,
    exportDestination: row.export_destination,
    exportConfig: JSON.parse(row.export_config) as Record<string, unknown>,
    isActive: row.is_active === 1,
    createdAt: row.created_at, updatedAt: row.updated_at,
  };
}

function mapViolation(row: ViolationRow): AuditPolicyViolation {
  return {
    id: row.id, tenantId: row.tenant_id, policyId: row.policy_id,
    eventType: row.event_type,
    violationType: row.violation_type as AuditPolicyViolation['violationType'],
    details: JSON.parse(row.details) as Record<string, unknown>,
    severity: row.severity as AuditPolicyViolation['severity'],
    resolved: row.resolved === 1, resolvedAt: row.resolved_at, createdAt: row.created_at,
  };
}

/** Create a new audit policy for a tenant */
export async function createPolicy(
  db: D1Database, tenantId: string, data: {
    policyName: string; eventTypes?: string[]; retentionDays?: number;
    logLevel?: string; includeRequestBody?: boolean; includeResponseBody?: boolean;
    exportEnabled?: boolean; exportDestination?: string; exportConfig?: Record<string, unknown>;
  }
): Promise<AuditPolicy> {
  const row = await db.prepare(
    `INSERT INTO audit_policies
      (tenant_id, policy_name, event_types, retention_days, log_level,
       include_request_body, include_response_body, export_enabled, export_destination, export_config)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     RETURNING *`
  ).bind(
    tenantId, data.policyName,
    JSON.stringify(data.eventTypes ?? ['*']),
    data.retentionDays ?? 90,
    data.logLevel ?? 'standard',
    data.includeRequestBody ? 1 : 0,
    data.includeResponseBody ? 1 : 0,
    data.exportEnabled ? 1 : 0,
    data.exportDestination ?? null,
    JSON.stringify(data.exportConfig ?? {}),
  ).first<PolicyRow>();
  return mapPolicy(row!);
}

/** List all audit policies for a tenant */
export async function listPolicies(db: D1Database, tenantId: string): Promise<AuditPolicy[]> {
  const rows = await db.prepare(
    `SELECT * FROM audit_policies WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenantId).all<PolicyRow>();
  return (rows.results ?? []).map(mapPolicy);
}

/** Get a single audit policy by ID (tenant-scoped) */
export async function getPolicy(
  db: D1Database, tenantId: string, policyId: string
): Promise<AuditPolicy | null> {
  const row = await db.prepare(
    `SELECT * FROM audit_policies WHERE id = ? AND tenant_id = ?`
  ).bind(policyId, tenantId).first<PolicyRow>();
  return row ? mapPolicy(row) : null;
}

/** Update an audit policy (partial update) */
export async function updatePolicy(
  db: D1Database, tenantId: string, policyId: string,
  data: Partial<{
    policyName: string; eventTypes: string[]; retentionDays: number;
    logLevel: string; includeRequestBody: boolean; includeResponseBody: boolean;
    exportEnabled: boolean; exportDestination: string | null;
    exportConfig: Record<string, unknown>; isActive: boolean;
  }>
): Promise<AuditPolicy | null> {
  const sets: string[] = ['updated_at = datetime(\'now\')'];
  const vals: unknown[] = [];
  if (data.policyName !== undefined) { sets.push('policy_name = ?'); vals.push(data.policyName); }
  if (data.eventTypes !== undefined) { sets.push('event_types = ?'); vals.push(JSON.stringify(data.eventTypes)); }
  if (data.retentionDays !== undefined) { sets.push('retention_days = ?'); vals.push(data.retentionDays); }
  if (data.logLevel !== undefined) { sets.push('log_level = ?'); vals.push(data.logLevel); }
  if (data.includeRequestBody !== undefined) { sets.push('include_request_body = ?'); vals.push(data.includeRequestBody ? 1 : 0); }
  if (data.includeResponseBody !== undefined) { sets.push('include_response_body = ?'); vals.push(data.includeResponseBody ? 1 : 0); }
  if (data.exportEnabled !== undefined) { sets.push('export_enabled = ?'); vals.push(data.exportEnabled ? 1 : 0); }
  if (data.exportDestination !== undefined) { sets.push('export_destination = ?'); vals.push(data.exportDestination); }
  if (data.exportConfig !== undefined) { sets.push('export_config = ?'); vals.push(JSON.stringify(data.exportConfig)); }
  if (data.isActive !== undefined) { sets.push('is_active = ?'); vals.push(data.isActive ? 1 : 0); }
  if (sets.length === 1) return getPolicy(db, tenantId, policyId);
  vals.push(policyId, tenantId);
  const row = await db.prepare(
    `UPDATE audit_policies SET ${sets.join(', ')} WHERE id = ? AND tenant_id = ? RETURNING *`
  ).bind(...vals).first<PolicyRow>();
  return row ? mapPolicy(row) : null;
}

/** Delete an audit policy */
export async function deletePolicy(
  db: D1Database, tenantId: string, policyId: string
): Promise<boolean> {
  const result = await db.prepare(
    `DELETE FROM audit_policies WHERE id = ? AND tenant_id = ?`
  ).bind(policyId, tenantId).run();
  return (result.meta?.changes ?? 0) > 0;
}

/** Check an event type against all active policies for a tenant; returns matching policies */
export async function checkEventAgainstPolicies(
  db: D1Database, tenantId: string, eventType: string
): Promise<AuditPolicy[]> {
  const all = await listPolicies(db, tenantId);
  return all.filter((p) =>
    p.isActive && (p.eventTypes.includes('*') || p.eventTypes.includes(eventType))
  );
}

/** Record a policy violation */
export async function recordViolation(
  db: D1Database, tenantId: string, data: {
    policyId: string; eventType: string;
    violationType: string; details?: Record<string, unknown>; severity?: string;
  }
): Promise<AuditPolicyViolation> {
  const row = await db.prepare(
    `INSERT INTO audit_policy_violations (tenant_id, policy_id, event_type, violation_type, details, severity)
     VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    tenantId, data.policyId, data.eventType, data.violationType,
    JSON.stringify(data.details ?? {}), data.severity ?? 'warning',
  ).first<ViolationRow>();
  return mapViolation(row!);
}

/** List violations for a tenant with optional filters */
export async function listViolations(
  db: D1Database, tenantId: string,
  opts: { resolved?: boolean; severity?: string; limit?: number } = {}
): Promise<AuditPolicyViolation[]> {
  const conditions = ['tenant_id = ?'];
  const vals: unknown[] = [tenantId];
  if (opts.resolved !== undefined) { conditions.push('resolved = ?'); vals.push(opts.resolved ? 1 : 0); }
  if (opts.severity) { conditions.push('severity = ?'); vals.push(opts.severity); }
  vals.push(Math.min(opts.limit ?? 50, 200));
  const rows = await db.prepare(
    `SELECT * FROM audit_policy_violations WHERE ${conditions.join(' AND ')} ORDER BY created_at DESC LIMIT ?`
  ).bind(...vals).all<ViolationRow>();
  return (rows.results ?? []).map(mapViolation);
}

/** Mark a violation as resolved */
export async function resolveViolation(
  db: D1Database, tenantId: string, violationId: string
): Promise<AuditPolicyViolation | null> {
  const row = await db.prepare(
    `UPDATE audit_policy_violations SET resolved = 1, resolved_at = datetime('now')
     WHERE id = ? AND tenant_id = ? RETURNING *`
  ).bind(violationId, tenantId).first<ViolationRow>();
  return row ? mapViolation(row) : null;
}

/** Admin: overview of all tenants — policy counts and unresolved critical violations */
export async function getAdminPolicyOverview(db: D1Database): Promise<{
  tenantId: string; totalPolicies: number; activePolicies: number;
  unresolvedCritical: number; unresolvedWarning: number;
}[]> {
  const rows = await db.prepare(
    `SELECT
       ap.tenant_id,
       COUNT(DISTINCT ap.id) as total_policies,
       SUM(CASE WHEN ap.is_active = 1 THEN 1 ELSE 0 END) as active_policies,
       SUM(CASE WHEN v.severity = 'critical' AND v.resolved = 0 THEN 1 ELSE 0 END) as unresolved_critical,
       SUM(CASE WHEN v.severity = 'warning' AND v.resolved = 0 THEN 1 ELSE 0 END) as unresolved_warning
     FROM audit_policies ap
     LEFT JOIN audit_policy_violations v ON v.policy_id = ap.id
     GROUP BY ap.tenant_id ORDER BY unresolved_critical DESC LIMIT 100`
  ).all<{ tenant_id: string; total_policies: number; active_policies: number; unresolved_critical: number; unresolved_warning: number; }>();
  return (rows.results ?? []).map((r) => ({
    tenantId: r.tenant_id, totalPolicies: r.total_policies,
    activePolicies: r.active_policies,
    unresolvedCritical: r.unresolved_critical ?? 0,
    unresolvedWarning: r.unresolved_warning ?? 0,
  }));
}
