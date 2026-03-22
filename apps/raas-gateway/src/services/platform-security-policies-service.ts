// Platform Security Policies Service — policy management, templates, violations, compliance
import type { D1Database } from '@cloudflare/workers-types';

/** List all active policies for a tenant */
export async function listPolicies(db: D1Database, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM security_policies WHERE tenant_id = ? AND deleted = 0 ORDER BY created_at DESC`
  ).bind(tenantId).all();
  return rows.results;
}

/** Create a new security policy for a tenant */
export async function createPolicy(
  db: D1Database,
  tenantId: string,
  data: {
    policy_name: string;
    policy_type?: string;
    rules_json?: Record<string, unknown>;
    is_enforced?: boolean;
    severity?: string;
  }
): Promise<unknown> {
  const id = crypto.randomUUID();
  return db.prepare(
    `INSERT INTO security_policies (id, tenant_id, policy_name, policy_type, rules_json, is_enforced, severity)
     VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id,
    tenantId,
    data.policy_name,
    data.policy_type ?? 'access',
    JSON.stringify(data.rules_json ?? {}),
    data.is_enforced !== false ? 1 : 0,
    data.severity ?? 'medium'
  ).first();
}

/** Update an existing policy owned by tenant */
export async function updatePolicy(
  db: D1Database,
  tenantId: string,
  policyId: string,
  data: {
    policy_name?: string;
    policy_type?: string;
    rules_json?: Record<string, unknown>;
    is_enforced?: boolean;
    severity?: string;
  }
): Promise<unknown | null> {
  const sets: string[] = ["updated_at = datetime('now')"];
  const binds: unknown[] = [];

  if (data.policy_name !== undefined) { sets.push('policy_name = ?'); binds.push(data.policy_name); }
  if (data.policy_type !== undefined) { sets.push('policy_type = ?'); binds.push(data.policy_type); }
  if (data.rules_json !== undefined) { sets.push('rules_json = ?'); binds.push(JSON.stringify(data.rules_json)); }
  if (data.is_enforced !== undefined) { sets.push('is_enforced = ?'); binds.push(data.is_enforced ? 1 : 0); }
  if (data.severity !== undefined) { sets.push('severity = ?'); binds.push(data.severity); }

  binds.push(policyId, tenantId);
  return db.prepare(
    `UPDATE security_policies SET ${sets.join(', ')}
     WHERE id = ? AND tenant_id = ? AND deleted = 0 RETURNING *`
  ).bind(...binds).first();
}

/** Soft-delete a policy owned by tenant */
export async function deletePolicy(
  db: D1Database,
  tenantId: string,
  policyId: string
): Promise<unknown | null> {
  return db.prepare(
    `UPDATE security_policies SET deleted = 1, updated_at = datetime('now')
     WHERE id = ? AND tenant_id = ? AND deleted = 0 RETURNING id`
  ).bind(policyId, tenantId).first();
}

/** List all policy templates (public) */
export async function listTemplates(db: D1Database): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM security_policy_templates ORDER BY policy_type, name`
  ).all();
  return rows.results;
}

/** Apply a template to a tenant — creates a new policy from the template's defaults */
export async function applyTemplate(
  db: D1Database,
  tenantId: string,
  templateId: string
): Promise<unknown | null> {
  const tpl = await db.prepare(
    `SELECT * FROM security_policy_templates WHERE id = ?`
  ).bind(templateId).first<{ name: string; policy_type: string; default_rules_json: string }>();

  if (!tpl) return null;

  const id = crypto.randomUUID();
  return db.prepare(
    `INSERT INTO security_policies (id, tenant_id, policy_name, policy_type, rules_json, is_enforced, severity)
     VALUES (?, ?, ?, ?, ?, 1, 'medium') RETURNING *`
  ).bind(id, tenantId, tpl.name, tpl.policy_type, tpl.default_rules_json).first();
}

/** List violations for a tenant (unresolved first) */
export async function listViolations(db: D1Database, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM security_violations WHERE tenant_id = ?
     ORDER BY resolved ASC, detected_at DESC`
  ).bind(tenantId).all();
  return rows.results;
}

/** Mark a violation as resolved */
export async function resolveViolation(
  db: D1Database,
  tenantId: string,
  violationId: string
): Promise<unknown | null> {
  return db.prepare(
    `UPDATE security_violations SET resolved = 1, resolved_at = datetime('now')
     WHERE id = ? AND tenant_id = ? AND resolved = 0 RETURNING *`
  ).bind(violationId, tenantId).first();
}

/** Compute compliance score: % of active policies enforced with no open violations */
export async function getComplianceScore(db: D1Database, tenantId: string): Promise<unknown> {
  const [total, enforced, openViolations] = await Promise.all([
    db.prepare(
      `SELECT COUNT(*) as count FROM security_policies WHERE tenant_id = ? AND deleted = 0`
    ).bind(tenantId).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM security_policies WHERE tenant_id = ? AND deleted = 0 AND is_enforced = 1`
    ).bind(tenantId).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM security_violations WHERE tenant_id = ? AND resolved = 0`
    ).bind(tenantId).first<{ count: number }>(),
  ]);

  const totalCount = total?.count ?? 0;
  const enforcedCount = enforced?.count ?? 0;
  const violationsCount = openViolations?.count ?? 0;
  const score = totalCount === 0 ? 100 : Math.round((enforcedCount / totalCount) * 100);

  return { score, total: totalCount, enforced: enforcedCount, open_violations: violationsCount };
}

/** Admin overview: platform-wide security stats */
export async function getAdminOverview(db: D1Database): Promise<unknown> {
  const [policies, enforced, templates, violations, unresolvedViolations] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM security_policies WHERE deleted = 0`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM security_policies WHERE deleted = 0 AND is_enforced = 1`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM security_policy_templates`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM security_violations`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM security_violations WHERE resolved = 0`).first<{ count: number }>(),
  ]);

  return {
    policies: { total: policies?.count ?? 0, enforced: enforced?.count ?? 0 },
    templates: templates?.count ?? 0,
    violations: { total: violations?.count ?? 0, unresolved: unresolvedViolations?.count ?? 0 },
  };
}
