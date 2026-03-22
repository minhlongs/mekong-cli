/**
 * Tenant API Throttling Service
 * Manages per-tenant throttle rules and records throttle events in D1.
 * Tables: api_throttle_rules, api_throttle_events
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ThrottleRule {
  id: string;
  tenant_id: string;
  rule_name: string;
  endpoint_pattern: string;
  max_concurrent: number;
  queue_timeout_ms: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ThrottleEvent {
  id: string;
  tenant_id: string;
  rule_id: string;
  event_type: string;
  request_path: string | null;
  queued_ms: number | null;
  created_at: string;
}

export interface CreateRuleInput {
  rule_name: string;
  endpoint_pattern: string;
  max_concurrent?: number;
  queue_timeout_ms?: number;
}

export interface ServiceResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

// ── Service functions ──────────────────────────────────────────────────────────

/**
 * List all throttle rules for a tenant
 */
async function listRules(db: any, tenantId: string): Promise<ServiceResult> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, rule_name, endpoint_pattern,
                max_concurrent, queue_timeout_ms, status, created_at, updated_at
         FROM api_throttle_rules
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
 * Create a new throttle rule for a tenant
 */
async function createRule(db: any, tenantId: string, input: CreateRuleInput): Promise<ServiceResult> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const maxConcurrent = input.max_concurrent ?? 10;
    const queueTimeoutMs = input.queue_timeout_ms ?? 30000;

    await db
      .prepare(
        `INSERT INTO api_throttle_rules
           (id, tenant_id, rule_name, endpoint_pattern, max_concurrent, queue_timeout_ms, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)`
      )
      .bind(id, tenantId, input.rule_name, input.endpoint_pattern, maxConcurrent, queueTimeoutMs, now, now)
      .run();

    const rule: ThrottleRule = {
      id,
      tenant_id: tenantId,
      rule_name: input.rule_name,
      endpoint_pattern: input.endpoint_pattern,
      max_concurrent: maxConcurrent,
      queue_timeout_ms: queueTimeoutMs,
      status: 'active',
      created_at: now,
      updated_at: now,
    };

    return { success: true, data: rule };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/**
 * List throttle events for a tenant
 * opts.limit: max events to return (default 50, max 200)
 * opts.ruleId: filter by specific rule
 */
async function getEvents(
  db: any,
  tenantId: string,
  opts: { limit?: number; ruleId?: string } = {}
): Promise<ServiceResult> {
  try {
    const limit = Math.min(opts.limit ?? 50, 200);
    const { ruleId } = opts;

    const rows = ruleId
      ? await db
          .prepare(
            `SELECT id, tenant_id, rule_id, event_type, request_path, queued_ms, created_at
             FROM api_throttle_events
             WHERE tenant_id = ? AND rule_id = ?
             ORDER BY created_at DESC LIMIT ?`
          )
          .bind(tenantId, ruleId, limit)
          .all()
      : await db
          .prepare(
            `SELECT id, tenant_id, rule_id, event_type, request_path, queued_ms, created_at
             FROM api_throttle_events
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
 * Admin overview — rule counts per tenant, recent event activity, last 20 events
 */
async function getAdminOverview(db: any): Promise<ServiceResult> {
  try {
    const [ruleStats, eventStats, recentEvents] = await Promise.all([
      db
        .prepare(
          `SELECT tenant_id,
                  COUNT(*) as total_rules,
                  SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_rules
           FROM api_throttle_rules
           GROUP BY tenant_id
           ORDER BY total_rules DESC
           LIMIT 50`
        )
        .all(),
      db
        .prepare(
          `SELECT tenant_id,
                  COUNT(*) as total_events,
                  COUNT(DISTINCT rule_id) as rules_triggered
           FROM api_throttle_events
           WHERE created_at >= datetime('now', '-24 hours')
           GROUP BY tenant_id
           ORDER BY total_events DESC
           LIMIT 50`
        )
        .all(),
      db
        .prepare(
          `SELECT id, tenant_id, rule_id, event_type, request_path, queued_ms, created_at
           FROM api_throttle_events
           ORDER BY created_at DESC LIMIT 20`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        ruleStats: ruleStats.results ?? [],
        eventStats: eventStats.results ?? [],
        recentEvents: recentEvents.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const tenantApiThrottlingService = {
  listRules,
  createRule,
  getEvents,
  getAdminOverview,
};
