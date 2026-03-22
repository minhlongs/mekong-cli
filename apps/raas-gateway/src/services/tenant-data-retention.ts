/**
 * Tenant Data Retention Service
 * Manages per-tenant data retention policies and execution history
 */

/** List all active retention policies for a tenant */
async function listPolicies(db: any, tenantId: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, data_type, retention_days, action, status, created_at, updated_at
         FROM data_retention_policies
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[tenantDataRetentionService] listPolicies error:', err);
    return { success: false, error: 'Failed to list retention policies' };
  }
}

/** Create a new retention policy for a tenant */
async function createPolicy(
  db: any,
  tenantId: string,
  body: { data_type: string; retention_days?: number; action?: string }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const { data_type, retention_days = 365, action = 'archive' } = body;

    if (!data_type) {
      return { success: false, error: 'data_type is required' };
    }

    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO data_retention_policies (id, tenant_id, data_type, retention_days, action, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 'active', ?, ?)`
      )
      .bind(id, tenantId, data_type, retention_days, action, now, now)
      .run();

    return {
      success: true,
      data: { id, tenant_id: tenantId, data_type, retention_days, action, status: 'active', created_at: now, updated_at: now },
    };
  } catch (err) {
    console.error('[tenantDataRetentionService] createPolicy error:', err);
    return { success: false, error: 'Failed to create retention policy' };
  }
}

/** Get execution history for a tenant's retention policies */
async function getExecutions(db: any, tenantId: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, policy_id, records_processed, records_deleted, executed_at
         FROM data_retention_executions
         WHERE tenant_id = ?
         ORDER BY executed_at DESC
         LIMIT 100`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[tenantDataRetentionService] getExecutions error:', err);
    return { success: false, error: 'Failed to fetch retention executions' };
  }
}

/** Admin overview: policy counts and totals across all tenants */
async function getAdminOverview(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [policies, executions] = await Promise.all([
      db
        .prepare(
          `SELECT
             COUNT(*) as total_policies,
             SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_policies,
             COUNT(DISTINCT tenant_id) as tenants_with_policies
           FROM data_retention_policies`
        )
        .first(),
      db
        .prepare(
          `SELECT
             COUNT(*) as total_executions,
             SUM(records_processed) as total_records_processed,
             SUM(records_deleted) as total_records_deleted
           FROM data_retention_executions`
        )
        .first(),
    ]);

    return {
      success: true,
      data: {
        policies: policies ?? {},
        executions: executions ?? {},
      },
    };
  } catch (err) {
    console.error('[tenantDataRetentionService] getAdminOverview error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

export const tenantDataRetentionService = {
  listPolicies,
  createPolicy,
  getExecutions,
  getAdminOverview,
};
