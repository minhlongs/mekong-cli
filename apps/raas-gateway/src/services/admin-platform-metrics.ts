/**
 * Admin Platform Metrics Service
 * CRUD for platform_metrics + alert rules + dashboard aggregation
 */

// List recent metrics, optionally filtered by metric_name
async function listMetrics(
  db: any,
  metricName?: string,
  limit = 100
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const cap = Math.min(limit, 500);
    const result = metricName
      ? await db
          .prepare(
            `SELECT * FROM platform_metrics WHERE metric_name = ?
             ORDER BY recorded_at DESC LIMIT ?`
          )
          .bind(metricName, cap)
          .all()
      : await db
          .prepare(
            `SELECT * FROM platform_metrics ORDER BY recorded_at DESC LIMIT ?`
          )
          .bind(cap)
          .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Insert a new platform metric data point
async function createMetric(
  db: any,
  payload: {
    id: string;
    metric_name: string;
    metric_value: number;
    unit?: string;
    tags?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const { id, metric_name, metric_value, unit, tags } = payload;
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO platform_metrics (id, metric_name, metric_value, unit, tags, recorded_at)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
      .bind(id, metric_name, metric_value, unit ?? 'count', tags ?? null, now)
      .run();

    const created = await db
      .prepare(`SELECT * FROM platform_metrics WHERE id = ?`)
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// List alert rules, optionally filtered by enabled state
async function getAlerts(
  db: any,
  enabledOnly = false
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = enabledOnly
      ? await db
          .prepare(
            `SELECT * FROM platform_metric_alerts WHERE enabled = 1
             ORDER BY metric_name ASC`
          )
          .all()
      : await db
          .prepare(
            `SELECT * FROM platform_metric_alerts ORDER BY metric_name ASC`
          )
          .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Aggregate dashboard: latest value per metric + breached alert count
async function getDashboard(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [latestRows, alertRows] = await Promise.all([
      db
        .prepare(
          `SELECT metric_name,
                  metric_value,
                  unit,
                  recorded_at
           FROM platform_metrics
           WHERE recorded_at = (
             SELECT MAX(recorded_at) FROM platform_metrics p2
             WHERE p2.metric_name = platform_metrics.metric_name
           )
           ORDER BY metric_name ASC`
        )
        .all(),
      db
        .prepare(
          `SELECT * FROM platform_metric_alerts WHERE enabled = 1`
        )
        .all(),
    ]);

    const latest: Record<string, any> = {};
    for (const row of (latestRows.results ?? []) as any[]) {
      latest[row.metric_name] = row;
    }

    // Evaluate which alerts are currently breaching
    const breached: any[] = [];
    for (const alert of (alertRows.results ?? []) as any[]) {
      const current = latest[alert.metric_name];
      if (!current) continue;
      const val: number = current.metric_value;
      const th: number = alert.threshold;
      const firing =
        alert.comparison === 'gt'
          ? val > th
          : alert.comparison === 'lt'
          ? val < th
          : alert.comparison === 'gte'
          ? val >= th
          : alert.comparison === 'lte'
          ? val <= th
          : val === th;
      if (firing) breached.push({ ...alert, current_value: val });
    }

    return {
      success: true,
      data: {
        latestMetrics: Object.values(latest),
        totalMetrics: Object.keys(latest).length,
        breachedAlerts: breached,
        breachedCount: breached.length,
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminPlatformMetricsService = {
  listMetrics,
  createMetric,
  getAlerts,
  getDashboard,
};
