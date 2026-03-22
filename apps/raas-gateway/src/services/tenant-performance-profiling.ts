/**
 * Tenant Performance Profiling Service
 * CRUD for performance_profiles and performance_baselines tables.
 * All functions return { success, data } or { success, error }.
 */

export interface PerformanceProfile {
  id: string;
  tenant_id: string;
  profile_name: string;
  endpoint: string;
  avg_response_ms: number | null;
  p95_response_ms: number | null;
  p99_response_ms: number | null;
  sample_count: number;
  created_at: string;
  updated_at: string;
}

export interface PerformanceBaseline {
  id: string;
  tenant_id: string;
  endpoint: string;
  baseline_avg_ms: number;
  baseline_p95_ms: number | null;
  threshold_multiplier: number;
  alert_enabled: number;
  created_at: string;
}

export interface CreateProfileInput {
  profile_name: string;
  endpoint: string;
  avg_response_ms?: number;
  p95_response_ms?: number;
  p99_response_ms?: number;
  sample_count?: number;
}

export interface AdminOverviewRow {
  tenant_id: string;
  profile_count: number;
  baseline_count: number;
  avg_sample_count: number;
}

// ── List profiles for a tenant ────────────────────────────────────────────────

export async function listProfiles(
  db: any,
  tenantId: string,
  limit = 50
): Promise<{ success: boolean; data?: PerformanceProfile[]; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit), 200);
    const result = await db
      .prepare(
        `SELECT id, tenant_id, profile_name, endpoint,
                avg_response_ms, p95_response_ms, p99_response_ms,
                sample_count, created_at, updated_at
         FROM performance_profiles
         WHERE tenant_id = ?
         ORDER BY updated_at DESC
         LIMIT ?`
      )
      .bind(tenantId, safeLimit)
      .all();

    return { success: true, data: result.results as PerformanceProfile[] };
  } catch (err) {
    console.error('[tenantPerformanceProfiling] listProfiles error:', err);
    return { success: false, error: 'Failed to list performance profiles' };
  }
}

// ── Create a new performance profile ─────────────────────────────────────────

export async function createProfile(
  db: any,
  tenantId: string,
  input: CreateProfileInput
): Promise<{ success: boolean; data?: PerformanceProfile; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const sampleCount = input.sample_count ?? 0;

    await db
      .prepare(
        `INSERT INTO performance_profiles
           (id, tenant_id, profile_name, endpoint,
            avg_response_ms, p95_response_ms, p99_response_ms,
            sample_count, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        input.profile_name,
        input.endpoint,
        input.avg_response_ms ?? null,
        input.p95_response_ms ?? null,
        input.p99_response_ms ?? null,
        sampleCount,
        now,
        now
      )
      .run();

    const row = await db
      .prepare('SELECT * FROM performance_profiles WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: row as PerformanceProfile };
  } catch (err) {
    console.error('[tenantPerformanceProfiling] createProfile error:', err);
    return { success: false, error: 'Failed to create performance profile' };
  }
}

// ── Get baselines for a tenant ────────────────────────────────────────────────

export async function getBaselines(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: PerformanceBaseline[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, endpoint, baseline_avg_ms, baseline_p95_ms,
                threshold_multiplier, alert_enabled, created_at
         FROM performance_baselines
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: result.results as PerformanceBaseline[] };
  } catch (err) {
    console.error('[tenantPerformanceProfiling] getBaselines error:', err);
    return { success: false, error: 'Failed to fetch performance baselines' };
  }
}

// ── Admin: platform-wide overview ─────────────────────────────────────────────

export async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: AdminOverviewRow[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT
           p.tenant_id,
           COUNT(DISTINCT p.id) AS profile_count,
           COUNT(DISTINCT b.id) AS baseline_count,
           COALESCE(AVG(p.sample_count), 0) AS avg_sample_count
         FROM performance_profiles p
         LEFT JOIN performance_baselines b ON b.tenant_id = p.tenant_id
         GROUP BY p.tenant_id
         ORDER BY profile_count DESC
         LIMIT 100`
      )
      .all();

    return { success: true, data: result.results as AdminOverviewRow[] };
  } catch (err) {
    console.error('[tenantPerformanceProfiling] getAdminOverview error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

// ── Named export matching spec ────────────────────────────────────────────────

export const tenantPerformanceProfilingService = {
  listProfiles,
  createProfile,
  getBaselines,
  getAdminOverview,
};
