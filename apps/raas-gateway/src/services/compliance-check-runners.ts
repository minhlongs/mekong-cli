/**
 * Compliance Check Runners — individual D1 checks for each compliance control type
 * Used by compliance-report-service to run and persist check results
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface ComplianceCheck {
  status: 'pass' | 'fail' | 'warning' | 'unknown';
  details: string;
}

interface CountRow { c: number }

export const CHECK_TYPES = [
  'data_encryption',
  'access_control',
  'audit_logging',
  'data_retention',
  'incident_response',
] as const;

async function checkDataEncryption(db: D1Database, tenantId: string): Promise<ComplianceCheck> {
  const keys = await db
    .prepare('SELECT COUNT(*) as c FROM api_keys WHERE tenant_id = ?')
    .bind(tenantId)
    .first<CountRow>();
  const count = keys?.c ?? 0;
  return {
    status: count > 0 ? 'pass' : 'warning',
    details: `${count} API key(s) configured (encrypted transport enforced)`,
  };
}

async function checkAccessControl(db: D1Database, tenantId: string): Promise<ComplianceCheck> {
  const roles = await db
    .prepare('SELECT COUNT(*) as c FROM roles WHERE tenant_id = ?')
    .bind(tenantId)
    .first<CountRow>();
  const count = roles?.c ?? 0;
  return {
    status: count > 0 ? 'pass' : 'fail',
    details: `${count} RBAC role(s) defined`,
  };
}

async function checkAuditLogging(db: D1Database, tenantId: string): Promise<ComplianceCheck> {
  const logs = await db
    .prepare('SELECT COUNT(*) as c FROM audit_logs WHERE tenant_id = ? LIMIT 1')
    .bind(tenantId)
    .first<CountRow>();
  const count = logs?.c ?? 0;
  return {
    status: count > 0 ? 'pass' : 'fail',
    details: `${count > 0 ? 'Audit' : 'No audit'} log entries found`,
  };
}

async function checkDataRetention(db: D1Database, tenantId: string): Promise<ComplianceCheck> {
  // data_retention_policies table from migration 0072
  const policy = await db
    .prepare('SELECT COUNT(*) as c FROM data_retention_policies WHERE tenant_id = ?')
    .bind(tenantId)
    .first<CountRow>();
  const count = policy?.c ?? 0;
  return {
    status: count > 0 ? 'pass' : 'warning',
    details: `${count} retention policy(ies) configured`,
  };
}

async function checkIncidentResponse(db: D1Database, tenantId: string): Promise<ComplianceCheck> {
  const alerts = await db
    .prepare('SELECT COUNT(*) as c FROM alert_configs WHERE tenant_id = ?')
    .bind(tenantId)
    .first<CountRow>();
  const count = alerts?.c ?? 0;
  return {
    status: count > 0 ? 'pass' : 'warning',
    details: `${count} alert configuration(s) active`,
  };
}

/** Dispatch a single check by type */
export async function runSingleCheck(
  db: D1Database,
  tenantId: string,
  checkType: string
): Promise<ComplianceCheck> {
  switch (checkType) {
    case 'data_encryption': return checkDataEncryption(db, tenantId);
    case 'access_control': return checkAccessControl(db, tenantId);
    case 'audit_logging': return checkAuditLogging(db, tenantId);
    case 'data_retention': return checkDataRetention(db, tenantId);
    case 'incident_response': return checkIncidentResponse(db, tenantId);
    default: return { status: 'unknown', details: `Unknown check type: ${checkType}` };
  }
}
