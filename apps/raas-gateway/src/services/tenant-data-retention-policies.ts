/**
 * Tenant Data Retention Policies Service — CRUD and overview for per-tenant retention rules
 */

export interface DataRetentionPolicy {
  id: string;
  tenant_id: string;
  entity_type: string;
  retention_days: number;
  action: string;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface DataRetentionRun {
  id: string;
  tenant_id: string;
  policy_id: string;
  status: string;
  records_processed: number;
  records_affected: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface CreatePolicyInput {
  entity_type: string;
  retention_days: number;
  action?: string;
  is_active?: number;
}

export interface AdminOverview {
  total_policies: number;
  active_policies: number;
  total_runs: number;
  pending_runs: number;
}

/**
 * List all data retention policies for a tenant
 */
export async function listPolicies(
  db: any,
  tenantId: string
): Promise<{ policies: DataRetentionPolicy[] }> {
  try {
    const result = await db
      .prepare('SELECT * FROM data_retention_policies WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return { policies: (result.results ?? []) as DataRetentionPolicy[] };
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to list policies';
    return { policies: [] };
  }
}

/**
 * Create a new data retention policy for a tenant
 */
export async function createPolicy(
  db: any,
  tenantId: string,
  data: CreatePolicyInput
): Promise<{ policy: DataRetentionPolicy | null; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const action = data.action ?? 'archive';
    const isActive = data.is_active ?? 1;

    await db
      .prepare(
        `INSERT INTO data_retention_policies (id, tenant_id, entity_type, retention_days, action, is_active)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, data.entity_type, data.retention_days, action, isActive)
      .run();

    const row = await db
      .prepare('SELECT * FROM data_retention_policies WHERE id = ?')
      .bind(id)
      .first();

    return { policy: row as DataRetentionPolicy };
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to create policy';
    return { policy: null, error: msg };
  }
}

/**
 * List all data retention runs for a tenant
 */
export async function getRuns(
  db: any,
  tenantId: string
): Promise<{ runs: DataRetentionRun[] }> {
  try {
    const result = await db
      .prepare('SELECT * FROM data_retention_runs WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return { runs: (result.results ?? []) as DataRetentionRun[] };
  } catch (err) {
    return { runs: [] };
  }
}

/**
 * Admin overview — aggregate counts of policies and runs across all tenants
 */
export async function getAdminOverview(db: any): Promise<{ overview: AdminOverview; error?: string }> {
  try {
    const [policyCounts, runCounts] = await Promise.all([
      db
        .prepare('SELECT COUNT(*) as total, SUM(is_active) as active FROM data_retention_policies')
        .first(),
      db
        .prepare(`SELECT COUNT(*) as total, SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending FROM data_retention_runs`)
        .first(),
    ]);

    return {
      overview: {
        total_policies: (policyCounts?.total as number) ?? 0,
        active_policies: (policyCounts?.active as number) ?? 0,
        total_runs: (runCounts?.total as number) ?? 0,
        pending_runs: (runCounts?.pending as number) ?? 0,
      },
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to get admin overview';
    return {
      overview: { total_policies: 0, active_policies: 0, total_runs: 0, pending_runs: 0 },
      error: msg,
    };
  }
}

export const dataRetentionPoliciesService = {
  listPolicies,
  createPolicy,
  getRuns,
  getAdminOverview,
};
