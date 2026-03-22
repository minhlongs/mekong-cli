// Admin Tenant Analytics Service — health scores, usage trends, risk indicators

export const adminTenantAnalyticsService = {
  async getHealthScore(db: any, tenantId: string): Promise<unknown | null> {
    return db.prepare(
      `SELECT * FROM tenant_health_scores WHERE tenant_id = ? ORDER BY calculated_at DESC LIMIT 1`
    ).bind(tenantId).first();
  },

  async calculateHealthScore(db: any, tenantId: string): Promise<unknown> {
    // Derive score from risk indicators: deduct points per severity
    const { results: risks } = await db.prepare(
      `SELECT severity, COUNT(*) as count FROM tenant_risk_indicators
       WHERE tenant_id = ? AND resolved = 0 GROUP BY severity`
    ).bind(tenantId).all();

    let score = 100;
    const factors: Record<string, number> = {};
    for (const row of risks as { severity: string; count: number }[]) {
      const deduction = row.severity === 'critical' ? 20 : row.severity === 'high' ? 10 : row.severity === 'medium' ? 5 : 2;
      score -= deduction * row.count;
      factors[row.severity] = row.count;
    }
    score = Math.max(0, Math.min(100, score));

    const riskLevel = score >= 80 ? 'low' : score >= 60 ? 'medium' : score >= 40 ? 'high' : 'critical';

    return db.prepare(
      `INSERT INTO tenant_health_scores (id, tenant_id, score, risk_level, factors_json, calculated_at)
       VALUES (?, ?, ?, ?, ?, datetime('now')) RETURNING *`
    ).bind(crypto.randomUUID(), tenantId, score, riskLevel, JSON.stringify(factors)).first();
  },

  async listHealthScores(db: any, filters?: { risk_level?: string; tenant_id?: string }): Promise<unknown[]> {
    const where: string[] = [];
    const binds: unknown[] = [];

    if (filters?.risk_level) { where.push('risk_level = ?'); binds.push(filters.risk_level); }
    if (filters?.tenant_id) { where.push('tenant_id = ?'); binds.push(filters.tenant_id); }

    const sql = `SELECT * FROM tenant_health_scores${where.length ? ` WHERE ${where.join(' AND ')}` : ''}
                 ORDER BY calculated_at DESC LIMIT 200`;
    const rows = await db.prepare(sql).bind(...binds).all();
    return rows.results;
  },

  async getUsageTrends(db: any, tenantId: string, periods?: string[]): Promise<unknown[]> {
    let sql = `SELECT * FROM tenant_usage_trends WHERE tenant_id = ?`;
    const binds: unknown[] = [tenantId];

    if (periods?.length) {
      sql += ` AND period IN (${periods.map(() => '?').join(',')})`;
      binds.push(...periods);
    }
    sql += ` ORDER BY period DESC LIMIT 100`;

    const rows = await db.prepare(sql).bind(...binds).all();
    return rows.results;
  },

  async recordUsageTrend(db: any, tenantId: string, data: {
    period: string; missions_count?: number; api_calls?: number; credits_used?: number; revenue_cents?: number;
  }): Promise<unknown> {
    if (!data.period) throw new Error('period is required');
    return db.prepare(
      `INSERT INTO tenant_usage_trends (id, tenant_id, period, missions_count, api_calls, credits_used, revenue_cents)
       VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(
      crypto.randomUUID(), tenantId, data.period,
      data.missions_count ?? 0, data.api_calls ?? 0,
      data.credits_used ?? 0, data.revenue_cents ?? 0
    ).first();
  },

  async listRiskIndicators(db: any, filters?: { tenant_id?: string; severity?: string; indicator_type?: string; resolved?: boolean }): Promise<unknown[]> {
    const where: string[] = [];
    const binds: unknown[] = [];

    if (filters?.tenant_id) { where.push('tenant_id = ?'); binds.push(filters.tenant_id); }
    if (filters?.severity) { where.push('severity = ?'); binds.push(filters.severity); }
    if (filters?.indicator_type) { where.push('indicator_type = ?'); binds.push(filters.indicator_type); }
    if (filters?.resolved !== undefined) { where.push('resolved = ?'); binds.push(filters.resolved ? 1 : 0); }

    const sql = `SELECT * FROM tenant_risk_indicators${where.length ? ` WHERE ${where.join(' AND ')}` : ''}
                 ORDER BY detected_at DESC LIMIT 200`;
    const rows = await db.prepare(sql).bind(...binds).all();
    return rows.results;
  },

  async createRiskIndicator(db: any, tenantId: string, data: {
    indicator_type: string; severity?: string; description?: string;
  }): Promise<unknown> {
    if (!data.indicator_type) throw new Error('indicator_type is required');
    return db.prepare(
      `INSERT INTO tenant_risk_indicators (id, tenant_id, indicator_type, severity, description)
       VALUES (?, ?, ?, ?, ?) RETURNING *`
    ).bind(
      crypto.randomUUID(), tenantId, data.indicator_type,
      data.severity ?? 'low', data.description ?? null
    ).first();
  },

  async resolveRiskIndicator(db: any, id: string): Promise<unknown | null> {
    return db.prepare(
      `UPDATE tenant_risk_indicators SET resolved = 1, resolved_at = datetime('now')
       WHERE id = ? RETURNING *`
    ).bind(id).first();
  },

  async getTenantReport(db: any, tenantId: string): Promise<unknown> {
    const [health, trends, openRisks] = await Promise.all([
      db.prepare(`SELECT * FROM tenant_health_scores WHERE tenant_id = ? ORDER BY calculated_at DESC LIMIT 1`).bind(tenantId).first(),
      db.prepare(`SELECT * FROM tenant_usage_trends WHERE tenant_id = ? ORDER BY period DESC LIMIT 6`).bind(tenantId).all(),
      db.prepare(`SELECT severity, COUNT(*) as count FROM tenant_risk_indicators WHERE tenant_id = ? AND resolved = 0 GROUP BY severity`).bind(tenantId).all(),
    ]);
    const riskSummary: Record<string, number> = {};
    for (const r of (openRisks.results as { severity: string; count: number }[])) riskSummary[r.severity] = r.count;
    return { tenant_id: tenantId, health, recent_trends: trends.results, open_risk_summary: riskSummary };
  },

  async getAdminOverview(db: any): Promise<unknown> {
    const [totalTenants, riskDist, openRisks, trendSummary] = await Promise.all([
      db.prepare(`SELECT COUNT(DISTINCT tenant_id) as count FROM tenant_health_scores`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT risk_level, COUNT(*) as count FROM tenant_health_scores GROUP BY risk_level`).all(),
      db.prepare(`SELECT COUNT(*) as count FROM tenant_risk_indicators WHERE resolved = 0`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT SUM(missions_count) as missions, SUM(api_calls) as api_calls, SUM(revenue_cents) as revenue FROM tenant_usage_trends`).first() as Promise<{ missions: number; api_calls: number; revenue: number } | null>,
    ]);
    const riskMap: Record<string, number> = {};
    for (const row of (riskDist.results as { risk_level: string; count: number }[])) riskMap[row.risk_level] = row.count;
    return {
      tenants_tracked: totalTenants?.count ?? 0,
      risk_distribution: riskMap,
      open_risk_indicators: openRisks?.count ?? 0,
      platform_totals: { missions: trendSummary?.missions ?? 0, api_calls: trendSummary?.api_calls ?? 0, revenue_cents: trendSummary?.revenue ?? 0 },
    };
  },
};
