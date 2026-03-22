/**
 * Tenant API Rate Policies Service
 * CRUD for per-tenant endpoint rate policy configs and violation records
 */

// Policy record shape from D1
interface PolicyRow {
  id: string;
  tenant_id: string;
  policy_name: string;
  endpoint_pattern: string;
  requests_per_minute: number;
  burst_size: number;
  status: string;
  created_at: string;
  updated_at: string;
}

// Violation record shape from D1
interface ViolationRow {
  id: string;
  tenant_id: string;
  policy_id: string;
  violated_at: string;
  request_count: number | null;
  endpoint: string | null;
  created_at: string;
}

// Input for policy creation
interface CreatePolicyInput {
  policy_name: string;
  endpoint_pattern: string;
  requests_per_minute?: number;
  burst_size?: number;
  status?: string;
}

// Admin overview aggregate row
interface AdminOverviewRow {
  tenant_id: string;
  policy_count: number;
  violation_count: number;
}

/**
 * List all active rate policies for a tenant
 */
async function listPolicies(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: PolicyRow[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, policy_name, endpoint_pattern,
                requests_per_minute, burst_size, status, created_at, updated_at
         FROM api_rate_policies
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: (result.results ?? []) as PolicyRow[] };
  } catch (err) {
    console.error('[tenantApiRatePoliciesService] listPolicies error:', err);
    return { success: false, error: 'Failed to list rate policies' };
  }
}

/**
 * Create a new rate policy for a tenant
 */
async function createPolicy(
  db: any,
  tenantId: string,
  input: CreatePolicyInput
): Promise<{ success: boolean; data?: PolicyRow; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const rpm = input.requests_per_minute ?? 60;
    const burst = input.burst_size ?? 10;
    const status = input.status ?? 'active';

    await db
      .prepare(
        `INSERT INTO api_rate_policies
           (id, tenant_id, policy_name, endpoint_pattern, requests_per_minute, burst_size, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, input.policy_name, input.endpoint_pattern, rpm, burst, status, now, now)
      .run();

    const created = await db
      .prepare(`SELECT * FROM api_rate_policies WHERE id = ?`)
      .bind(id)
      .first() as PolicyRow | null;

    return { success: true, data: created ?? undefined };
  } catch (err) {
    console.error('[tenantApiRatePoliciesService] createPolicy error:', err);
    return { success: false, error: 'Failed to create rate policy' };
  }
}

/**
 * Get violation records for a tenant (most recent first, limit 100)
 */
async function getViolations(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: ViolationRow[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, policy_id, violated_at, request_count, endpoint, created_at
         FROM api_rate_policy_violations
         WHERE tenant_id = ?
         ORDER BY violated_at DESC
         LIMIT 100`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: (result.results ?? []) as ViolationRow[] };
  } catch (err) {
    console.error('[tenantApiRatePoliciesService] getViolations error:', err);
    return { success: false, error: 'Failed to fetch violations' };
  }
}

/**
 * Admin overview: policy and violation counts grouped by tenant
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: AdminOverviewRow[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT
           p.tenant_id,
           COUNT(DISTINCT p.id) as policy_count,
           COUNT(DISTINCT v.id) as violation_count
         FROM api_rate_policies p
         LEFT JOIN api_rate_policy_violations v ON v.tenant_id = p.tenant_id
         GROUP BY p.tenant_id
         ORDER BY violation_count DESC`
      )
      .all();

    return { success: true, data: (result.results ?? []) as AdminOverviewRow[] };
  } catch (err) {
    console.error('[tenantApiRatePoliciesService] getAdminOverview error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

export const tenantApiRatePoliciesService = {
  listPolicies,
  createPolicy,
  getViolations,
  getAdminOverview,
};
