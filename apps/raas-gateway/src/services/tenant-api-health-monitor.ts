/**
 * Tenant API Health Monitor Service
 * Manages per-tenant external endpoint monitors and stores check results in D1
 */

// ---- Types ----------------------------------------------------------------

export interface ApiHealthMonitor {
  id: string;
  tenant_id: string;
  monitor_name: string;
  endpoint_url: string;
  check_interval_ms: number;
  expected_status: number;
  status: string;
  last_checked_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiHealthMonitorResult {
  id: string;
  tenant_id: string;
  monitor_id: string;
  status_code: number | null;
  response_time_ms: number | null;
  healthy: number;
  checked_at: string;
}

export interface CreateMonitorInput {
  monitor_name: string;
  endpoint_url: string;
  check_interval_ms?: number;
  expected_status?: number;
}

// ---- Helpers ---------------------------------------------------------------

function generateId(): string {
  return crypto.randomUUID();
}

// ---- Service ---------------------------------------------------------------

/**
 * List all active monitors for a tenant
 */
async function listMonitors(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: ApiHealthMonitor[]; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT * FROM api_health_monitors WHERE tenant_id = ? ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();
    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[tenantApiHealthMonitorService] listMonitors error:', err);
    return { success: false, error: 'Failed to list monitors' };
  }
}

/**
 * Create a new health monitor for a tenant endpoint
 */
async function createMonitor(
  db: any,
  tenantId: string,
  input: CreateMonitorInput
): Promise<{ success: boolean; data?: ApiHealthMonitor; error?: string }> {
  try {
    const id = generateId();
    const now = new Date().toISOString();
    const checkInterval = input.check_interval_ms ?? 60000;
    const expectedStatus = input.expected_status ?? 200;

    await db
      .prepare(
        `INSERT INTO api_health_monitors
          (id, tenant_id, monitor_name, endpoint_url, check_interval_ms, expected_status, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)`
      )
      .bind(id, tenantId, input.monitor_name, input.endpoint_url, checkInterval, expectedStatus, now, now)
      .run();

    const created = await db
      .prepare(`SELECT * FROM api_health_monitors WHERE id = ?`)
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    console.error('[tenantApiHealthMonitorService] createMonitor error:', err);
    return { success: false, error: 'Failed to create monitor' };
  }
}

/**
 * Get recent check results for a specific monitor
 * Query param: limit (default 20, max 100)
 */
async function getResults(
  db: any,
  tenantId: string,
  monitorId: string,
  limit: number = 20
): Promise<{ success: boolean; data?: ApiHealthMonitorResult[]; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit), 100);

    // Verify monitor belongs to tenant before returning results
    const monitor = await db
      .prepare(`SELECT id FROM api_health_monitors WHERE id = ? AND tenant_id = ?`)
      .bind(monitorId, tenantId)
      .first();

    if (!monitor) {
      return { success: false, error: 'Monitor not found' };
    }

    const rows = await db
      .prepare(
        `SELECT * FROM api_health_monitor_results
         WHERE monitor_id = ? AND tenant_id = ?
         ORDER BY checked_at DESC LIMIT ?`
      )
      .bind(monitorId, tenantId, safeLimit)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[tenantApiHealthMonitorService] getResults error:', err);
    return { success: false, error: 'Failed to fetch results' };
  }
}

/**
 * Admin overview: monitor counts and recent unhealthy checks across all tenants
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: object; error?: string }> {
  try {
    const [monitorStats, unhealthy] = await Promise.all([
      db
        .prepare(
          `SELECT
            COUNT(*) as total_monitors,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_monitors,
            COUNT(DISTINCT tenant_id) as tenant_count
           FROM api_health_monitors`
        )
        .first(),
      db
        .prepare(
          `SELECT r.monitor_id, r.tenant_id, r.status_code, r.response_time_ms, r.checked_at,
                  m.monitor_name, m.endpoint_url
           FROM api_health_monitor_results r
           JOIN api_health_monitors m ON m.id = r.monitor_id
           WHERE r.healthy = 0
           ORDER BY r.checked_at DESC LIMIT 50`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        stats: monitorStats,
        recentUnhealthyChecks: unhealthy.results ?? [],
      },
    };
  } catch (err) {
    console.error('[tenantApiHealthMonitorService] getAdminOverview error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

// ---- Exports ---------------------------------------------------------------

export const tenantApiHealthMonitorService = {
  listMonitors,
  createMonitor,
  getResults,
  getAdminOverview,
};
