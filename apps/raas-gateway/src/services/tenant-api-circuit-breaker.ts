/**
 * Tenant API Circuit Breaker Service
 * Manages per-tenant circuit breaker configs and event log in D1.
 * Tables: api_circuit_breakers, api_circuit_breaker_events
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export interface CircuitBreaker {
  id: string;
  tenant_id: string;
  endpoint_pattern: string;
  failure_threshold: number;
  recovery_timeout_ms: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CircuitBreakerEvent {
  id: string;
  tenant_id: string;
  breaker_id: string;
  event_type: string;
  failure_count: number | null;
  created_at: string;
}

export interface CreateBreakerInput {
  endpoint_pattern: string;
  failure_threshold?: number;
  recovery_timeout_ms?: number;
}

export interface ServiceResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

// ── Service functions ──────────────────────────────────────────────────────────

/**
 * List all circuit breakers for a tenant
 */
async function listBreakers(db: any, tenantId: string): Promise<ServiceResult> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, endpoint_pattern, failure_threshold,
                recovery_timeout_ms, status, created_at, updated_at
         FROM api_circuit_breakers
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();
    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/**
 * Create a new circuit breaker for a tenant
 */
async function createBreaker(db: any, tenantId: string, input: CreateBreakerInput): Promise<ServiceResult> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const failureThreshold = input.failure_threshold ?? 5;
    const recoveryTimeoutMs = input.recovery_timeout_ms ?? 30000;

    await db
      .prepare(
        `INSERT INTO api_circuit_breakers
           (id, tenant_id, endpoint_pattern, failure_threshold, recovery_timeout_ms, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 'closed', ?, ?)`
      )
      .bind(id, tenantId, input.endpoint_pattern, failureThreshold, recoveryTimeoutMs, now, now)
      .run();

    const breaker: CircuitBreaker = {
      id,
      tenant_id: tenantId,
      endpoint_pattern: input.endpoint_pattern,
      failure_threshold: failureThreshold,
      recovery_timeout_ms: recoveryTimeoutMs,
      status: 'closed',
      created_at: now,
      updated_at: now,
    };

    return { success: true, data: breaker };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/**
 * List circuit breaker events for a tenant
 * opts.limit: max events to return (default 50, max 200)
 * opts.breakerId: filter by specific breaker
 */
async function getEvents(
  db: any,
  tenantId: string,
  opts: { limit?: number; breakerId?: string } = {}
): Promise<ServiceResult> {
  try {
    const limit = Math.min(opts.limit ?? 50, 200);
    const { breakerId } = opts;

    const rows = breakerId
      ? await db
          .prepare(
            `SELECT id, tenant_id, breaker_id, event_type, failure_count, created_at
             FROM api_circuit_breaker_events
             WHERE tenant_id = ? AND breaker_id = ?
             ORDER BY created_at DESC LIMIT ?`
          )
          .bind(tenantId, breakerId, limit)
          .all()
      : await db
          .prepare(
            `SELECT id, tenant_id, breaker_id, event_type, failure_count, created_at
             FROM api_circuit_breaker_events
             WHERE tenant_id = ?
             ORDER BY created_at DESC LIMIT ?`
          )
          .bind(tenantId, limit)
          .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/**
 * Admin overview — breaker counts per tenant, recent events, status breakdown
 */
async function getAdminOverview(db: any): Promise<ServiceResult> {
  try {
    const [breakerStats, eventStats, recentEvents] = await Promise.all([
      db
        .prepare(
          `SELECT tenant_id,
                  COUNT(*) as total_breakers,
                  SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_breakers,
                  SUM(CASE WHEN status = 'half_open' THEN 1 ELSE 0 END) as half_open_breakers,
                  SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_breakers
           FROM api_circuit_breakers
           GROUP BY tenant_id
           ORDER BY total_breakers DESC
           LIMIT 50`
        )
        .all(),
      db
        .prepare(
          `SELECT tenant_id,
                  COUNT(*) as total_events,
                  COUNT(DISTINCT breaker_id) as breakers_triggered
           FROM api_circuit_breaker_events
           WHERE created_at >= datetime('now', '-24 hours')
           GROUP BY tenant_id
           ORDER BY total_events DESC
           LIMIT 50`
        )
        .all(),
      db
        .prepare(
          `SELECT id, tenant_id, breaker_id, event_type, failure_count, created_at
           FROM api_circuit_breaker_events
           ORDER BY created_at DESC LIMIT 20`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        breakerStats: breakerStats.results ?? [],
        eventStats: eventStats.results ?? [],
        recentEvents: recentEvents.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const tenantApiCircuitBreakerService = {
  listBreakers,
  createBreaker,
  getEvents,
  getAdminOverview,
};
