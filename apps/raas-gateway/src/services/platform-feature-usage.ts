/**
 * Platform Feature Usage Service — tracks per-tenant feature usage and adoption rates
 */

/** List all feature usage records, optionally filtered by feature_name or tenant_id */
export async function listUsage(db: any, opts?: { feature_name?: string; tenant_id?: string; period?: string }) {
  try {
    let query = 'SELECT * FROM feature_usage WHERE 1=1';
    const params: string[] = [];
    if (opts?.feature_name) { query += ' AND feature_name = ?'; params.push(opts.feature_name); }
    if (opts?.tenant_id)    { query += ' AND tenant_id = ?';    params.push(opts.tenant_id); }
    if (opts?.period)       { query += ' AND period = ?';        params.push(opts.period); }
    query += ' ORDER BY usage_count DESC';
    const result = await db.prepare(query).bind(...params).all();
    return result.results ?? [];
  } catch (e: any) {
    throw new Error(`listUsage failed: ${e.message}`);
  }
}

interface RecordUsageInput {
  id: string;
  feature_name: string;
  tenant_id: string;
  period?: string;
  last_used_at?: string;
}

/**
 * Upsert usage record — increments usage_count and updates last_used_at.
 * Insert on first call, increment on subsequent calls.
 */
export async function recordUsage(db: any, data: RecordUsageInput) {
  try {
    const period = data.period ?? 'monthly';
    const last_used_at = data.last_used_at ?? new Date().toISOString();

    // Check if record exists for this tenant+feature+period
    const existing = await db.prepare(
      'SELECT id FROM feature_usage WHERE feature_name = ? AND tenant_id = ? AND period = ?'
    ).bind(data.feature_name, data.tenant_id, period).first();

    if (existing) {
      await db.prepare(
        `UPDATE feature_usage SET usage_count = usage_count + 1, last_used_at = ? WHERE feature_name = ? AND tenant_id = ? AND period = ?`
      ).bind(last_used_at, data.feature_name, data.tenant_id, period).run();
    } else {
      await db.prepare(
        `INSERT INTO feature_usage (id, feature_name, tenant_id, usage_count, last_used_at, period) VALUES (?, ?, ?, 1, ?, ?)`
      ).bind(data.id, data.feature_name, data.tenant_id, last_used_at, period).run();
    }

    return { success: true, feature_name: data.feature_name, tenant_id: data.tenant_id, period };
  } catch (e: any) {
    throw new Error(`recordUsage failed: ${e.message}`);
  }
}

/** Get adoption metrics for all features from feature_adoption table */
export async function getAdoption(db: any, feature_name?: string) {
  try {
    let query = 'SELECT * FROM feature_adoption';
    const params: string[] = [];
    if (feature_name) { query += ' WHERE feature_name = ?'; params.push(feature_name); }
    query += ' ORDER BY adoption_rate DESC';
    const result = await db.prepare(query).bind(...params).all();
    return result.results ?? [];
  } catch (e: any) {
    throw new Error(`getAdoption failed: ${e.message}`);
  }
}

/** Dashboard: summary of top features by usage + adoption overview */
export async function getDashboard(db: any) {
  try {
    const [topUsage, adoption, totals] = await Promise.all([
      db.prepare(
        `SELECT feature_name, SUM(usage_count) as total_usage, COUNT(DISTINCT tenant_id) as tenant_count
         FROM feature_usage GROUP BY feature_name ORDER BY total_usage DESC LIMIT 10`
      ).all(),
      db.prepare(
        `SELECT feature_name, AVG(adoption_rate) as avg_adoption_rate
         FROM feature_adoption GROUP BY feature_name ORDER BY avg_adoption_rate DESC LIMIT 10`
      ).all(),
      db.prepare(
        `SELECT COUNT(DISTINCT feature_name) as features, COUNT(DISTINCT tenant_id) as tenants, SUM(usage_count) as total_events
         FROM feature_usage`
      ).first(),
    ]);

    return {
      top_features_by_usage: topUsage.results ?? [],
      top_features_by_adoption: adoption.results ?? [],
      summary: totals ?? { features: 0, tenants: 0, total_events: 0 },
    };
  } catch (e: any) {
    throw new Error(`getDashboard failed: ${e.message}`);
  }
}

export const platformFeatureUsageService = {
  listUsage,
  recordUsage,
  getAdoption,
  getDashboard,
};
