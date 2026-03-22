/**
 * Tenant Usage Analytics Service — detailed API usage tracking and period summaries per tenant
 * Methods: listAnalytics, createAnalytic, getSummaries, getAdminOverview
 */

// Row shapes for D1 queries — avoids generic type args on .first()/.all()
type AnalyticRow = {
  id: string; tenant_id: string; endpoint: string; method: string;
  status_code: number | null; response_time_ms: number | null;
  request_size: number | null; response_size: number | null; created_at: string;
};

type SummaryRow = {
  id: string; tenant_id: string; period: string; total_requests: number;
  avg_response_time_ms: number | null; error_count: number; created_at: string;
};

type AdminOverviewRow = {
  tenant_id: string; total_requests: number; error_count: number;
};

export interface UsageAnalytic {
  id: string;
  tenantId: string;
  endpoint: string;
  method: string;
  statusCode: number | null;
  responseTimeMs: number | null;
  requestSize: number | null;
  responseSize: number | null;
  createdAt: string;
}

export interface UsageSummary {
  id: string;
  tenantId: string;
  period: string;
  totalRequests: number;
  avgResponseTimeMs: number | null;
  errorCount: number;
  createdAt: string;
}

export interface AdminOverview {
  tenants: { tenantId: string; totalRequests: number; errorCount: number }[];
  totalTenants: number;
  grandTotalRequests: number;
}

function mapAnalytic(row: AnalyticRow): UsageAnalytic {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    endpoint: row.endpoint,
    method: row.method,
    statusCode: row.status_code,
    responseTimeMs: row.response_time_ms,
    requestSize: row.request_size,
    responseSize: row.response_size,
    createdAt: row.created_at,
  };
}

function mapSummary(row: SummaryRow): UsageSummary {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    period: row.period,
    totalRequests: row.total_requests,
    avgResponseTimeMs: row.avg_response_time_ms,
    errorCount: row.error_count,
    createdAt: row.created_at,
  };
}

export const tenantUsageAnalyticsService = {
  /** List recent analytics records for a tenant, most recent first */
  async listAnalytics(
    db: any,
    tenantId: string,
    limit = 50
  ): Promise<{ success: boolean; data?: UsageAnalytic[]; error?: string }> {
    try {
      const result = await db
        .prepare(
          'SELECT * FROM api_usage_analytics WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
        )
        .bind(tenantId, limit)
        .all();
      return { success: true, data: (result.results as AnalyticRow[]).map(mapAnalytic) };
    } catch (err) {
      return { success: false, error: `listAnalytics failed: ${String(err)}` };
    }
  },

  /** Insert a single API usage analytic record for a tenant */
  async createAnalytic(
    db: any,
    tenantId: string,
    endpoint: string,
    method: string,
    statusCode?: number,
    responseTimeMs?: number,
    requestSize?: number,
    responseSize?: number
  ): Promise<{ success: boolean; data?: UsageAnalytic; error?: string }> {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO api_usage_analytics
             (id, tenant_id, endpoint, method, status_code, response_time_ms, request_size, response_size, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id, tenantId, endpoint, method,
          statusCode ?? null, responseTimeMs ?? null,
          requestSize ?? null, responseSize ?? null, now
        )
        .run();
      const row = (await db
        .prepare('SELECT * FROM api_usage_analytics WHERE id = ?')
        .bind(id)
        .first()) as AnalyticRow | null;
      if (!row) throw new Error('Row not found after insert');
      return { success: true, data: mapAnalytic(row) };
    } catch (err) {
      return { success: false, error: `createAnalytic failed: ${String(err)}` };
    }
  },

  /** Get period summaries for a tenant, most recent first */
  async getSummaries(
    db: any,
    tenantId: string,
    limit = 30
  ): Promise<{ success: boolean; data?: UsageSummary[]; error?: string }> {
    try {
      const result = await db
        .prepare(
          'SELECT * FROM api_usage_summaries WHERE tenant_id = ? ORDER BY period DESC LIMIT ?'
        )
        .bind(tenantId, limit)
        .all();
      return { success: true, data: (result.results as SummaryRow[]).map(mapSummary) };
    } catch (err) {
      return { success: false, error: `getSummaries failed: ${String(err)}` };
    }
  },

  /** Admin overview: per-tenant request totals and error counts across all tenants */
  async getAdminOverview(
    db: any
  ): Promise<{ success: boolean; data?: AdminOverview; error?: string }> {
    try {
      const [tenantsResult, grandTotalRow] = await Promise.all([
        db
          .prepare(
            `SELECT tenant_id,
               COUNT(*) AS total_requests,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS error_count
             FROM api_usage_analytics
             GROUP BY tenant_id
             ORDER BY total_requests DESC
             LIMIT 100`
          )
          .all(),
        db
          .prepare('SELECT COUNT(*) AS total FROM api_usage_analytics')
          .first(),
      ]);

      const rows = tenantsResult.results as AdminOverviewRow[];
      const grandTotal = (grandTotalRow as { total: number } | null)?.total ?? 0;

      return {
        success: true,
        data: {
          tenants: rows.map(r => ({
            tenantId: r.tenant_id,
            totalRequests: r.total_requests,
            errorCount: r.error_count,
          })),
          totalTenants: rows.length,
          grandTotalRequests: grandTotal,
        },
      };
    } catch (err) {
      return { success: false, error: `getAdminOverview failed: ${String(err)}` };
    }
  },
};
