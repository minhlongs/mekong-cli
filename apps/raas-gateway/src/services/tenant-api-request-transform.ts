/**
 * Tenant API Request Transform Service
 * CRUD for transform rules and log retrieval per tenant; admin overview across all tenants
 */

export const tenantApiRequestTransformService = {
  /**
   * List all transforms for a tenant
   */
  async listTransforms(db: any, tenantId: string): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const rows = await db
        .prepare(
          `SELECT id, tenant_id, transform_name, source_path, target_path,
                  transform_type, transform_config, enabled, created_at, updated_at
           FROM api_request_transforms
           WHERE tenant_id = ?
           ORDER BY created_at DESC`
        )
        .bind(tenantId)
        .all();
      return { success: true, data: rows.results ?? [] };
    } catch (err) {
      console.error('[tenantApiRequestTransformService.listTransforms]', err);
      return { success: false, error: 'Failed to list transforms' };
    }
  },

  /**
   * Create a new transform rule for a tenant
   */
  async createTransform(
    db: any,
    tenantId: string,
    body: {
      transform_name: string;
      source_path: string;
      target_path: string;
      transform_type?: string;
      transform_config?: string;
      enabled?: number;
    }
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      const transformType = body.transform_type ?? 'map';
      const enabled = body.enabled ?? 1;

      await db
        .prepare(
          `INSERT INTO api_request_transforms
             (id, tenant_id, transform_name, source_path, target_path, transform_type, transform_config, enabled, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          body.transform_name,
          body.source_path,
          body.target_path,
          transformType,
          body.transform_config ?? null,
          enabled,
          now,
          now
        )
        .run();

      return {
        success: true,
        data: {
          id,
          tenant_id: tenantId,
          transform_name: body.transform_name,
          source_path: body.source_path,
          target_path: body.target_path,
          transform_type: transformType,
          transform_config: body.transform_config ?? null,
          enabled,
          created_at: now,
          updated_at: now,
        },
      };
    } catch (err) {
      console.error('[tenantApiRequestTransformService.createTransform]', err);
      return { success: false, error: 'Failed to create transform' };
    }
  },

  /**
   * Get transform application logs for a tenant
   * Optional limit param (default 50, max 200)
   */
  async getLogs(
    db: any,
    tenantId: string,
    limit = 50
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const safeLimit = Math.min(Math.max(1, limit), 200);
      const rows = await db
        .prepare(
          `SELECT id, tenant_id, transform_id, request_path, applied, created_at
           FROM api_request_transform_logs
           WHERE tenant_id = ?
           ORDER BY created_at DESC
           LIMIT ?`
        )
        .bind(tenantId, safeLimit)
        .all();
      return { success: true, data: rows.results ?? [] };
    } catch (err) {
      console.error('[tenantApiRequestTransformService.getLogs]', err);
      return { success: false, error: 'Failed to fetch transform logs' };
    }
  },

  /**
   * Admin overview: transform and log counts across all tenants
   */
  async getAdminOverview(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const [transformStats, logStats, recentLogs] = await Promise.all([
        db
          .prepare(
            `SELECT tenant_id,
                    COUNT(*) as total_transforms,
                    SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as active_transforms
             FROM api_request_transforms
             GROUP BY tenant_id
             ORDER BY total_transforms DESC
             LIMIT 50`
          )
          .all(),
        db
          .prepare(
            `SELECT COUNT(*) as total_logs,
                    SUM(CASE WHEN applied = 1 THEN 1 ELSE 0 END) as applied_count
             FROM api_request_transform_logs
             WHERE created_at >= datetime('now', '-7 days')`
          )
          .first(),
        db
          .prepare(
            `SELECT tenant_id, transform_id, request_path, applied, created_at
             FROM api_request_transform_logs
             ORDER BY created_at DESC
             LIMIT 20`
          )
          .all(),
      ]);

      return {
        success: true,
        data: {
          tenantStats: transformStats.results ?? [],
          weeklyLogs: {
            total: logStats?.total_logs ?? 0,
            applied: logStats?.applied_count ?? 0,
          },
          recentLogs: recentLogs.results ?? [],
        },
      };
    } catch (err) {
      console.error('[tenantApiRequestTransformService.getAdminOverview]', err);
      return { success: false, error: 'Failed to fetch admin overview' };
    }
  },
};
