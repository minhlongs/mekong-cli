/**
 * Tenant API Rate Quotas Service — CRUD for api_rate_quotas + usage aggregation
 */

export interface ApiRateQuota {
  id: string;
  tenant_id: string;
  endpoint_pattern: string;
  max_requests_per_minute: number;
  max_requests_per_hour: number;
  max_requests_per_day: number;
  burst_limit: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ApiRateQuotaUsage {
  id: string;
  tenant_id: string;
  quota_id: string;
  period: string;
  request_count: number;
  blocked_count: number;
  recorded_at: string;
}

export interface CreateQuotaInput {
  endpoint_pattern: string;
  max_requests_per_minute?: number;
  max_requests_per_hour?: number;
  max_requests_per_day?: number;
  burst_limit?: number;
}

// ---------------------------------------------------------------------------
// List quotas for a tenant
// ---------------------------------------------------------------------------

export async function listQuotas(db: any, tenantId: string): Promise<ApiRateQuota[]> {
  try {
    const { results } = await db
      .prepare('SELECT * FROM api_rate_quotas WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC')
      .bind(tenantId, 'active')
      .all();
    return results as ApiRateQuota[];
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'DB error';
    throw new Error(`listQuotas failed: ${msg}`);
  }
}

// ---------------------------------------------------------------------------
// Create a new quota for a tenant
// ---------------------------------------------------------------------------

export async function createQuota(db: any, tenantId: string, input: CreateQuotaInput): Promise<ApiRateQuota> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  const rpm = input.max_requests_per_minute ?? 60;
  const rph = input.max_requests_per_hour ?? 1000;
  const rpd = input.max_requests_per_day ?? 10000;
  const burst = input.burst_limit ?? 100;

  try {
    await db
      .prepare(
        `INSERT INTO api_rate_quotas
           (id, tenant_id, endpoint_pattern, max_requests_per_minute, max_requests_per_hour,
            max_requests_per_day, burst_limit, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)`
      )
      .bind(id, tenantId, input.endpoint_pattern, rpm, rph, rpd, burst, now, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM api_rate_quotas WHERE id = ?')
      .bind(id)
      .first();
    return row as ApiRateQuota;
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'DB error';
    throw new Error(`createQuota failed: ${msg}`);
  }
}

// ---------------------------------------------------------------------------
// Get usage stats for a tenant (optionally filtered by quota_id)
// ---------------------------------------------------------------------------

export async function getUsage(db: any, tenantId: string, quotaId?: string): Promise<ApiRateQuotaUsage[]> {
  try {
    let stmt;
    if (quotaId) {
      stmt = db
        .prepare('SELECT * FROM api_rate_quota_usage WHERE tenant_id = ? AND quota_id = ? ORDER BY recorded_at DESC LIMIT 100')
        .bind(tenantId, quotaId);
    } else {
      stmt = db
        .prepare('SELECT * FROM api_rate_quota_usage WHERE tenant_id = ? ORDER BY recorded_at DESC LIMIT 100')
        .bind(tenantId);
    }
    const { results } = await stmt.all();
    return results as ApiRateQuotaUsage[];
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'DB error';
    throw new Error(`getUsage failed: ${msg}`);
  }
}

// ---------------------------------------------------------------------------
// Admin overview — quota counts + usage totals across all tenants
// ---------------------------------------------------------------------------

export async function getAdminOverview(db: any): Promise<Record<string, unknown>> {
  try {
    const totalQuotas = await db
      .prepare('SELECT COUNT(*) as count FROM api_rate_quotas WHERE status = ?')
      .bind('active')
      .first();

    const totalTenants = await db
      .prepare('SELECT COUNT(DISTINCT tenant_id) as count FROM api_rate_quotas')
      .first();

    const usageSummary = await db
      .prepare(
        `SELECT tenant_id, SUM(request_count) as total_requests, SUM(blocked_count) as total_blocked
         FROM api_rate_quota_usage
         GROUP BY tenant_id
         ORDER BY total_requests DESC
         LIMIT 20`
      )
      .all();

    return {
      active_quotas: (totalQuotas as any)?.count ?? 0,
      tenants_with_quotas: (totalTenants as any)?.count ?? 0,
      top_tenants_by_usage: (usageSummary.results ?? []) as unknown[],
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'DB error';
    throw new Error(`getAdminOverview failed: ${msg}`);
  }
}
