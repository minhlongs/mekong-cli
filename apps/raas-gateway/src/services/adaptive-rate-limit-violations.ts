/**
 * Adaptive Rate Limit — Violation tracking + adaptive limit adjustment
 */

// ---------------------------------------------------------------------------
// Violations
// ---------------------------------------------------------------------------

export async function recordViolation(
  db: D1Database,
  tenantId: string,
  endpoint: string,
  violationType: string,
  requestCount: number,
  limitValue: number
): Promise<void> {
  await db
    .prepare(
      'INSERT INTO rate_limit_violations (id, tenant_id, endpoint, violation_type, request_count, limit_value) VALUES (?, ?, ?, ?, ?, ?)'
    )
    .bind(crypto.randomUUID(), tenantId, endpoint, violationType, requestCount, limitValue)
    .run();
}

export async function getViolationHistory(
  db: D1Database,
  tenantId: string,
  days = 7
): Promise<Record<string, unknown>[]> {
  const since = new Date(Date.now() - days * 86400000).toISOString();
  const { results } = await db
    .prepare(
      'SELECT * FROM rate_limit_violations WHERE tenant_id = ? AND occurred_at > ? ORDER BY occurred_at DESC LIMIT 500'
    )
    .bind(tenantId, since)
    .all();
  return results as Record<string, unknown>[];
}

export async function getTopViolators(db: D1Database, limit = 10): Promise<Record<string, unknown>[]> {
  const { results } = await db
    .prepare(
      `SELECT tenant_id, COUNT(*) as violation_count, MAX(occurred_at) as last_violation
       FROM rate_limit_violations
       WHERE occurred_at > datetime('now', '-30 days')
       GROUP BY tenant_id ORDER BY violation_count DESC LIMIT ?`
    )
    .bind(limit)
    .all();
  return results as Record<string, unknown>[];
}

// ---------------------------------------------------------------------------
// Adaptive limit adjustment (±20% based on 30d violation history)
// ---------------------------------------------------------------------------

export async function adaptLimits(
  db: D1Database,
  tenantId: string
): Promise<{ action: string; factor: number }> {
  const since30d = new Date(Date.now() - 30 * 86400000).toISOString();
  const row = await db
    .prepare(
      'SELECT COUNT(*) as cnt FROM rate_limit_violations WHERE tenant_id = ? AND occurred_at > ?'
    )
    .bind(tenantId, since30d)
    .first<{ cnt: number }>();

  const count = row?.cnt ?? 0;
  const factor = count === 0 ? 1.2 : count > 10 ? 0.8 : 1.0;
  const action = count === 0 ? 'increased' : count > 10 ? 'decreased' : 'unchanged';

  if (factor !== 1.0) {
    await db
      .prepare(
        `UPDATE rate_limit_configs
         SET requests_per_minute = CAST(requests_per_minute * ? AS INTEGER),
             requests_per_hour = CAST(requests_per_hour * ? AS INTEGER)
         WHERE tenant_id = ? AND is_active = 1`
      )
      .bind(factor, factor, tenantId)
      .run();
  }

  return { action, factor };
}
