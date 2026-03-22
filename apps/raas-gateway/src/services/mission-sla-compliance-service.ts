/**
 * Mission SLA Compliance Service — policy management and violation tracking
 */

function newId(): string {
  return crypto.randomUUID();
}

// ── Policies ───────────────────────────────────────────────────────────────

async function listPolicies(db: any, tenantId: string): Promise<unknown[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM mission_sla_policies WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as unknown[];
  } catch (err) {
    throw new Error(`listPolicies failed: ${String(err)}`);
  }
}

async function createPolicy(
  db: any,
  tenantId: string,
  input: {
    policy_name: string;
    max_execution_time_ms?: number;
    min_success_rate?: number;
    evaluation_window?: string;
  },
): Promise<unknown> {
  try {
    const id = newId();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO mission_sla_policies
         (id, tenant_id, policy_name, max_execution_time_ms, min_success_rate, evaluation_window, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)`,
      )
      .bind(
        id,
        tenantId,
        input.policy_name,
        input.max_execution_time_ms ?? 30000,
        input.min_success_rate ?? 0.95,
        input.evaluation_window ?? '24h',
        now,
        now,
      )
      .run();
    const row = await db
      .prepare('SELECT * FROM mission_sla_policies WHERE id = ?')
      .bind(id)
      .first();
    return row as unknown;
  } catch (err) {
    throw new Error(`createPolicy failed: ${String(err)}`);
  }
}

// ── Violations ─────────────────────────────────────────────────────────────

async function getViolations(
  db: any,
  tenantId: string,
  policyId?: string,
): Promise<unknown[]> {
  try {
    const query = policyId
      ? 'SELECT * FROM mission_sla_violations WHERE tenant_id = ? AND policy_id = ? ORDER BY created_at DESC'
      : 'SELECT * FROM mission_sla_violations WHERE tenant_id = ? ORDER BY created_at DESC';
    const stmt = policyId
      ? db.prepare(query).bind(tenantId, policyId)
      : db.prepare(query).bind(tenantId);
    const result = await stmt.all();
    return (result.results ?? []) as unknown[];
  } catch (err) {
    throw new Error(`getViolations failed: ${String(err)}`);
  }
}

// ── Admin ──────────────────────────────────────────────────────────────────

async function getAdminOverview(db: any): Promise<unknown> {
  try {
    const [policies, violations] = await Promise.all([
      db.prepare('SELECT COUNT(*) as total, status FROM mission_sla_policies GROUP BY status').all(),
      db.prepare('SELECT COUNT(*) as total, resolved FROM mission_sla_violations GROUP BY resolved').all(),
    ]);
    return {
      policies: (policies.results ?? []) as unknown[],
      violations: (violations.results ?? []) as unknown[],
    };
  } catch (err) {
    throw new Error(`getAdminOverview failed: ${String(err)}`);
  }
}

// ── Named export object ────────────────────────────────────────────────────

export const missionSlaComplianceService = {
  listPolicies,
  createPolicy,
  getViolations,
  getAdminOverview,
};
