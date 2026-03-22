/**
 * Tenant API Playground Configs Service
 * CRUD for saved playground configs + execution history per tenant
 */

// Saved API request configuration
interface PlaygroundConfig {
  id: string;
  tenant_id: string;
  config_name: string;
  endpoint: string;
  method: string;
  headers_json: string;
  body_json: string | null;
  is_shared: number;
  created_at: string;
  updated_at: string;
}

// Execution log record
interface PlaygroundExecution {
  id: string;
  tenant_id: string;
  config_id: string;
  response_status: number | null;
  response_time_ms: number | null;
  created_at: string;
}

/**
 * List all configs for a tenant (includes shared configs from other tenants)
 */
async function listConfigs(db: any, tenantId: string): Promise<PlaygroundConfig[]> {
  try {
    const result = await db
      .prepare(
        `SELECT * FROM playground_configs
         WHERE tenant_id = ? OR is_shared = 1
         ORDER BY updated_at DESC LIMIT 100`
      )
      .bind(tenantId)
      .all();
    return (result.results ?? []) as PlaygroundConfig[];
  } catch (err) {
    console.error('[playgroundConfigsSvc] listConfigs error:', err);
    throw err;
  }
}

/**
 * Create a new playground config for a tenant
 */
async function createConfig(
  db: any,
  tenantId: string,
  body: {
    config_name: string;
    endpoint: string;
    method?: string;
    headers_json?: string;
    body_json?: string | null;
    is_shared?: number;
  }
): Promise<PlaygroundConfig> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO playground_configs
           (id, tenant_id, config_name, endpoint, method, headers_json, body_json, is_shared, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        body.config_name,
        body.endpoint,
        body.method ?? 'GET',
        body.headers_json ?? '{}',
        body.body_json ?? null,
        body.is_shared ?? 0,
        now,
        now
      )
      .run();

    const row = await db
      .prepare('SELECT * FROM playground_configs WHERE id = ?')
      .bind(id)
      .first();
    return row as PlaygroundConfig;
  } catch (err) {
    console.error('[playgroundConfigsSvc] createConfig error:', err);
    throw err;
  }
}

/**
 * Get execution history for a tenant, optionally filtered by config_id
 */
async function getExecutions(
  db: any,
  tenantId: string,
  configId?: string
): Promise<PlaygroundExecution[]> {
  try {
    const result = configId
      ? await db
          .prepare(
            `SELECT * FROM playground_executions
             WHERE tenant_id = ? AND config_id = ?
             ORDER BY created_at DESC LIMIT 200`
          )
          .bind(tenantId, configId)
          .all()
      : await db
          .prepare(
            `SELECT * FROM playground_executions
             WHERE tenant_id = ?
             ORDER BY created_at DESC LIMIT 200`
          )
          .bind(tenantId)
          .all();
    return (result.results ?? []) as PlaygroundExecution[];
  } catch (err) {
    console.error('[playgroundConfigsSvc] getExecutions error:', err);
    throw err;
  }
}

/**
 * Admin overview — config counts and recent execution stats across all tenants
 */
async function getAdminOverview(db: any): Promise<{
  total_configs: number;
  shared_configs: number;
  total_executions: number;
  unique_tenants: number;
}> {
  try {
    const configs = await db
      .prepare(
        `SELECT COUNT(*) as total,
                SUM(is_shared) as shared,
                COUNT(DISTINCT tenant_id) as tenants
         FROM playground_configs`
      )
      .first();
    const execs = await db
      .prepare('SELECT COUNT(*) as total FROM playground_executions')
      .first();
    return {
      total_configs: (configs as any)?.total ?? 0,
      shared_configs: (configs as any)?.shared ?? 0,
      total_executions: (execs as any)?.total ?? 0,
      unique_tenants: (configs as any)?.tenants ?? 0,
    };
  } catch (err) {
    console.error('[playgroundConfigsSvc] getAdminOverview error:', err);
    throw err;
  }
}

export const playgroundConfigsService = {
  listConfigs,
  createConfig,
  getExecutions,
  getAdminOverview,
};
