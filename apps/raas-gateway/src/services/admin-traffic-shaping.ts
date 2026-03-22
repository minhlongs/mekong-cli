// Admin Traffic Shaping Service — manage traffic rules, events, and dashboard stats

export const adminTrafficShapingService = {
  async listRules(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM traffic_rules ORDER BY priority DESC, created_at DESC`
      ).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`listRules failed: ${(e as Error).message}`);
    }
  },

  async createRule(db: any, data: {
    rule_name: string;
    target_pattern: string;
    max_rps: number;
    burst_size?: number;
    priority?: number;
    is_active?: number;
  }): Promise<unknown> {
    try {
      return db.prepare(
        `INSERT INTO traffic_rules (id, rule_name, target_pattern, max_rps, burst_size, priority, is_active)
         VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
      ).bind(
        crypto.randomUUID(),
        data.rule_name,
        data.target_pattern,
        data.max_rps,
        data.burst_size ?? 10,
        data.priority ?? 5,
        data.is_active ?? 1
      ).first();
    } catch (e: unknown) {
      throw new Error(`createRule failed: ${(e as Error).message}`);
    }
  },

  async getEvents(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM traffic_events ORDER BY created_at DESC LIMIT 500`
      ).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`getEvents failed: ${(e as Error).message}`);
    }
  },

  async getDashboard(db: any): Promise<unknown> {
    try {
      const [totalRules, activeRules, totalEvents, recentEvents] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM traffic_rules`).first() as Promise<{ count: number } | null>,
        db.prepare(`SELECT COUNT(*) as count FROM traffic_rules WHERE is_active = 1`).first() as Promise<{ count: number } | null>,
        db.prepare(`SELECT COUNT(*) as count FROM traffic_events`).first() as Promise<{ count: number } | null>,
        db.prepare(
          `SELECT action_taken, COUNT(*) as count FROM traffic_events GROUP BY action_taken`
        ).all(),
      ]);
      const actionMap: Record<string, number> = {};
      for (const row of (recentEvents.results as any[])) {
        actionMap[row.action_taken] = row.count;
      }
      return {
        rules: {
          total: totalRules?.count ?? 0,
          active: activeRules?.count ?? 0,
          inactive: (totalRules?.count ?? 0) - (activeRules?.count ?? 0),
        },
        events: {
          total: totalEvents?.count ?? 0,
          by_action: actionMap,
        },
      };
    } catch (e: unknown) {
      throw new Error(`getDashboard failed: ${(e as Error).message}`);
    }
  },
};
