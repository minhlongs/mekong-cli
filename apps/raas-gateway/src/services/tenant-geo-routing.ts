/**
 * Tenant Geo Routing Service — per-tenant geographic routing rules and analytics
 * CRUD for geo_routing_rules, analytics reads, admin overview aggregation
 */

/** List all geo routing rules for a tenant, ordered by priority desc */
async function listRules(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const { results } = await db
      .prepare(
        'SELECT * FROM geo_routing_rules WHERE tenant_id = ? ORDER BY priority DESC, created_at ASC'
      )
      .bind(tenantId)
      .all();
    return { success: true, data: results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/** Create a new geo routing rule for a tenant */
async function createRule(
  db: any,
  tenantId: string,
  input: {
    rule_name: string;
    source_region: string;
    target_endpoint: string;
    priority?: number;
    enabled?: number;
  }
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO geo_routing_rules
         (id, tenant_id, rule_name, source_region, target_endpoint, priority, enabled, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        input.rule_name,
        input.source_region,
        input.target_endpoint,
        input.priority ?? 0,
        input.enabled ?? 1,
        now,
        now
      )
      .run();

    const row = await db
      .prepare('SELECT * FROM geo_routing_rules WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: row };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/** Get analytics records for a tenant, optionally filtered by rule_id */
async function getAnalytics(
  db: any,
  tenantId: string,
  ruleId?: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    let query = 'SELECT * FROM geo_routing_analytics WHERE tenant_id = ?';
    const bindings: unknown[] = [tenantId];

    if (ruleId) {
      query += ' AND rule_id = ?';
      bindings.push(ruleId);
    }

    query += ' ORDER BY recorded_at DESC';

    const { results } = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/** Admin overview — aggregate rules and analytics counts across all tenants */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const { results: ruleStats } = await db
      .prepare(
        `SELECT tenant_id,
                COUNT(*) AS total_rules,
                SUM(enabled) AS enabled_rules
         FROM geo_routing_rules
         GROUP BY tenant_id
         ORDER BY total_rules DESC`
      )
      .all();

    const { results: analyticsStats } = await db
      .prepare(
        `SELECT tenant_id,
                COUNT(*) AS analytics_records,
                SUM(requests_count) AS total_requests,
                AVG(avg_latency_ms) AS avg_latency_ms
         FROM geo_routing_analytics
         GROUP BY tenant_id
         ORDER BY total_requests DESC`
      )
      .all();

    return {
      success: true,
      data: {
        rules_by_tenant: ruleStats,
        analytics_by_tenant: analyticsStats,
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const tenantGeoRoutingService = {
  listRules,
  createRule,
  getAnalytics,
  getAdminOverview,
};
