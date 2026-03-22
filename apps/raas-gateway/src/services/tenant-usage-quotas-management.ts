/**
 * Tenant Usage Quotas Management Service
 * CRUD for usage_quotas and usage_quota_alerts tables
 */

interface QuotaRow {
  id: string;
  tenant_id: string;
  resource_type: string;
  quota_limit: number;
  current_usage: number;
  period: string;
  reset_at: string | null;
  created_at: string;
  updated_at: string;
}

interface AlertRow {
  id: string;
  tenant_id: string;
  quota_id: string;
  alert_threshold: number;
  notification_sent: number;
  triggered_at: string | null;
  created_at: string;
}

interface AdminOverviewRow {
  tenant_id: string;
  total_quotas: number;
  over_limit: number;
  alerts_pending: number;
}

interface ServiceResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

/** List all quotas for a tenant */
async function listQuotas(db: any, tenantId: string): Promise<ServiceResult> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, resource_type, quota_limit, current_usage,
                period, reset_at, created_at, updated_at
         FROM usage_quotas
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    console.error('[tenantUsageQuotasManagementService.listQuotas] error:', err);
    return { success: false, error: 'Failed to list quotas' };
  }
}

/** Create a new quota for a tenant */
async function createQuota(
  db: any,
  tenantId: string,
  resourceType: string,
  quotaLimit: number,
  period: string = 'monthly',
  resetAt?: string
): Promise<ServiceResult> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO usage_quotas
           (id, tenant_id, resource_type, quota_limit, current_usage, period, reset_at, created_at, updated_at)
         VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, resourceType, quotaLimit, period, resetAt ?? null, now, now)
      .run();

    const row = await db
      .prepare(`SELECT * FROM usage_quotas WHERE id = ?`)
      .bind(id)
      .first();

    return { success: true, data: row };
  } catch (err) {
    console.error('[tenantUsageQuotasManagementService.createQuota] error:', err);
    return { success: false, error: 'Failed to create quota' };
  }
}

/** Get all alerts for a tenant */
async function getAlerts(db: any, tenantId: string): Promise<ServiceResult> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, quota_id, alert_threshold, notification_sent,
                triggered_at, created_at
         FROM usage_quota_alerts
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    console.error('[tenantUsageQuotasManagementService.getAlerts] error:', err);
    return { success: false, error: 'Failed to fetch alerts' };
  }
}

/** Admin overview — usage and alert counts per tenant */
async function getAdminOverview(db: any): Promise<ServiceResult> {
  try {
    const result = await db
      .prepare(
        `SELECT
           q.tenant_id,
           COUNT(q.id)                                                        AS total_quotas,
           SUM(CASE WHEN q.current_usage >= q.quota_limit THEN 1 ELSE 0 END) AS over_limit,
           COUNT(a.id)                                                        AS alerts_pending
         FROM usage_quotas q
         LEFT JOIN usage_quota_alerts a
           ON a.quota_id = q.id AND a.notification_sent = 0
         GROUP BY q.tenant_id
         ORDER BY over_limit DESC`
      )
      .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    console.error('[tenantUsageQuotasManagementService.getAdminOverview] error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

export const tenantUsageQuotasManagementService = {
  listQuotas,
  createQuota,
  getAlerts,
  getAdminOverview,
};
