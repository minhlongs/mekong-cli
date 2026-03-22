/**
 * Tenant API Load Balancing Service
 *
 * Manages load balancer configs and targets per tenant.
 * Admin overview aggregates across all tenants.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface LoadBalancerConfig {
  id: string;
  tenant_id: string;
  config_name: string;
  algorithm: string;
  health_check_interval_ms: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface LoadBalancerTarget {
  id: string;
  tenant_id: string;
  config_id: string;
  target_url: string;
  weight: number;
  healthy: number;
  created_at: string;
}

export interface CreateConfigInput {
  config_name: string;
  algorithm?: string;
  health_check_interval_ms?: number;
}

// ---------------------------------------------------------------------------
// listConfigs — fetch all load balancer configs for a tenant
// ---------------------------------------------------------------------------

export async function listConfigs(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: LoadBalancerConfig[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        'SELECT * FROM api_load_balancer_configs WHERE tenant_id = ? ORDER BY created_at DESC'
      )
      .bind(tenantId)
      .all();
    return { success: true, data: result.results as LoadBalancerConfig[] };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return { success: false, error: message };
  }
}

// ---------------------------------------------------------------------------
// createConfig — insert a new load balancer config for a tenant
// ---------------------------------------------------------------------------

export async function createConfig(
  db: any,
  tenantId: string,
  input: CreateConfigInput
): Promise<{ success: boolean; data?: LoadBalancerConfig; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const algorithm = input.algorithm ?? 'round-robin';
    const healthCheckIntervalMs = input.health_check_interval_ms ?? 30000;
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO api_load_balancer_configs
          (id, tenant_id, config_name, algorithm, health_check_interval_ms, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 'active', ?, ?)`
      )
      .bind(id, tenantId, input.config_name, algorithm, healthCheckIntervalMs, now, now)
      .run();

    const created: LoadBalancerConfig = {
      id,
      tenant_id: tenantId,
      config_name: input.config_name,
      algorithm,
      health_check_interval_ms: healthCheckIntervalMs,
      status: 'active',
      created_at: now,
      updated_at: now,
    };
    return { success: true, data: created };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return { success: false, error: message };
  }
}

// ---------------------------------------------------------------------------
// getTargets — fetch all targets for a given config (scoped to tenant)
// ---------------------------------------------------------------------------

export async function getTargets(
  db: any,
  tenantId: string,
  configId: string
): Promise<{ success: boolean; data?: LoadBalancerTarget[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        'SELECT * FROM api_load_balancer_targets WHERE config_id = ? AND tenant_id = ? ORDER BY created_at ASC'
      )
      .bind(configId, tenantId)
      .all();
    return { success: true, data: result.results as LoadBalancerTarget[] };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return { success: false, error: message };
  }
}

// ---------------------------------------------------------------------------
// getAdminOverview — aggregate stats across all tenants (admin only)
// ---------------------------------------------------------------------------

export async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: object; error?: string }> {
  try {
    const configStats = await db
      .prepare(
        `SELECT
           COUNT(*) as total_configs,
           COUNT(DISTINCT tenant_id) as total_tenants,
           SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_configs
         FROM api_load_balancer_configs`
      )
      .first();

    const targetStats = await db
      .prepare(
        `SELECT
           COUNT(*) as total_targets,
           SUM(CASE WHEN healthy = 1 THEN 1 ELSE 0 END) as healthy_targets,
           SUM(CASE WHEN healthy = 0 THEN 1 ELSE 0 END) as unhealthy_targets
         FROM api_load_balancer_targets`
      )
      .first();

    const algorithmBreakdown = await db
      .prepare(
        'SELECT algorithm, COUNT(*) as count FROM api_load_balancer_configs GROUP BY algorithm'
      )
      .all();

    return {
      success: true,
      data: {
        configs: configStats,
        targets: targetStats,
        algorithm_breakdown: algorithmBreakdown.results,
      },
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error';
    return { success: false, error: message };
  }
}

export const tenantApiLoadBalancingService = {
  listConfigs,
  createConfig,
  getTargets,
  getAdminOverview,
};
