// Admin Configuration Drift Service — detects and tracks config drift between expected and actual resource state

export const adminConfigurationDriftService = {
  /** List all drift detections, optionally filtered by resource_type */
  async listDetections(db: any, opts?: { resource_type?: string; severity?: string; limit?: number }): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
    try {
      const limit = Math.min(opts?.limit ?? 100, 500);
      let query = `SELECT * FROM configuration_drift_detections`;
      const binds: unknown[] = [];
      const conditions: string[] = [];

      if (opts?.resource_type) {
        conditions.push(`resource_type = ?`);
        binds.push(opts.resource_type);
      }
      if (opts?.severity) {
        conditions.push(`severity = ?`);
        binds.push(opts.severity);
      }
      if (conditions.length) query += ` WHERE ` + conditions.join(' AND ');
      query += ` ORDER BY detected_at DESC LIMIT ?`;
      binds.push(limit);

      const rows = await db.prepare(query).bind(...binds).all();
      return { success: true, data: rows.results };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** Record a new drift detection */
  async createDetection(db: any, data: {
    resource_type: string;
    resource_id: string;
    expected_value?: string;
    actual_value?: string;
    drift_type?: string;
    severity?: string;
  }): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const id = crypto.randomUUID();
      const row = await db.prepare(
        `INSERT INTO configuration_drift_detections
           (id, resource_type, resource_id, expected_value, actual_value, drift_type, severity)
         VALUES (?, ?, ?, ?, ?, ?, ?)
         RETURNING *`
      ).bind(
        id,
        data.resource_type,
        data.resource_id,
        data.expected_value ?? null,
        data.actual_value ?? null,
        data.drift_type ?? 'modified',
        data.severity ?? 'medium',
      ).first();
      return { success: true, data: row };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** List baselines, optionally filtered by resource_type */
  async getBaselines(db: any, opts?: { resource_type?: string; resource_id?: string; limit?: number }): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
    try {
      const limit = Math.min(opts?.limit ?? 100, 500);
      let query = `SELECT * FROM configuration_drift_baselines`;
      const binds: unknown[] = [];
      const conditions: string[] = [];

      if (opts?.resource_type) {
        conditions.push(`resource_type = ?`);
        binds.push(opts.resource_type);
      }
      if (opts?.resource_id) {
        conditions.push(`resource_id = ?`);
        binds.push(opts.resource_id);
      }
      if (conditions.length) query += ` WHERE ` + conditions.join(' AND ');
      query += ` ORDER BY updated_at DESC LIMIT ?`;
      binds.push(limit);

      const rows = await db.prepare(query).bind(...binds).all();
      return { success: true, data: rows.results };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** Aggregated drift dashboard — counts by severity and drift_type */
  async getDashboard(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const [bySeverity, byType, recentDetections, baselineCount] = await Promise.all([
        db.prepare(
          `SELECT severity, COUNT(*) as count FROM configuration_drift_detections GROUP BY severity`
        ).all(),
        db.prepare(
          `SELECT drift_type, COUNT(*) as count FROM configuration_drift_detections GROUP BY drift_type`
        ).all(),
        db.prepare(
          `SELECT * FROM configuration_drift_detections ORDER BY detected_at DESC LIMIT 10`
        ).all(),
        db.prepare(
          `SELECT COUNT(*) as total FROM configuration_drift_baselines`
        ).first(),
      ]);

      return {
        success: true,
        data: {
          by_severity: bySeverity.results,
          by_drift_type: byType.results,
          recent_detections: recentDetections.results,
          baseline_count: (baselineCount as any)?.total ?? 0,
        },
      };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },
};
