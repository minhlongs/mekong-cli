/**
 * Mission Analytics Dashboard Service
 * Provides snapshot aggregation, widget config, and admin overview for mission analytics.
 */

// ── Helpers ────────────────────────────────────────────────────────────────

function uid(): string {
  return crypto.randomUUID();
}

// ── listSnapshots ──────────────────────────────────────────────────────────

async function listSnapshots(
  db: any,
  tenantId: string,
  opts: { period?: string; limit?: number } = {}
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const limit = Math.min(opts.limit ?? 50, 200);
    const periodClause = opts.period ? 'AND period = ?' : '';
    const bindings: any[] = opts.period
      ? [tenantId, opts.period, limit]
      : [tenantId, limit];

    const rows = await db
      .prepare(
        `SELECT id, tenant_id, period, total_missions, completed_missions,
                failed_missions, avg_duration_ms, created_at
         FROM mission_analytics_snapshots
         WHERE tenant_id = ? ${periodClause}
         ORDER BY created_at DESC
         LIMIT ?`
      )
      .bind(...bindings)
      .all();

    return { success: true, data: rows.results };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to list snapshots';
    return { success: false, error };
  }
}

// ── createSnapshot ─────────────────────────────────────────────────────────

interface SnapshotInput {
  period: string;
  total_missions?: number;
  completed_missions?: number;
  failed_missions?: number;
  avg_duration_ms?: number | null;
}

async function createSnapshot(
  db: any,
  tenantId: string,
  input: SnapshotInput
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    if (!input.period?.trim()) {
      return { success: false, error: 'period is required' };
    }

    const id = uid();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO mission_analytics_snapshots
           (id, tenant_id, period, total_missions, completed_missions, failed_missions, avg_duration_ms, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        input.period.trim(),
        input.total_missions ?? 0,
        input.completed_missions ?? 0,
        input.failed_missions ?? 0,
        input.avg_duration_ms ?? null,
        now
      )
      .run();

    return {
      success: true,
      data: {
        id,
        tenant_id: tenantId,
        period: input.period.trim(),
        total_missions: input.total_missions ?? 0,
        completed_missions: input.completed_missions ?? 0,
        failed_missions: input.failed_missions ?? 0,
        avg_duration_ms: input.avg_duration_ms ?? null,
        created_at: now,
      },
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to create snapshot';
    return { success: false, error };
  }
}

// ── getWidgets ─────────────────────────────────────────────────────────────

async function getWidgets(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, widget_name, widget_type, config_json, position, created_at
         FROM mission_analytics_widgets
         WHERE tenant_id = ?
         ORDER BY position ASC, created_at ASC`
      )
      .bind(tenantId)
      .all();

    const data = (rows.results as any[]).map((w) => ({
      ...w,
      config: w.config_json ? (() => { try { return JSON.parse(w.config_json); } catch { return null; } })() : null,
    }));

    return { success: true, data };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to fetch widgets';
    return { success: false, error };
  }
}

// ── getAdminOverview ───────────────────────────────────────────────────────

async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [totalSnapshots, totalWidgets, recentSnapshots, topTenants] = await Promise.all([
      db
        .prepare(`SELECT COUNT(*) as count FROM mission_analytics_snapshots`)
        .first(),
      db
        .prepare(`SELECT COUNT(*) as count FROM mission_analytics_widgets`)
        .first(),
      db
        .prepare(
          `SELECT id, tenant_id, period, total_missions, completed_missions, failed_missions, avg_duration_ms, created_at
           FROM mission_analytics_snapshots
           ORDER BY created_at DESC
           LIMIT 10`
        )
        .all(),
      db
        .prepare(
          `SELECT tenant_id, COUNT(*) as snapshot_count, SUM(total_missions) as total_missions
           FROM mission_analytics_snapshots
           GROUP BY tenant_id
           ORDER BY total_missions DESC
           LIMIT 10`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        total_snapshots: totalSnapshots?.count ?? 0,
        total_widgets: totalWidgets?.count ?? 0,
        recent_snapshots: recentSnapshots.results,
        top_tenants: topTenants.results,
      },
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to fetch admin overview';
    return { success: false, error };
  }
}

// ── Exported service object ────────────────────────────────────────────────

export const missionAnalyticsDashboardService = {
  listSnapshots,
  createSnapshot,
  getWidgets,
  getAdminOverview,
};
