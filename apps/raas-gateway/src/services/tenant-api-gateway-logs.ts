/**
 * Tenant API Gateway Logs Service
 * CRUD for api_gateway_logs and api_gateway_log_filters tables.
 * All methods: db as first param (any), no generic type args, try/catch.
 */

// ---- listLogs ---------------------------------------------------------------

/**
 * List gateway logs for a tenant, newest first.
 * Optional query params: limit (default 50, max 200), status_code, method.
 */
async function listLogs(
  db: any,
  tenantId: string,
  opts: { limit?: number; status_code?: number; method?: string } = {}
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const limit = Math.min(opts.limit ?? 50, 200);
    let query = `SELECT * FROM api_gateway_logs WHERE tenant_id = ?`;
    const params: any[] = [tenantId];

    if (opts.status_code !== undefined) {
      query += ` AND status_code = ?`;
      params.push(opts.status_code);
    }
    if (opts.method) {
      query += ` AND method = ?`;
      params.push(opts.method.toUpperCase());
    }

    query += ` ORDER BY created_at DESC LIMIT ?`;
    params.push(limit);

    const result = await db.prepare(query).bind(...params).all();
    return { success: true, data: result.results };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to list gateway logs' };
  }
}

// ---- createLog --------------------------------------------------------------

/**
 * Insert a single gateway log entry.
 */
async function createLog(
  db: any,
  payload: {
    id: string;
    tenant_id: string;
    request_id?: string;
    method: string;
    path: string;
    status_code?: number;
    response_time_ms?: number;
    ip_address?: string;
    user_agent?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    await db
      .prepare(
        `INSERT INTO api_gateway_logs
          (id, tenant_id, request_id, method, path, status_code, response_time_ms, ip_address, user_agent)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        payload.id,
        payload.tenant_id,
        payload.request_id ?? null,
        payload.method,
        payload.path,
        payload.status_code ?? null,
        payload.response_time_ms ?? null,
        payload.ip_address ?? null,
        payload.user_agent ?? null
      )
      .run();

    return { success: true, data: { id: payload.id } };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to create gateway log' };
  }
}

// ---- getFilters -------------------------------------------------------------

/**
 * Retrieve all log filters for a tenant.
 */
async function getFilters(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT * FROM api_gateway_log_filters WHERE tenant_id = ? ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: result.results };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to get log filters' };
  }
}

// ---- getAdminOverview -------------------------------------------------------

/**
 * Platform-wide admin overview: total logs, error rate, top paths, tenant breakdown.
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [totals, topPaths, tenantBreakdown] = await Promise.all([
      db
        .prepare(
          `SELECT
            COUNT(*) as total_requests,
            SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as server_errors,
            SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as client_errors,
            AVG(response_time_ms) as avg_response_time_ms
           FROM api_gateway_logs`
        )
        .first(),
      db
        .prepare(
          `SELECT path, COUNT(*) as count
           FROM api_gateway_logs
           GROUP BY path
           ORDER BY count DESC
           LIMIT 10`
        )
        .all(),
      db
        .prepare(
          `SELECT tenant_id, COUNT(*) as request_count
           FROM api_gateway_logs
           GROUP BY tenant_id
           ORDER BY request_count DESC
           LIMIT 20`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        totals,
        topPaths: topPaths.results,
        tenantBreakdown: tenantBreakdown.results,
      },
    };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to get admin overview' };
  }
}

// ---- Export -----------------------------------------------------------------

export const tenantApiGatewayLogsService = {
  listLogs,
  createLog,
  getFilters,
  getAdminOverview,
};
