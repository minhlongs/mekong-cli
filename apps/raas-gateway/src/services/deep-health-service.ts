/**
 * Deep Health Service — dependency-aware health checks for D1, KV, and AI bindings
 * Tracks health history and supports trending/alerting
 */

import type { D1Database, KVNamespace } from '@cloudflare/workers-types';
import type { Env } from '../index';

export interface HealthCheck {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms: number;
  details?: Record<string, unknown>;
}

export interface HealthResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: HealthCheck[];
  timestamp: string;
}

interface HealthSnapshot {
  id: string;
  overall_status: string;
  checks: string;
  timestamp: string;
}

/**
 * Checks D1 database health via SELECT 1 + write test
 */
export async function checkD1Health(db: D1Database): Promise<HealthCheck> {
  const start = Date.now();
  try {
    await db.prepare('SELECT 1').run();

    // Write test — insert + delete in health_checks table
    const testId = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO health_checks (id, created_at) VALUES (?, ?)`
    ).bind(testId, new Date().toISOString()).run();
    await db.prepare(`DELETE FROM health_checks WHERE id = ?`).bind(testId).run();

    return {
      name: 'd1',
      status: 'healthy',
      latency_ms: Date.now() - start,
      details: { write_test: 'passed' },
    };
  } catch (err) {
    return {
      name: 'd1',
      status: 'unhealthy',
      latency_ms: Date.now() - start,
      details: { error: String(err) },
    };
  }
}

/**
 * Checks KV store health via put + get + delete of a test key
 */
export async function checkKVHealth(kv: KVNamespace): Promise<HealthCheck> {
  const start = Date.now();
  const testKey = `__health_check_${crypto.randomUUID()}`;
  try {
    await kv.put(testKey, 'ok', { expirationTtl: 60 });
    const val = await kv.get(testKey);
    await kv.delete(testKey);

    return {
      name: 'kv',
      status: val === 'ok' ? 'healthy' : 'degraded',
      latency_ms: Date.now() - start,
      details: { read_back: val === 'ok' ? 'matched' : 'mismatch' },
    };
  } catch (err) {
    return {
      name: 'kv',
      status: 'unhealthy',
      latency_ms: Date.now() - start,
      details: { error: String(err) },
    };
  }
}

/**
 * Checks AI binding availability via typeof check (no actual inference cost)
 */
export async function checkAIHealth(ai: Ai | undefined): Promise<HealthCheck> {
  const start = Date.now();
  const available = typeof ai !== 'undefined' && ai !== null;
  return {
    name: 'ai',
    status: available ? 'healthy' : 'degraded',
    latency_ms: Date.now() - start,
    details: { binding_available: available },
  };
}

/**
 * Runs all health checks in parallel and returns combined result
 * Overall status = worst individual status
 */
export async function runFullHealthCheck(env: Env): Promise<HealthResult> {
  const [d1, kv, ai] = await Promise.all([
    checkD1Health(env.DB),
    checkKVHealth(env.RATE_LIMIT_KV),
    checkAIHealth(env.AI),
  ]);

  const checks = [d1, kv, ai];
  const hasUnhealthy = checks.some(c => c.status === 'unhealthy');
  const hasDegraded = checks.some(c => c.status === 'degraded');
  const overall: HealthResult['status'] = hasUnhealthy ? 'unhealthy' : hasDegraded ? 'degraded' : 'healthy';

  return { status: overall, checks, timestamp: new Date().toISOString() };
}

/**
 * Retrieves historical health snapshots for trending
 */
export async function getHealthHistory(
  db: D1Database,
  limit = 24
): Promise<HealthResult[]> {
  const safeLimit = Math.min(limit, 100);
  const { results } = await db.prepare(
    `SELECT * FROM health_snapshots ORDER BY timestamp DESC LIMIT ?`
  ).bind(safeLimit).all<HealthSnapshot>();

  return results.map(row => ({
    status: row.overall_status as HealthResult['status'],
    checks: JSON.parse(row.checks) as HealthCheck[],
    timestamp: row.timestamp,
  }));
}

/**
 * Records a health snapshot for trending and alerting
 */
export async function recordHealthSnapshot(
  db: D1Database,
  result: HealthResult
): Promise<void> {
  await db.prepare(
    `INSERT INTO health_snapshots (id, overall_status, checks, timestamp) VALUES (?, ?, ?, ?)`
  ).bind(
    crypto.randomUUID(),
    result.status,
    JSON.stringify(result.checks),
    result.timestamp
  ).run();
}
