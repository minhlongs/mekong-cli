/**
 * Tenant API Versioning Config Service
 * Manages per-tenant API version configurations and version mappings
 */

export const tenantApiVersioningConfigService = {
  /** List all API versioning configs for a tenant */
  async listConfigs(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare('SELECT * FROM api_versioning_configs WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { success: true, data: results };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  },

  /** Create a new API versioning config for a tenant */
  async createConfig(db: any, tenantId: string, data: Record<string, any>) {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO api_versioning_configs
           (id, tenant_id, api_version, deprecation_policy, sunset_date, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.api_version ?? 'v1',
          data.deprecation_policy ?? null,
          data.sunset_date ?? null,
          now,
          now
        )
        .run();
      const row = await db
        .prepare('SELECT * FROM api_versioning_configs WHERE id = ?')
        .bind(id)
        .first();
      return { success: true, data: row };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  },

  /** List all API version mappings for a tenant */
  async getMappings(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare('SELECT * FROM api_version_mappings WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { success: true, data: results };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  },

  /** Admin overview: config and mapping counts across all tenants */
  async getAdminOverview(db: any) {
    try {
      const configCount = await db
        .prepare('SELECT COUNT(*) as total FROM api_versioning_configs')
        .first();
      const mappingCount = await db
        .prepare('SELECT COUNT(*) as total FROM api_version_mappings')
        .first();
      const tenantCount = await db
        .prepare('SELECT COUNT(DISTINCT tenant_id) as total FROM api_versioning_configs')
        .first();
      return {
        success: true,
        data: {
          total_configs: configCount?.total ?? 0,
          total_mappings: mappingCount?.total ?? 0,
          total_tenants: tenantCount?.total ?? 0,
        },
      };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  },
};
