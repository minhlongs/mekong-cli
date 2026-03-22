/**
 * Admin Platform Alerts Service — metric-based alert rules and incident management
 */

function newId(): string {
  return crypto.randomUUID();
}

function now(): string {
  return new Date().toISOString();
}

export const adminPlatformAlertsService = {
  /** List all alert rules, active first */
  async listRules(db: any): Promise<any[]> {
    try {
      const result = await db
        .prepare('SELECT * FROM platform_alert_rules ORDER BY is_active DESC, created_at DESC')
        .all();
      return (result.results ?? []) as any[];
    } catch (err) {
      throw new Error(`listRules failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  },

  /** Create a new alert rule */
  async createRule(db: any, input: {
    rule_name: string;
    metric_name: string;
    condition: string;
    threshold?: number;
    severity?: string;
    notification_channels?: unknown[];
    is_active?: number;
  }): Promise<any> {
    try {
      const id = newId();
      const ts = now();
      const channels = JSON.stringify(input.notification_channels ?? []);
      await db
        .prepare(
          `INSERT INTO platform_alert_rules
           (id, rule_name, metric_name, condition, threshold, severity, notification_channels, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          input.rule_name,
          input.metric_name,
          input.condition,
          input.threshold ?? null,
          input.severity ?? 'warning',
          channels,
          input.is_active ?? 1,
          ts,
          ts
        )
        .run();
      return { id, ...input, notification_channels: channels, created_at: ts, updated_at: ts };
    } catch (err) {
      throw new Error(`createRule failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  },

  /** List incidents, optionally filtered by status or rule_id */
  async getIncidents(db: any, filter?: { rule_id?: string; status?: string }): Promise<any[]> {
    try {
      let query = 'SELECT * FROM platform_alert_incidents';
      const params: string[] = [];
      const clauses: string[] = [];
      if (filter?.rule_id) { clauses.push('rule_id = ?'); params.push(filter.rule_id); }
      if (filter?.status) { clauses.push('status = ?'); params.push(filter.status); }
      if (clauses.length) query += ' WHERE ' + clauses.join(' AND ');
      query += ' ORDER BY created_at DESC LIMIT 200';
      const result = await db.prepare(query).bind(...params).all();
      return (result.results ?? []) as any[];
    } catch (err) {
      throw new Error(`getIncidents failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  },

  /** Dashboard summary: rule counts by severity + open incident count */
  async getDashboard(db: any): Promise<any> {
    try {
      const [rulesResult, incidentsResult] = await Promise.all([
        db.prepare(
          `SELECT severity, COUNT(*) as count FROM platform_alert_rules WHERE is_active = 1 GROUP BY severity`
        ).all(),
        db.prepare(
          `SELECT status, COUNT(*) as count FROM platform_alert_incidents GROUP BY status`
        ).all(),
      ]);
      return {
        rules_by_severity: (rulesResult.results ?? []) as any[],
        incidents_by_status: (incidentsResult.results ?? []) as any[],
      };
    } catch (err) {
      throw new Error(`getDashboard failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  },
};
