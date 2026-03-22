// Admin System Health Service — metrics, component health, uptime, alert rules

/** Evaluate alert condition against a value */
function evalCondition(condition: string, val: number, threshold: number): boolean {
  if (condition === 'gt') return val > threshold;
  if (condition === 'lt') return val < threshold;
  if (condition === 'gte') return val >= threshold;
  if (condition === 'lte') return val <= threshold;
  if (condition === 'eq') return val === threshold;
  return false;
}

export const adminSystemHealthService = {
  async recordMetric(db: any, data: {
    metric_name: string; metric_value: number; unit?: string; component?: string; tags?: Record<string, unknown>;
  }): Promise<unknown> {
    return db.prepare(
      `INSERT INTO system_metrics (id, metric_name, metric_value, unit, component, tags_json)
       VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(crypto.randomUUID(), data.metric_name, data.metric_value,
      data.unit ?? 'count', data.component ?? 'gateway', JSON.stringify(data.tags ?? {})).first();
  },

  async getMetrics(db: any, metricName: string, limit = 100): Promise<unknown[]> {
    const rows = await db.prepare(
      `SELECT * FROM system_metrics WHERE metric_name = ? ORDER BY recorded_at DESC LIMIT ?`
    ).bind(metricName, Math.min(limit, 500)).all();
    return rows.results;
  },

  async listComponents(db: any): Promise<unknown[]> {
    const rows = await db.prepare(`SELECT * FROM component_health ORDER BY component_name ASC`).all();
    return rows.results;
  },

  async updateComponent(db: any, name: string, data: {
    status?: string; last_check_at?: string; response_time_ms?: number; error_message?: string; metadata?: Record<string, unknown>;
  }): Promise<unknown> {
    return db.prepare(
      `INSERT INTO component_health (id, component_name, status, last_check_at, response_time_ms, error_message, metadata_json, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
       ON CONFLICT(component_name) DO UPDATE SET
         status=excluded.status, last_check_at=excluded.last_check_at, response_time_ms=excluded.response_time_ms,
         error_message=excluded.error_message, metadata_json=excluded.metadata_json, updated_at=datetime('now')
       RETURNING *`
    ).bind(crypto.randomUUID(), name, data.status ?? 'healthy',
      data.last_check_at ?? new Date().toISOString(), data.response_time_ms ?? null,
      data.error_message ?? null, JSON.stringify(data.metadata ?? {})).first();
  },

  async getUptimeHistory(db: any, componentName: string): Promise<unknown[]> {
    const rows = await db.prepare(
      `SELECT * FROM uptime_records WHERE component_name = ? ORDER BY started_at DESC LIMIT 100`
    ).bind(componentName).all();
    return rows.results;
  },

  async recordUptime(db: any, data: {
    component_name: string; status: string; started_at: string; ended_at?: string; duration_seconds?: number;
  }): Promise<unknown> {
    return db.prepare(
      `INSERT INTO uptime_records (id, component_name, status, started_at, ended_at, duration_seconds)
       VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(crypto.randomUUID(), data.component_name, data.status,
      data.started_at, data.ended_at ?? null, data.duration_seconds ?? null).first();
  },

  async listAlertRules(db: any): Promise<unknown[]> {
    const rows = await db.prepare(`SELECT * FROM alert_rules ORDER BY severity DESC, created_at DESC`).all();
    return rows.results;
  },

  async createAlertRule(db: any, data: {
    name: string; metric_name: string; condition: string; threshold: number; severity?: string; enabled?: boolean;
  }): Promise<unknown> {
    return db.prepare(
      `INSERT INTO alert_rules (id, name, metric_name, condition, threshold, severity, enabled)
       VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(crypto.randomUUID(), data.name, data.metric_name, data.condition,
      data.threshold, data.severity ?? 'warning', data.enabled !== false ? 1 : 0).first();
  },

  async updateAlertRule(db: any, id: string, data: {
    name?: string; condition?: string; threshold?: number; severity?: string; enabled?: boolean;
  }): Promise<unknown | null> {
    const sets: string[] = [];
    const binds: unknown[] = [];
    if (data.name !== undefined) { sets.push('name = ?'); binds.push(data.name); }
    if (data.condition !== undefined) { sets.push('condition = ?'); binds.push(data.condition); }
    if (data.threshold !== undefined) { sets.push('threshold = ?'); binds.push(data.threshold); }
    if (data.severity !== undefined) { sets.push('severity = ?'); binds.push(data.severity); }
    if (data.enabled !== undefined) { sets.push('enabled = ?'); binds.push(data.enabled ? 1 : 0); }
    if (!sets.length) return db.prepare(`SELECT * FROM alert_rules WHERE id = ?`).bind(id).first();
    binds.push(id);
    return db.prepare(`UPDATE alert_rules SET ${sets.join(', ')} WHERE id = ? RETURNING *`).bind(...binds).first();
  },

  async deleteAlertRule(db: any, id: string): Promise<boolean> {
    const result = await db.prepare(`DELETE FROM alert_rules WHERE id = ?`).bind(id).run();
    return result.meta?.changes > 0;
  },

  async checkAlerts(db: any): Promise<unknown[]> {
    const { results: rules } = await db.prepare(`SELECT * FROM alert_rules WHERE enabled = 1`).all();
    const triggered: unknown[] = [];
    for (const rule of rules as any[]) {
      const latest = await db.prepare(
        `SELECT metric_value FROM system_metrics WHERE metric_name = ? ORDER BY recorded_at DESC LIMIT 1`
      ).bind(rule.metric_name).first() as { metric_value: number } | null;
      if (!latest || !evalCondition(rule.condition, latest.metric_value, rule.threshold)) continue;
      await db.prepare(`UPDATE alert_rules SET last_triggered_at = datetime('now') WHERE id = ?`).bind(rule.id).run();
      triggered.push({ rule_id: rule.id, name: rule.name, metric_name: rule.metric_name,
        value: latest.metric_value, threshold: rule.threshold, severity: rule.severity });
    }
    return triggered;
  },

  async getAdminOverview(db: any): Promise<unknown> {
    const [totalMetrics, components, activeAlerts, uptimeCount] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as count FROM system_metrics`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT status, COUNT(*) as count FROM component_health GROUP BY status`).all(),
      db.prepare(`SELECT COUNT(*) as count FROM alert_rules WHERE enabled = 1`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT COUNT(*) as count FROM uptime_records WHERE ended_at IS NULL`).first() as Promise<{ count: number } | null>,
    ]);
    const compMap: Record<string, number> = {};
    for (const row of (components.results as any[])) compMap[row.status] = row.count;
    return {
      metrics: { total: totalMetrics?.count ?? 0 },
      components: { healthy: compMap['healthy'] ?? 0, degraded: compMap['degraded'] ?? 0, unhealthy: compMap['unhealthy'] ?? 0 },
      alerts: { active_rules: activeAlerts?.count ?? 0 },
      uptime: { open_records: uptimeCount?.count ?? 0 },
    };
  },
};
