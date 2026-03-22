// Admin Platform Maintenance Service — schedule and manage platform maintenance windows

export const adminPlatformMaintenanceService = {
  /** List all maintenance windows ordered by scheduled start */
  async listWindows(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM platform_maintenance_windows ORDER BY scheduled_start DESC`
      ).all();
      return { success: true, data: rows.results };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** Create a new maintenance window */
  async createWindow(db: any, data: {
    title: string;
    description?: string;
    scheduled_start: string;
    scheduled_end: string;
    status?: string;
    affected_services?: string;
  }): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const id = crypto.randomUUID();
      const result = await db.prepare(
        `INSERT INTO platform_maintenance_windows
           (id, title, description, scheduled_start, scheduled_end, status, affected_services)
         VALUES (?, ?, ?, ?, ?, ?, ?)
         RETURNING *`
      ).bind(
        id,
        data.title,
        data.description ?? null,
        data.scheduled_start,
        data.scheduled_end,
        data.status ?? 'scheduled',
        data.affected_services ?? null
      ).first();
      return { success: true, data: result };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** List notifications for all maintenance windows */
  async getNotifications(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM platform_maintenance_notifications ORDER BY created_at DESC`
      ).all();
      return { success: true, data: rows.results };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** Aggregate dashboard stats for maintenance windows */
  async getDashboard(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const [totalsResult, byStatusResult, upcomingResult, notifResult] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as total FROM platform_maintenance_windows`).first(),
        db.prepare(`SELECT status, COUNT(*) as count FROM platform_maintenance_windows GROUP BY status`).all(),
        db.prepare(
          `SELECT * FROM platform_maintenance_windows
           WHERE status = 'scheduled'
           ORDER BY scheduled_start ASC LIMIT 5`
        ).all(),
        db.prepare(
          `SELECT COUNT(*) as total, SUM(recipient_count) as total_recipients
           FROM platform_maintenance_notifications`
        ).first(),
      ]);

      const byStatus: Record<string, number> = {};
      for (const row of (byStatusResult?.results ?? [])) {
        byStatus[row.status] = row.count;
      }

      return {
        success: true,
        data: {
          total_windows: totalsResult?.total ?? 0,
          windows_by_status: byStatus,
          upcoming_windows: upcomingResult?.results ?? [],
          total_notifications: notifResult?.total ?? 0,
          total_recipients_notified: notifResult?.total_recipients ?? 0,
        },
      };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },
};
