// Mission Retry Policies Service — manage retry configurations and attempt tracking

/** List all active retry policies for a tenant */
export async function listPolicies(db: any, tenantId: string): Promise<unknown[]> {
  try {
    const rows = await db.prepare(
      `SELECT * FROM retry_policies WHERE tenant_id = ? ORDER BY created_at DESC`
    ).bind(tenantId).all();
    return rows.results;
  } catch (e: unknown) {
    throw new Error(`listPolicies failed: ${(e as Error).message}`);
  }
}

/** Create a new retry policy for a tenant */
export async function createPolicy(
  db: any,
  tenantId: string,
  data: {
    policy_name: string;
    max_retries?: number;
    backoff_type?: string;
    initial_delay_ms?: number;
    max_delay_ms?: number;
  }
): Promise<unknown> {
  try {
    const id = crypto.randomUUID();
    return await db.prepare(
      `INSERT INTO retry_policies
        (id, tenant_id, policy_name, max_retries, backoff_type, initial_delay_ms, max_delay_ms)
       VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(
      id,
      tenantId,
      data.policy_name,
      data.max_retries ?? 3,
      data.backoff_type ?? 'exponential',
      data.initial_delay_ms ?? 1000,
      data.max_delay_ms ?? 60000
    ).first();
  } catch (e: unknown) {
    throw new Error(`createPolicy failed: ${(e as Error).message}`);
  }
}

/** List all retry attempts for a tenant */
export async function getAttempts(db: any, tenantId: string): Promise<unknown[]> {
  try {
    const rows = await db.prepare(
      `SELECT * FROM retry_attempts WHERE tenant_id = ? ORDER BY created_at DESC`
    ).bind(tenantId).all();
    return rows.results;
  } catch (e: unknown) {
    throw new Error(`getAttempts failed: ${(e as Error).message}`);
  }
}

/** Admin overview: policy and attempt counts across all tenants */
export async function getAdminOverview(db: any): Promise<unknown> {
  try {
    const [totalPolicies, activePolicies, totalAttempts, pending, succeeded, failed] =
      await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM retry_policies`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM retry_policies WHERE is_active = 1`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM retry_attempts`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM retry_attempts WHERE status = 'pending'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM retry_attempts WHERE status = 'succeeded'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM retry_attempts WHERE status = 'failed'`).first(),
      ]);

    return {
      policies: {
        total: (totalPolicies as any)?.count ?? 0,
        active: (activePolicies as any)?.count ?? 0,
      },
      attempts: {
        total: (totalAttempts as any)?.count ?? 0,
        pending: (pending as any)?.count ?? 0,
        succeeded: (succeeded as any)?.count ?? 0,
        failed: (failed as any)?.count ?? 0,
      },
    };
  } catch (e: unknown) {
    throw new Error(`getAdminOverview failed: ${(e as Error).message}`);
  }
}

export const missionRetryPoliciesService = {
  listPolicies,
  createPolicy,
  getAttempts,
  getAdminOverview,
};
