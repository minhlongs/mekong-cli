/**
 * Admin Platform Dashboard Summary Service
 * Widget config management + platform snapshot aggregation for the admin dashboard
 */

const TIER_PRICES: Record<string, number> = { starter: 49, pro: 149, enterprise: 499 };

/** List all dashboard widgets ordered by position */
async function listWidgets(db: any): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const rows = await db.prepare(
      `SELECT * FROM platform_dashboard_widgets ORDER BY position ASC, created_at ASC`
    ).all();
    return { success: true, data: rows.results as any[] };
  } catch (e: any) {
    return { success: false, error: e.message };
  }
}

/** Create a new dashboard widget */
async function createWidget(
  db: any,
  params: {
    widget_name: string;
    widget_type?: string;
    data_source: string;
    refresh_interval_ms?: number;
    position?: number;
    enabled?: number;
  }
): Promise<{ success: boolean; data?: { id: string }; error?: string }> {
  try {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO platform_dashboard_widgets
         (id, widget_name, widget_type, data_source, refresh_interval_ms, position, enabled)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id,
      params.widget_name,
      params.widget_type ?? 'metric',
      params.data_source,
      params.refresh_interval_ms ?? 60000,
      params.position ?? 0,
      params.enabled ?? 1
    ).run();
    return { success: true, data: { id } };
  } catch (e: any) {
    return { success: false, error: e.message };
  }
}

/** List dashboard snapshots, most recent first */
async function getSnapshots(
  db: any,
  limit = 30
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const rows = await db.prepare(
      `SELECT * FROM platform_dashboard_snapshots ORDER BY created_at DESC LIMIT ?`
    ).bind(Math.min(limit, 365)).all();
    return { success: true, data: rows.results as any[] };
  } catch (e: any) {
    return { success: false, error: e.message };
  }
}

/** Aggregate live dashboard: tenants, missions, revenue, MRR/ARR — then persist snapshot */
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [tenants, missions, revenue] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as count FROM tenants`).first(),
      db.prepare(`SELECT COUNT(*) as count FROM missions`).first(),
      db.prepare(
        `SELECT COALESCE(SUM(amount), 0) as total FROM credit_transactions WHERE type = 'purchase'`
      ).first(),
    ]);

    const mrr = await _computeMRR(db);
    const arr = mrr * 12;

    const summary = {
      total_tenants: tenants?.count ?? 0,
      total_missions: missions?.count ?? 0,
      total_revenue: revenue?.total ?? 0,
      mrr,
      arr,
      captured_at: new Date().toISOString(),
    };

    // Persist snapshot for historical tracking
    const snapshotId = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO platform_dashboard_snapshots
         (id, snapshot_data, total_tenants, total_missions, total_revenue, mrr, arr)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      snapshotId,
      JSON.stringify(summary),
      summary.total_tenants,
      summary.total_missions,
      summary.total_revenue,
      mrr,
      arr
    ).run();

    return { success: true, data: { ...summary, snapshot_id: snapshotId } };
  } catch (e: any) {
    return { success: false, error: e.message };
  }
}

// --- internal helper ---

async function _computeMRR(db: any): Promise<number> {
  try {
    const subs = await db.prepare(
      `SELECT tier, COUNT(*) as count FROM subscriptions WHERE status = 'active' GROUP BY tier`
    ).all();
    if (subs.results.length > 0) {
      return (subs.results as any[]).reduce(
        (sum: number, r: any) => sum + (TIER_PRICES[r.tier] || 0) * r.count, 0
      );
    }
    const tiers = await db.prepare(
      `SELECT tier, COUNT(*) as count FROM tenants WHERE active = 1 GROUP BY tier`
    ).all();
    return (tiers.results as any[]).reduce(
      (sum: number, r: any) => sum + (TIER_PRICES[r.tier] || 0) * r.count, 0
    );
  } catch {
    return 0;
  }
}

export const adminPlatformDashboardSummaryService = {
  listWidgets,
  createWidget,
  getSnapshots,
  getDashboard,
};
