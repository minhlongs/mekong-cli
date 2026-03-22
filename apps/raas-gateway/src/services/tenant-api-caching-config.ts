/**
 * Tenant API Caching Config Service
 * CRUD for per-tenant endpoint caching rules + cache hit/miss stats
 */

// Result wrapper used across all methods
interface ServiceResult {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * List all caching configs for a tenant
 */
async function listConfigs(db: any, tenantId: string): Promise<ServiceResult> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, endpoint_pattern, ttl_seconds, cache_key_template, enabled, created_at, updated_at
         FROM api_caching_configs
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[tenantApiCachingConfig] listConfigs error:', err);
    return { success: false, error: 'Failed to list caching configs' };
  }
}

/**
 * Create a new caching config for a tenant
 */
async function createConfig(
  db: any,
  tenantId: string,
  payload: {
    endpoint_pattern: string;
    ttl_seconds?: number;
    cache_key_template?: string;
    enabled?: number;
  }
): Promise<ServiceResult> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO api_caching_configs
           (id, tenant_id, endpoint_pattern, ttl_seconds, cache_key_template, enabled, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        payload.endpoint_pattern,
        payload.ttl_seconds ?? 300,
        payload.cache_key_template ?? null,
        payload.enabled ?? 1,
        now,
        now
      )
      .run();

    return {
      success: true,
      data: {
        id,
        tenant_id: tenantId,
        endpoint_pattern: payload.endpoint_pattern,
        ttl_seconds: payload.ttl_seconds ?? 300,
        cache_key_template: payload.cache_key_template ?? null,
        enabled: payload.enabled ?? 1,
        created_at: now,
        updated_at: now,
      },
    };
  } catch (err) {
    console.error('[tenantApiCachingConfig] createConfig error:', err);
    return { success: false, error: 'Failed to create caching config' };
  }
}

/**
 * Get cache hit/miss stats for a tenant, optionally filtered by config_id
 */
async function getStats(db: any, tenantId: string, configId?: string): Promise<ServiceResult> {
  try {
    const query = configId
      ? `SELECT id, tenant_id, config_id, hits, misses, hit_rate, recorded_at
         FROM api_cache_stats
         WHERE tenant_id = ? AND config_id = ?
         ORDER BY recorded_at DESC LIMIT 100`
      : `SELECT id, tenant_id, config_id, hits, misses, hit_rate, recorded_at
         FROM api_cache_stats
         WHERE tenant_id = ?
         ORDER BY recorded_at DESC LIMIT 100`;

    const stmt = configId
      ? db.prepare(query).bind(tenantId, configId)
      : db.prepare(query).bind(tenantId);

    const rows = await stmt.all();

    // Aggregate totals across all stats rows
    const results = rows.results ?? [];
    const totalHits = results.reduce((sum: number, r: any) => sum + (r.hits ?? 0), 0);
    const totalMisses = results.reduce((sum: number, r: any) => sum + (r.misses ?? 0), 0);
    const totalRequests = totalHits + totalMisses;
    const aggregateHitRate = totalRequests > 0 ? totalHits / totalRequests : null;

    return {
      success: true,
      data: {
        rows: results,
        aggregate: {
          total_hits: totalHits,
          total_misses: totalMisses,
          total_requests: totalRequests,
          hit_rate: aggregateHitRate,
        },
      },
    };
  } catch (err) {
    console.error('[tenantApiCachingConfig] getStats error:', err);
    return { success: false, error: 'Failed to fetch cache stats' };
  }
}

/**
 * Admin overview — platform-wide caching config counts and aggregate performance
 */
async function getAdminOverview(db: any): Promise<ServiceResult> {
  try {
    const [configSummary, statsSummary, topTenants] = await Promise.all([
      // Config counts by enabled state
      db
        .prepare(
          `SELECT
             COUNT(*) as total_configs,
             SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_configs,
             SUM(CASE WHEN enabled = 0 THEN 1 ELSE 0 END) as disabled_configs,
             COUNT(DISTINCT tenant_id) as tenants_with_configs
           FROM api_caching_configs`
        )
        .first(),

      // Platform-wide hit/miss aggregates
      db
        .prepare(
          `SELECT
             COALESCE(SUM(hits), 0) as total_hits,
             COALESCE(SUM(misses), 0) as total_misses,
             CASE
               WHEN SUM(hits) + SUM(misses) > 0
               THEN CAST(SUM(hits) AS REAL) / (SUM(hits) + SUM(misses))
               ELSE NULL
             END as platform_hit_rate
           FROM api_cache_stats`
        )
        .first(),

      // Top 10 tenants by cache hits
      db
        .prepare(
          `SELECT tenant_id, SUM(hits) as total_hits, SUM(misses) as total_misses
           FROM api_cache_stats
           GROUP BY tenant_id
           ORDER BY total_hits DESC
           LIMIT 10`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        configs: configSummary,
        performance: statsSummary,
        top_tenants_by_hits: topTenants.results ?? [],
      },
    };
  } catch (err) {
    console.error('[tenantApiCachingConfig] getAdminOverview error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

export const tenantApiCachingConfigService = {
  listConfigs,
  createConfig,
  getStats,
  getAdminOverview,
};
