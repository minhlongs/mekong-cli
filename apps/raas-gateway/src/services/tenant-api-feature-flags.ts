/**
 * Tenant API Feature Flags Service
 * CRUD for per-tenant feature flags + evaluation log queries
 */

// Flag record shape returned from DB
interface FlagRow {
  id: string;
  tenant_id: string;
  flag_key: string;
  flag_value: number;
  description: string | null;
  rollout_percentage: number;
  created_at: string;
  updated_at: string;
}

// Evaluation record shape returned from DB
interface EvaluationRow {
  id: string;
  tenant_id: string;
  flag_id: string;
  user_id: string | null;
  result: number;
  context_json: string | null;
  evaluated_at: string;
}

// Admin overview shape
interface AdminOverviewRow {
  total_flags: number;
  enabled_flags: number;
  total_evaluations: number;
  tenant_count: number;
}

/**
 * List all feature flags for a tenant
 */
async function listFlags(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: FlagRow[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, flag_key, flag_value, description, rollout_percentage, created_at, updated_at
         FROM tenant_feature_flags
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: (result.results ?? []) as FlagRow[] };
  } catch (err) {
    console.error('[featureFlags] listFlags error:', err);
    return { success: false, error: 'Failed to list feature flags' };
  }
}

/**
 * Create a new feature flag for a tenant
 */
async function createFlag(
  db: any,
  tenantId: string,
  flagKey: string,
  flagValue: number,
  description?: string,
  rolloutPercentage?: number
): Promise<{ success: boolean; data?: FlagRow; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const pct = rolloutPercentage ?? 100;

    await db
      .prepare(
        `INSERT INTO tenant_feature_flags
           (id, tenant_id, flag_key, flag_value, description, rollout_percentage, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, flagKey, flagValue, description ?? null, pct, now, now)
      .run();

    const row = await db
      .prepare(
        `SELECT id, tenant_id, flag_key, flag_value, description, rollout_percentage, created_at, updated_at
         FROM tenant_feature_flags WHERE id = ?`
      )
      .bind(id)
      .first();

    return { success: true, data: (row ?? undefined) as FlagRow | undefined };
  } catch (err) {
    console.error('[featureFlags] createFlag error:', err);
    return { success: false, error: 'Failed to create feature flag' };
  }
}

/**
 * Get flag evaluations for a tenant
 * Optionally filter by flag_id; default limit 50
 */
async function getEvaluations(
  db: any,
  tenantId: string,
  flagId?: string,
  limit?: number
): Promise<{ success: boolean; data?: EvaluationRow[]; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit ?? 50), 200);

    let result;
    if (flagId) {
      result = await db
        .prepare(
          `SELECT id, tenant_id, flag_id, user_id, result, context_json, evaluated_at
           FROM tenant_feature_flag_evaluations
           WHERE tenant_id = ? AND flag_id = ?
           ORDER BY evaluated_at DESC
           LIMIT ?`
        )
        .bind(tenantId, flagId, safeLimit)
        .all();
    } else {
      result = await db
        .prepare(
          `SELECT id, tenant_id, flag_id, user_id, result, context_json, evaluated_at
           FROM tenant_feature_flag_evaluations
           WHERE tenant_id = ?
           ORDER BY evaluated_at DESC
           LIMIT ?`
        )
        .bind(tenantId, safeLimit)
        .all();
    }

    return { success: true, data: (result.results ?? []) as EvaluationRow[] };
  } catch (err) {
    console.error('[featureFlags] getEvaluations error:', err);
    return { success: false, error: 'Failed to fetch evaluations' };
  }
}

/**
 * Admin overview: aggregate stats across all tenants
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: AdminOverviewRow; error?: string }> {
  try {
    const [flagStats, evalStats, tenantCount] = await Promise.all([
      db
        .prepare(
          `SELECT
             COUNT(*) as total_flags,
             SUM(CASE WHEN flag_value = 1 THEN 1 ELSE 0 END) as enabled_flags
           FROM tenant_feature_flags`
        )
        .first(),
      db
        .prepare(`SELECT COUNT(*) as total_evaluations FROM tenant_feature_flag_evaluations`)
        .first(),
      db
        .prepare(`SELECT COUNT(DISTINCT tenant_id) as tenant_count FROM tenant_feature_flags`)
        .first(),
    ]) as [
      { total_flags: number; enabled_flags: number } | null,
      { total_evaluations: number } | null,
      { tenant_count: number } | null,
    ];

    return {
      success: true,
      data: {
        total_flags: flagStats?.total_flags ?? 0,
        enabled_flags: flagStats?.enabled_flags ?? 0,
        total_evaluations: evalStats?.total_evaluations ?? 0,
        tenant_count: tenantCount?.tenant_count ?? 0,
      },
    };
  } catch (err) {
    console.error('[featureFlags] getAdminOverview error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

export const tenantApiFeatureFlagsService = {
  listFlags,
  createFlag,
  getEvaluations,
  getAdminOverview,
};
