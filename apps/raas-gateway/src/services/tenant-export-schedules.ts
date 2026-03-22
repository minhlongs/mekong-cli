// Tenant Export Schedules Service — CRUD for export schedules and run history

export const tenantExportSchedulesService = {
  async listSchedules(db: any, tenantId: string): Promise<unknown[]> {
    try {
      const { results } = await db.prepare(
        `SELECT * FROM export_schedules WHERE tenant_id = ? ORDER BY created_at DESC`
      ).bind(tenantId).all();
      return results;
    } catch (e: unknown) {
      throw new Error(`listSchedules failed: ${(e as Error).message}`);
    }
  },

  async createSchedule(db: any, tenantId: string, data: {
    export_type: string;
    format?: string;
    cron_expression: string;
    destination: string;
    is_active?: number;
  }): Promise<unknown> {
    try {
      if (!data.export_type) throw new Error('export_type is required');
      if (!data.cron_expression) throw new Error('cron_expression is required');
      if (!data.destination) throw new Error('destination is required');

      return db.prepare(
        `INSERT INTO export_schedules (id, tenant_id, export_type, format, cron_expression, destination, is_active)
         VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
      ).bind(
        crypto.randomUUID(),
        tenantId,
        data.export_type,
        data.format ?? 'csv',
        data.cron_expression,
        data.destination,
        data.is_active ?? 1
      ).first();
    } catch (e: unknown) {
      throw new Error(`createSchedule failed: ${(e as Error).message}`);
    }
  },

  async getRuns(db: any, tenantId: string): Promise<unknown[]> {
    try {
      const { results } = await db.prepare(
        `SELECT * FROM export_runs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 100`
      ).bind(tenantId).all();
      return results;
    } catch (e: unknown) {
      throw new Error(`getRuns failed: ${(e as Error).message}`);
    }
  },

  async getAdminOverview(db: any): Promise<unknown> {
    try {
      const [schedulesTotal, activeSchedules, runsTotal, recentFailed] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM export_schedules`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM export_schedules WHERE is_active = 1`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM export_runs`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM export_runs WHERE status = 'failed'`).first(),
      ]);

      return {
        schedules_total: (schedulesTotal as { count: number } | null)?.count ?? 0,
        schedules_active: (activeSchedules as { count: number } | null)?.count ?? 0,
        runs_total: (runsTotal as { count: number } | null)?.count ?? 0,
        runs_failed: (recentFailed as { count: number } | null)?.count ?? 0,
      };
    } catch (e: unknown) {
      throw new Error(`getAdminOverview failed: ${(e as Error).message}`);
    }
  },
};
