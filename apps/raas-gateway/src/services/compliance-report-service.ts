/**
 * Compliance Report Service — SOC2/GDPR/HIPAA/PCI report generation and scoring
 * Orchestrates check runners and persists results to D1
 */

import type { D1Database } from '@cloudflare/workers-types';
import { CHECK_TYPES, runSingleCheck } from './compliance-check-runners';

export type { ComplianceCheck } from './compliance-check-runners';

export interface ComplianceScore {
  category: string;
  pass: number;
  total: number;
  score: number; // 0-100
}

interface CheckRow { check_type: string; status: string }

/** Run all compliance checks for a category and persist results to D1 */
export async function runComplianceChecks(
  db: D1Database,
  tenantId: string,
  category: string
): Promise<Array<{ checkType: string; status: string; details: string }>> {
  const results = [];
  for (const checkType of CHECK_TYPES) {
    const result = await runSingleCheck(db, tenantId, checkType);
    await db
      .prepare(
        `INSERT INTO compliance_checks (id, tenant_id, check_type, category, status, details)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
      .bind(crypto.randomUUID(), tenantId, checkType, category, result.status, result.details)
      .run();
    results.push({ checkType, ...result });
  }
  return results;
}

/** Calculate pass/total score for a category based on latest check per type */
export async function getComplianceScore(
  db: D1Database,
  tenantId: string,
  category: string
): Promise<ComplianceScore> {
  const rows = await db
    .prepare(
      `SELECT check_type, status FROM compliance_checks
       WHERE tenant_id = ? AND category = ?
       GROUP BY check_type HAVING MAX(checked_at)`
    )
    .bind(tenantId, category)
    .all<CheckRow>();

  const checks = rows.results ?? [];
  const pass = checks.filter((r: CheckRow) => r.status === 'pass').length;
  const total = checks.length || CHECK_TYPES.length;
  return { category, pass, total, score: Math.round((pass / total) * 100) };
}

/** Generate a full compliance report: run checks and store aggregated result */
export async function generateReport(
  db: D1Database,
  tenantId: string,
  reportType: string,
  coverageStart: string,
  coverageEnd: string
): Promise<{ id: string; status: string }> {
  const id = crypto.randomUUID();
  const title = `${reportType.toUpperCase()} Compliance Report`;
  const checks = await runComplianceChecks(db, tenantId, reportType);
  const pass = checks.filter((c) => c.status === 'pass').length;
  const reportData = JSON.stringify({ checks, summary: { pass, total: checks.length } });
  const expiresAt = new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString();

  await db
    .prepare(
      `INSERT INTO compliance_reports
         (id, tenant_id, report_type, title, status, report_data, coverage_start, coverage_end, expires_at)
       VALUES (?, ?, ?, ?, 'ready', ?, ?, ?, ?)`
    )
    .bind(id, tenantId, reportType, title, reportData, coverageStart, coverageEnd, expiresAt)
    .run();

  return { id, status: 'ready' };
}

/** List reports for tenant, optionally filtered by report type */
export async function getReports(
  db: D1Database,
  tenantId: string,
  reportType?: string
): Promise<unknown[]> {
  const base = `SELECT id, tenant_id, report_type, title, status,
                       coverage_start, coverage_end, generated_at, expires_at
                FROM compliance_reports WHERE tenant_id = ?`;
  const stmt = reportType
    ? db.prepare(`${base} AND report_type = ? ORDER BY generated_at DESC`).bind(tenantId, reportType)
    : db.prepare(`${base} ORDER BY generated_at DESC`).bind(tenantId);
  const rows = await stmt.all();
  return rows.results ?? [];
}

/** Get single report with full report_data payload */
export async function getReport(
  db: D1Database,
  tenantId: string,
  reportId: string
): Promise<unknown | null> {
  return db
    .prepare('SELECT * FROM compliance_reports WHERE id = ? AND tenant_id = ?')
    .bind(reportId, tenantId)
    .first();
}

/** Delete a report, returns true if a row was removed */
export async function deleteReport(
  db: D1Database,
  tenantId: string,
  reportId: string
): Promise<boolean> {
  const result = await db
    .prepare('DELETE FROM compliance_reports WHERE id = ? AND tenant_id = ?')
    .bind(reportId, tenantId)
    .run();
  return result.meta?.changes > 0;
}

/** Get historical check results for tenant + category (last 100) */
export async function getCheckHistory(
  db: D1Database,
  tenantId: string,
  category: string
): Promise<unknown[]> {
  const rows = await db
    .prepare(
      `SELECT id, check_type, status, details, checked_at
       FROM compliance_checks WHERE tenant_id = ? AND category = ?
       ORDER BY checked_at DESC LIMIT 100`
    )
    .bind(tenantId, category)
    .all();
  return rows.results ?? [];
}

/** Cross-category summary: score for soc2, gdpr, hipaa, pci */
export async function getComplianceSummary(
  db: D1Database,
  tenantId: string
): Promise<ComplianceScore[]> {
  const categories = ['soc2', 'gdpr', 'hipaa', 'pci'];
  return Promise.all(categories.map((cat) => getComplianceScore(db, tenantId, cat)));
}

/** Export report with parsed report_data for downstream consumption */
export async function exportReport(
  db: D1Database,
  tenantId: string,
  reportId: string
): Promise<unknown | null> {
  const report = (await getReport(db, tenantId, reportId)) as Record<string, unknown> | null;
  if (!report) return null;
  return {
    ...report,
    report_data: report.report_data ? JSON.parse(report.report_data as string) : null,
    exported_at: new Date().toISOString(),
  };
}

/** Return supported compliance frameworks with check type descriptions */
export function getFrameworks(): object {
  return {
    frameworks: [
      { id: 'soc2', name: 'SOC 2 Type II', checks: CHECK_TYPES, description: 'Security, availability, and confidentiality controls' },
      { id: 'gdpr', name: 'GDPR', checks: CHECK_TYPES, description: 'EU General Data Protection Regulation compliance' },
      { id: 'hipaa', name: 'HIPAA', checks: CHECK_TYPES, description: 'Health Insurance Portability and Accountability Act' },
      { id: 'pci', name: 'PCI DSS', checks: CHECK_TYPES, description: 'Payment Card Industry Data Security Standard' },
      { id: 'custom', name: 'Custom', checks: CHECK_TYPES, description: 'Custom compliance framework' },
    ],
    check_types: {
      data_encryption: 'Verify encrypted communications and key management',
      access_control: 'Verify RBAC roles and access policies',
      audit_logging: 'Verify audit trail completeness',
      data_retention: 'Verify data retention policies are configured',
      incident_response: 'Verify alert and incident response configs',
    },
  };
}
