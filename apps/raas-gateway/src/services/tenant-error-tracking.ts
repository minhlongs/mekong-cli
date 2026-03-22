/**
 * Tenant Error Tracking Service — error entries and alert rules per tenant
 * Methods: listErrors, createError, getRules, getAdminOverview
 */

// Row shapes for D1 queries — avoids generic type args on .first()/.all()
type ErrorEntryRow = {
  id: string; tenant_id: string; error_type: string; message: string;
  stack_trace: string | null; endpoint: string | null; status_code: number | null;
  created_at: string;
};

type ErrorRuleRow = {
  id: string; tenant_id: string; rule_name: string; error_pattern: string;
  action: string; notification_channel: string | null; created_at: string;
};

type AdminErrorTypeRow = {
  error_type: string; entry_count: number;
};

type AdminTenantCountRow = {
  tenants_with_errors: number;
};

export interface ErrorEntry {
  id: string;
  tenantId: string;
  errorType: string;
  message: string;
  stackTrace: string | null;
  endpoint: string | null;
  statusCode: number | null;
  createdAt: string;
}

export interface ErrorRule {
  id: string;
  tenantId: string;
  ruleName: string;
  errorPattern: string;
  action: string;
  notificationChannel: string | null;
  createdAt: string;
}

export interface AdminOverview {
  topErrorTypes: { errorType: string; entryCount: number }[];
  tenantsWithErrors: number;
  totalRules: number;
}

function mapEntry(row: ErrorEntryRow): ErrorEntry {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    errorType: row.error_type,
    message: row.message,
    stackTrace: row.stack_trace,
    endpoint: row.endpoint,
    statusCode: row.status_code,
    createdAt: row.created_at,
  };
}

function mapRule(row: ErrorRuleRow): ErrorRule {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    ruleName: row.rule_name,
    errorPattern: row.error_pattern,
    action: row.action,
    notificationChannel: row.notification_channel,
    createdAt: row.created_at,
  };
}

export const tenantErrorTrackingService = {
  /** List error entries for a tenant, most recent first */
  async listErrors(db: any, tenantId: string, limit = 50): Promise<{ success: boolean; data?: ErrorEntry[]; error?: string }> {
    try {
      const result = await db
        .prepare('SELECT * FROM tenant_error_entries WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?')
        .bind(tenantId, limit)
        .all();
      return { success: true, data: (result.results as ErrorEntryRow[]).map(mapEntry) };
    } catch (err) {
      return { success: false, error: `listErrors failed: ${String(err)}` };
    }
  },

  /** Create a new error entry for a tenant */
  async createError(
    db: any,
    tenantId: string,
    errorType: string,
    message: string,
    stackTrace?: string,
    endpoint?: string,
    statusCode?: number
  ): Promise<{ success: boolean; data?: ErrorEntry; error?: string }> {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO tenant_error_entries
             (id, tenant_id, error_type, message, stack_trace, endpoint, status_code, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(id, tenantId, errorType, message, stackTrace ?? null, endpoint ?? null, statusCode ?? null, now)
        .run();
      const row = (await db
        .prepare('SELECT * FROM tenant_error_entries WHERE id = ?')
        .bind(id)
        .first()) as ErrorEntryRow | null;
      if (!row) throw new Error('Row not found after insert');
      return { success: true, data: mapEntry(row) };
    } catch (err) {
      return { success: false, error: `createError failed: ${String(err)}` };
    }
  },

  /** List error rules for a tenant, ordered by created_at DESC */
  async getRules(db: any, tenantId: string): Promise<{ success: boolean; data?: ErrorRule[]; error?: string }> {
    try {
      const result = await db
        .prepare('SELECT * FROM tenant_error_rules WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { success: true, data: (result.results as ErrorRuleRow[]).map(mapRule) };
    } catch (err) {
      return { success: false, error: `getRules failed: ${String(err)}` };
    }
  },

  /** Admin overview: top error types + tenant/rule counts across all tenants */
  async getAdminOverview(db: any): Promise<{ success: boolean; data?: AdminOverview; error?: string }> {
    try {
      const [typesResult, tenantCountRow, ruleCountRow] = await Promise.all([
        db
          .prepare(
            `SELECT error_type, COUNT(id) as entry_count
             FROM tenant_error_entries
             GROUP BY error_type
             ORDER BY entry_count DESC
             LIMIT 10`
          )
          .all(),
        db
          .prepare('SELECT COUNT(DISTINCT tenant_id) as tenants_with_errors FROM tenant_error_entries')
          .first(),
        db
          .prepare('SELECT COUNT(*) as total FROM tenant_error_rules')
          .first(),
      ]);

      const types = typesResult.results as AdminErrorTypeRow[];
      const tenants = tenantCountRow as AdminTenantCountRow | null;
      const rules = ruleCountRow as { total: number } | null;

      return {
        success: true,
        data: {
          topErrorTypes: types.map(r => ({ errorType: r.error_type, entryCount: r.entry_count })),
          tenantsWithErrors: tenants?.tenants_with_errors ?? 0,
          totalRules: rules?.total ?? 0,
        },
      };
    } catch (err) {
      return { success: false, error: `getAdminOverview failed: ${String(err)}` };
    }
  },
};
