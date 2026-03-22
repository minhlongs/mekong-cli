/**
 * Tenant API Access Logs Service
 * List logs, create log entries, get export jobs, and admin overview
 */

// List access logs for a tenant with optional pagination
async function listLogs(
  db: any,
  tenantId: string,
  limit = 50,
  offset = 0
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit), 200);
    const rows = await db
      .prepare(
        `SELECT id, user_id, method, path, status_code, ip_address, user_agent, country, created_at
         FROM api_access_logs
         WHERE tenant_id = ?
         ORDER BY created_at DESC
         LIMIT ? OFFSET ?`
      )
      .bind(tenantId, safeLimit, offset)
      .all();

    const countRow = await db
      .prepare('SELECT COUNT(*) as total FROM api_access_logs WHERE tenant_id = ?')
      .bind(tenantId)
      .first();

    return {
      success: true,
      data: {
        logs: rows.results ?? [],
        total: countRow?.total ?? 0,
        limit: safeLimit,
        offset,
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Create a single access log entry for a tenant
async function createLog(
  db: any,
  tenantId: string,
  entry: {
    userId?: string;
    method: string;
    path: string;
    statusCode?: number;
    ipAddress?: string;
    userAgent?: string;
    country?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO api_access_logs
           (id, tenant_id, user_id, method, path, status_code, ip_address, user_agent, country)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        entry.userId ?? null,
        entry.method,
        entry.path,
        entry.statusCode ?? null,
        entry.ipAddress ?? null,
        entry.userAgent ?? null,
        entry.country ?? null
      )
      .run();

    return { success: true, data: { id } };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Get export jobs for a tenant
async function getExports(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, format, date_from, date_to, status, file_url, created_at
         FROM api_access_log_exports
         WHERE tenant_id = ?
         ORDER BY created_at DESC
         LIMIT 50`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Create an export job for a tenant
async function createExport(
  db: any,
  tenantId: string,
  format: string,
  dateFrom?: string,
  dateTo?: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO api_access_log_exports (id, tenant_id, format, date_from, date_to, status)
         VALUES (?, ?, ?, ?, ?, 'pending')`
      )
      .bind(id, tenantId, format, dateFrom ?? null, dateTo ?? null)
      .run();

    return { success: true, data: { id, status: 'pending' } };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Admin overview — aggregate stats across all tenants
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [totals, topTenants, recentErrors] = await Promise.all([
      db
        .prepare(
          `SELECT
             COUNT(*) as total_requests,
             COUNT(DISTINCT tenant_id) as active_tenants,
             SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as server_errors,
             SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as client_errors
           FROM api_access_logs
           WHERE created_at >= datetime('now', '-24 hours')`
        )
        .first(),

      db
        .prepare(
          `SELECT tenant_id, COUNT(*) as requests
           FROM api_access_logs
           WHERE created_at >= datetime('now', '-24 hours')
           GROUP BY tenant_id
           ORDER BY requests DESC
           LIMIT 10`
        )
        .all(),

      db
        .prepare(
          `SELECT tenant_id, method, path, status_code, created_at
           FROM api_access_logs
           WHERE status_code >= 500
             AND created_at >= datetime('now', '-1 hours')
           ORDER BY created_at DESC
           LIMIT 20`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        last24h: totals,
        topTenants: topTenants.results ?? [],
        recentServerErrors: recentErrors.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const tenantApiAccessLogsService = {
  listLogs,
  createLog,
  getExports,
  createExport,
  getAdminOverview,
};
