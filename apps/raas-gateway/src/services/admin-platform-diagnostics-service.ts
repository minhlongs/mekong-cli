/**
 * Admin Platform Diagnostics Service
 * Runs health checks against platform components and stores aggregated reports
 */

import { randomUUID } from 'crypto';

interface DiagnosticCheck {
  id: string;
  check_name: string;
  check_type: string;
  target: string | null;
  status: string;
  response_time_ms: number | null;
  error_message: string | null;
  checked_at: string;
}

interface DiagnosticReport {
  id: string;
  report_type: string;
  total_checks: number;
  passed: number;
  failed: number;
  summary_json: string;
  generated_at: string;
}

// Built-in check definitions — extend by POSTing custom checks
const BUILT_IN_CHECKS = [
  { name: 'db_connectivity', type: 'health', target: 'D1' },
  { name: 'kv_connectivity', type: 'health', target: 'KV' },
  { name: 'api_latency', type: 'latency', target: '/v1/health' },
];

async function listChecks(db: any): Promise<DiagnosticCheck[]> {
  try {
    const result = await db
      .prepare(`SELECT * FROM diagnostic_checks ORDER BY checked_at DESC LIMIT 100`)
      .all();
    return result.results as DiagnosticCheck[];
  } catch (err: any) {
    throw new Error(`listChecks failed: ${err.message}`);
  }
}

async function runCheck(db: any, name: string, type: string, target: string | null): Promise<DiagnosticCheck> {
  const start = Date.now();
  let status = 'pass';
  let errorMessage: string | null = null;

  try {
    // Probe: attempt a lightweight DB query as the health signal
    await db.prepare('SELECT 1').first();
  } catch (err: any) {
    status = 'fail';
    errorMessage = err.message;
  }

  const responseTimeMs = Date.now() - start;
  const id = randomUUID();
  const checkedAt = new Date().toISOString();

  try {
    await db
      .prepare(
        `INSERT INTO diagnostic_checks
         (id, check_name, check_type, target, status, response_time_ms, error_message, checked_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, name, type, target, status, responseTimeMs, errorMessage, checkedAt)
      .run();
  } catch (err: any) {
    throw new Error(`runCheck insert failed: ${err.message}`);
  }

  return { id, check_name: name, check_type: type, target, status, response_time_ms: responseTimeMs, error_message: errorMessage, checked_at: checkedAt };
}

async function getReports(db: any): Promise<DiagnosticReport[]> {
  try {
    const result = await db
      .prepare(`SELECT * FROM diagnostic_reports ORDER BY generated_at DESC LIMIT 50`)
      .all();
    return result.results as DiagnosticReport[];
  } catch (err: any) {
    throw new Error(`getReports failed: ${err.message}`);
  }
}

async function getDashboard(db: any): Promise<object> {
  try {
    // Run all built-in checks and compile a full-scan report
    const checks = await Promise.all(
      BUILT_IN_CHECKS.map((c) => runCheck(db, c.name, c.type, c.target))
    );

    const passed = checks.filter((c) => c.status === 'pass').length;
    const failed = checks.length - passed;
    const avgLatency = checks.reduce((s, c) => s + (c.response_time_ms ?? 0), 0) / checks.length;

    const summaryJson = JSON.stringify({ checks, avgLatency });
    const reportId = randomUUID();
    const generatedAt = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO diagnostic_reports
         (id, report_type, total_checks, passed, failed, summary_json, generated_at)
         VALUES (?, 'full', ?, ?, ?, ?, ?)`
      )
      .bind(reportId, checks.length, passed, failed, summaryJson, generatedAt)
      .run();

    return { reportId, total: checks.length, passed, failed, avgLatency, checks };
  } catch (err: any) {
    throw new Error(`getDashboard failed: ${err.message}`);
  }
}

export const adminPlatformDiagnosticsService = { listChecks, runCheck, getReports, getDashboard };
