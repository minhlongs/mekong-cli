/**
 * API Rate Limit Policies Service — CRUD + templates + violations + stats
 *
 * Tables: rate_limit_policies, rate_limit_policy_templates, rate_limit_violations
 */

export interface RateLimitPolicy {
  id: string;
  tenant_id: string;
  policy_name: string;
  endpoint_pattern: string;
  method: string;
  max_requests: number;
  window_seconds: number;
  burst_limit: number;
  action_on_limit: string;
  is_active: number;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface PolicyTemplate {
  id: string;
  template_name: string;
  description: string | null;
  policies_json: string;
  is_default: number;
  created_at: string;
}

export interface PolicyViolation {
  id: string;
  tenant_id: string;
  policy_id: string;
  endpoint: string;
  violation_count: number;
  window_start: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Policies
// ---------------------------------------------------------------------------

export async function listPolicies(db: D1Database, tenantId: string): Promise<RateLimitPolicy[]> {
  const { results } = await db
    .prepare('SELECT * FROM rate_limit_policies WHERE tenant_id = ? ORDER BY priority DESC, created_at DESC')
    .bind(tenantId)
    .all<RateLimitPolicy>();
  return results;
}

export async function createPolicy(
  db: D1Database,
  tenantId: string,
  data: Omit<RateLimitPolicy, 'id' | 'tenant_id' | 'created_at' | 'updated_at'>
): Promise<{ id: string }> {
  const id = 'rlp_' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
  await db
    .prepare(
      `INSERT INTO rate_limit_policies
         (id, tenant_id, policy_name, endpoint_pattern, method, max_requests, window_seconds, burst_limit, action_on_limit, is_active, priority)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(
      id, tenantId,
      data.policy_name, data.endpoint_pattern, data.method ?? '*',
      data.max_requests ?? 100, data.window_seconds ?? 60, data.burst_limit ?? 0,
      data.action_on_limit ?? 'reject', data.is_active ?? 1, data.priority ?? 0
    )
    .run();
  return { id };
}

export async function updatePolicy(
  db: D1Database,
  id: string,
  tenantId: string,
  data: Partial<Omit<RateLimitPolicy, 'id' | 'tenant_id' | 'created_at' | 'updated_at'>>
): Promise<boolean> {
  const fields = Object.keys(data).filter(k => k !== 'id' && k !== 'tenant_id');
  if (fields.length === 0) return false;
  const sets = fields.map(f => `${f} = ?`).join(', ');
  const vals = fields.map(f => (data as Record<string, unknown>)[f]);
  const result = await db
    .prepare(`UPDATE rate_limit_policies SET ${sets}, updated_at = datetime('now') WHERE id = ? AND tenant_id = ?`)
    .bind(...vals, id, tenantId)
    .run();
  return (result.meta?.changes ?? 0) > 0;
}

export async function deletePolicy(db: D1Database, id: string, tenantId: string): Promise<boolean> {
  const result = await db
    .prepare('DELETE FROM rate_limit_policies WHERE id = ? AND tenant_id = ?')
    .bind(id, tenantId)
    .run();
  return (result.meta?.changes ?? 0) > 0;
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export async function listTemplates(db: D1Database): Promise<PolicyTemplate[]> {
  const { results } = await db
    .prepare('SELECT * FROM rate_limit_policy_templates ORDER BY is_default DESC, template_name ASC')
    .all<PolicyTemplate>();
  return results;
}

export async function createTemplate(
  db: D1Database,
  data: { template_name: string; description?: string; policies_json: string; is_default?: number }
): Promise<{ id: string }> {
  const id = 'rlt_' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
  await db
    .prepare(
      `INSERT INTO rate_limit_policy_templates (id, template_name, description, policies_json, is_default)
       VALUES (?, ?, ?, ?, ?)`
    )
    .bind(id, data.template_name, data.description ?? null, data.policies_json, data.is_default ?? 0)
    .run();
  return { id };
}

export async function applyTemplate(
  db: D1Database,
  tenantId: string,
  templateId: string
): Promise<{ applied: number }> {
  const tpl = await db
    .prepare('SELECT * FROM rate_limit_policy_templates WHERE id = ?')
    .bind(templateId)
    .first<PolicyTemplate>();
  if (!tpl) throw new Error('Template not found');

  const policies: Array<Omit<RateLimitPolicy, 'id' | 'tenant_id' | 'created_at' | 'updated_at'>> = JSON.parse(tpl.policies_json);
  await Promise.all(policies.map(p => createPolicy(db, tenantId, p)));
  return { applied: policies.length };
}

// ---------------------------------------------------------------------------
// Violations + stats
// ---------------------------------------------------------------------------

export async function getViolations(db: D1Database, tenantId: string, limit = 50): Promise<PolicyViolation[]> {
  const { results } = await db
    .prepare('SELECT * FROM rate_limit_violations WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?')
    .bind(tenantId, limit)
    .all<PolicyViolation>();
  return results;
}

export async function getPolicyStats(db: D1Database, tenantId: string): Promise<Record<string, unknown>> {
  const [total, active, violations] = await Promise.all([
    db.prepare('SELECT COUNT(*) as count FROM rate_limit_policies WHERE tenant_id = ?').bind(tenantId).first<{ count: number }>(),
    db.prepare('SELECT COUNT(*) as count FROM rate_limit_policies WHERE tenant_id = ? AND is_active = 1').bind(tenantId).first<{ count: number }>(),
    db.prepare('SELECT COUNT(*) as count, SUM(violation_count) as total_hits FROM rate_limit_violations WHERE tenant_id = ?').bind(tenantId).first<{ count: number; total_hits: number }>(),
  ]);
  return {
    total_policies: total?.count ?? 0,
    active_policies: active?.count ?? 0,
    violation_events: violations?.count ?? 0,
    total_violation_hits: violations?.total_hits ?? 0,
  };
}

export async function getAdminOverview(db: D1Database): Promise<Record<string, unknown>> {
  const [tenants, templates, violations] = await Promise.all([
    db.prepare('SELECT COUNT(DISTINCT tenant_id) as count FROM rate_limit_policies').first<{ count: number }>(),
    db.prepare('SELECT COUNT(*) as count FROM rate_limit_policy_templates').first<{ count: number }>(),
    db.prepare('SELECT COUNT(*) as count, SUM(violation_count) as total FROM rate_limit_violations').first<{ count: number; total: number }>(),
  ]);
  return {
    tenants_with_policies: tenants?.count ?? 0,
    total_templates: templates?.count ?? 0,
    total_violation_events: violations?.count ?? 0,
    total_violation_hits: violations?.total ?? 0,
  };
}
