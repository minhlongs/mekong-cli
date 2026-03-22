/**
 * Tenant API Throttling Service
 * Manage per-tenant endpoint throttle rules and throttle event logs.
 */

export interface ThrottleRule {
  id: string;
  tenant_id: string;
  endpoint_pattern: string;
  requests_per_minute: number;
  burst_limit: number;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface ThrottleEvent {
  id: string;
  tenant_id: string;
  rule_id: string;
  event_type: string;
  request_path: string;
  client_ip: string;
  created_at: string;
}

export interface CreateRuleData {
  endpoint_pattern: string;
  requests_per_minute?: number;
  burst_limit?: number;
}

/** List all throttle rules for a tenant */
export async function listRules(db: any, tenantId: string): Promise<ThrottleRule[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM throttle_rules WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as ThrottleRule[];
  } catch (err) {
    throw new Error(`Failed to list throttle rules: ${err}`);
  }
}

/** Create a new throttle rule for a tenant */
export async function createRule(
  db: any,
  tenantId: string,
  data: CreateRuleData
): Promise<ThrottleRule> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const rpm = data.requests_per_minute ?? 60;
    const burst = data.burst_limit ?? 10;

    await db
      .prepare(
        `INSERT INTO throttle_rules (id, tenant_id, endpoint_pattern, requests_per_minute, burst_limit, is_active, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 1, ?, ?)`
      )
      .bind(id, tenantId, data.endpoint_pattern, rpm, burst, now, now)
      .run();

    return {
      id,
      tenant_id: tenantId,
      endpoint_pattern: data.endpoint_pattern,
      requests_per_minute: rpm,
      burst_limit: burst,
      is_active: 1,
      created_at: now,
      updated_at: now,
    };
  } catch (err) {
    throw new Error(`Failed to create throttle rule: ${err}`);
  }
}

/** Get throttle events for a tenant */
export async function getEvents(db: any, tenantId: string): Promise<ThrottleEvent[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM throttle_events WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 200')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as ThrottleEvent[];
  } catch (err) {
    throw new Error(`Failed to get throttle events: ${err}`);
  }
}

/** Admin overview — rule and event counts across all tenants */
export async function getAdminOverview(db: any): Promise<{
  total_rules: number;
  active_rules: number;
  total_events: number;
  tenants_with_rules: number;
}> {
  try {
    const [rules, events, tenants] = await Promise.all([
      db.prepare('SELECT COUNT(*) as total, SUM(is_active) as active FROM throttle_rules').first(),
      db.prepare('SELECT COUNT(*) as total FROM throttle_events').first(),
      db.prepare('SELECT COUNT(DISTINCT tenant_id) as total FROM throttle_rules').first(),
    ]);

    return {
      total_rules: Number(rules?.total ?? 0),
      active_rules: Number(rules?.active ?? 0),
      total_events: Number(events?.total ?? 0),
      tenants_with_rules: Number(tenants?.total ?? 0),
    };
  } catch (err) {
    throw new Error(`Failed to get admin overview: ${err}`);
  }
}

export const tenantApiThrottlingService = {
  listRules,
  createRule,
  getEvents,
  getAdminOverview,
};
