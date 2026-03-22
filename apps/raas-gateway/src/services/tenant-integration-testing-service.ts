/**
 * Tenant Integration Testing Service — manage test configs and results per tenant
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export interface IntegrationTestConfig {
  id: string;
  tenant_id: string;
  test_name: string;
  target_endpoint: string;
  method: string;
  expected_status: number;
  headers_json: string;
  body_json: string | null;
  schedule_cron: string | null;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface IntegrationTestResult {
  id: string;
  tenant_id: string;
  config_id: string;
  status: string;
  response_status: number | null;
  response_time_ms: number | null;
  error_message: string | null;
  executed_at: string;
}

export interface CreateConfigData {
  test_name: string;
  target_endpoint: string;
  method?: string;
  expected_status?: number;
  headers_json?: string;
  body_json?: string;
  schedule_cron?: string;
}

type AdminOverviewRow = { tenant_id: string; config_count: number; result_count: number; pass_count: number };

// ── Service ────────────────────────────────────────────────────────────────────

export const tenantIntegrationTestingService = {

  /** List all active test configs for tenant */
  async listConfigs(db: any, tenantId: string) {
    try {
      const result = await db.prepare(
        `SELECT * FROM integration_test_configs WHERE tenant_id = ? ORDER BY created_at DESC`
      ).bind(tenantId).all();
      return (result.results ?? []) as IntegrationTestConfig[];
    } catch (err) {
      throw new Error(`listConfigs failed: ${err}`);
    }
  },

  /** Create a new test config for tenant */
  async createConfig(db: any, tenantId: string, data: CreateConfigData) {
    const id = crypto.randomUUID();
    try {
      await db.prepare(
        `INSERT INTO integration_test_configs
           (id, tenant_id, test_name, target_endpoint, method, expected_status, headers_json, body_json, schedule_cron)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(
        id,
        tenantId,
        data.test_name,
        data.target_endpoint,
        data.method ?? 'GET',
        data.expected_status ?? 200,
        data.headers_json ?? '{}',
        data.body_json ?? null,
        data.schedule_cron ?? null
      ).run();
      return { id, tenant_id: tenantId, ...data };
    } catch (err) {
      throw new Error(`createConfig failed: ${err}`);
    }
  },

  /** Get test results for a tenant, optionally filtered by config_id */
  async getResults(db: any, tenantId: string, configId?: string) {
    try {
      const sql = configId
        ? `SELECT * FROM integration_test_results WHERE tenant_id = ? AND config_id = ? ORDER BY executed_at DESC LIMIT 100`
        : `SELECT * FROM integration_test_results WHERE tenant_id = ? ORDER BY executed_at DESC LIMIT 100`;
      const result = configId
        ? await db.prepare(sql).bind(tenantId, configId).all()
        : await db.prepare(sql).bind(tenantId).all();
      return (result.results ?? []) as IntegrationTestResult[];
    } catch (err) {
      throw new Error(`getResults failed: ${err}`);
    }
  },

  /** Admin overview — config and result counts grouped by tenant */
  async getAdminOverview(db: any) {
    try {
      const configs = await db.prepare(
        `SELECT tenant_id, COUNT(*) as config_count FROM integration_test_configs GROUP BY tenant_id`
      ).all();
      const results = await db.prepare(
        `SELECT tenant_id, COUNT(*) as result_count,
                SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as pass_count
         FROM integration_test_results GROUP BY tenant_id`
      ).all();
      return {
        by_tenant_configs: (configs.results ?? []) as AdminOverviewRow[],
        by_tenant_results: (results.results ?? []) as AdminOverviewRow[],
      };
    } catch (err) {
      throw new Error(`getAdminOverview failed: ${err}`);
    }
  },
};
