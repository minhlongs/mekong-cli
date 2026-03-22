/**
 * Admin Platform Security Scan Service — CRUD for platform_security_scans and platform_security_findings
 * Used by admin-platform-security-scan routes. All functions accept db: any (D1 binding).
 */

import { randomUUID } from 'crypto';

/** List all platform security scans, optionally filtered by scan_type or status */
async function listScans(db: any, filters?: { scan_type?: string; status?: string }): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    let query = 'SELECT * FROM platform_security_scans';
    const bindings: string[] = [];
    const conditions: string[] = [];

    if (filters?.scan_type) {
      conditions.push('scan_type = ?');
      bindings.push(filters.scan_type);
    }
    if (filters?.status) {
      conditions.push('status = ?');
      bindings.push(filters.status);
    }
    if (conditions.length > 0) {
      query += ' WHERE ' + conditions.join(' AND ');
    }
    query += ' ORDER BY created_at DESC';

    const rows = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: rows.results };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** Create a new security scan record */
async function createScan(
  db: any,
  data: { scan_type: string; target: string }
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    if (!data.scan_type || !data.target) {
      return { success: false, error: 'scan_type and target are required' };
    }

    const id = randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO platform_security_scans
           (id, scan_type, target, status, started_at, created_at)
         VALUES (?, ?, ?, 'pending', ?, ?)`
      )
      .bind(id, data.scan_type, data.target, now, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM platform_security_scans WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: row };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** List findings for a scan, optionally filtered by severity or status */
async function getFindings(
  db: any,
  filters?: { scan_id?: string; severity?: string; status?: string }
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    let query = 'SELECT * FROM platform_security_findings';
    const bindings: string[] = [];
    const conditions: string[] = [];

    if (filters?.scan_id) {
      conditions.push('scan_id = ?');
      bindings.push(filters.scan_id);
    }
    if (filters?.severity) {
      conditions.push('severity = ?');
      bindings.push(filters.severity);
    }
    if (filters?.status) {
      conditions.push('status = ?');
      bindings.push(filters.status);
    }
    if (conditions.length > 0) {
      query += ' WHERE ' + conditions.join(' AND ');
    }
    query += ' ORDER BY created_at DESC';

    const rows = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: rows.results };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** Dashboard summary: scan counts by status/type, severity breakdown, recent findings */
async function getDashboard(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const byStatus = await db
      .prepare('SELECT status, COUNT(*) as count FROM platform_security_scans GROUP BY status')
      .all();
    const byType = await db
      .prepare('SELECT scan_type, COUNT(*) as count FROM platform_security_scans GROUP BY scan_type')
      .all();
    const bySeverity = await db
      .prepare('SELECT severity, COUNT(*) as count FROM platform_security_findings GROUP BY severity')
      .all();
    const recentFindings = await db
      .prepare('SELECT * FROM platform_security_findings ORDER BY created_at DESC LIMIT 10')
      .all();
    const totals = await db
      .prepare(
        `SELECT
           COALESCE(SUM(severity_high), 0) as total_high,
           COALESCE(SUM(severity_medium), 0) as total_medium,
           COALESCE(SUM(severity_low), 0) as total_low,
           COALESCE(SUM(findings_count), 0) as total_findings
         FROM platform_security_scans`
      )
      .first();

    return {
      success: true,
      data: {
        by_status: byStatus.results,
        by_type: byType.results,
        by_severity: bySeverity.results,
        totals,
        recent_findings: recentFindings.results,
      },
    };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

export const adminPlatformSecurityScanService = {
  listScans,
  createScan,
  getFindings,
  getDashboard,
};
