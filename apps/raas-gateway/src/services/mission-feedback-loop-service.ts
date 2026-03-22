// Mission Feedback Loop Service — CRUD for mission feedback + resolution actions

export const missionFeedbackLoopService = {
  async listFeedback(db: any, tenantId: string, missionId?: string): Promise<unknown[]> {
    try {
      let sql = `SELECT * FROM mission_feedback WHERE tenant_id = ?`;
      const binds: unknown[] = [tenantId];
      if (missionId) { sql += ` AND mission_id = ?`; binds.push(missionId); }
      sql += ` ORDER BY created_at DESC LIMIT 200`;
      const rows = await db.prepare(sql).bind(...binds).all();
      return rows.results as unknown[];
    } catch (e: unknown) {
      throw new Error(`listFeedback failed: ${(e as Error).message}`);
    }
  },

  async createFeedback(db: any, tenantId: string, data: {
    mission_id: string;
    rating: number;
    feedback_text?: string;
    feedback_type?: string;
  }): Promise<unknown> {
    try {
      if (!data.mission_id) throw new Error('mission_id is required');
      if (data.rating == null) throw new Error('rating is required');
      if (data.rating < 1 || data.rating > 5) throw new Error('rating must be 1-5');
      return await db.prepare(
        `INSERT INTO mission_feedback (id, tenant_id, mission_id, rating, feedback_text, feedback_type)
         VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
      ).bind(
        crypto.randomUUID(), tenantId, data.mission_id, data.rating,
        data.feedback_text ?? null,
        data.feedback_type ?? 'quality'
      ).first();
    } catch (e: unknown) {
      throw new Error(`createFeedback failed: ${(e as Error).message}`);
    }
  },

  async getActions(db: any, tenantId: string, feedbackId?: string): Promise<unknown[]> {
    try {
      let sql = `SELECT * FROM mission_feedback_actions WHERE tenant_id = ?`;
      const binds: unknown[] = [tenantId];
      if (feedbackId) { sql += ` AND feedback_id = ?`; binds.push(feedbackId); }
      sql += ` ORDER BY created_at DESC LIMIT 200`;
      const rows = await db.prepare(sql).bind(...binds).all();
      return rows.results as unknown[];
    } catch (e: unknown) {
      throw new Error(`getActions failed: ${(e as Error).message}`);
    }
  },

  async getAdminOverview(db: any): Promise<unknown> {
    try {
      const [totalFeedback, avgRating, byType, openActions] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM mission_feedback`).first() as Promise<{ count: number } | null>,
        db.prepare(`SELECT ROUND(AVG(rating), 2) as avg FROM mission_feedback`).first() as Promise<{ avg: number } | null>,
        db.prepare(
          `SELECT feedback_type, COUNT(*) as count, ROUND(AVG(rating), 2) as avg_rating
           FROM mission_feedback GROUP BY feedback_type`
        ).all(),
        db.prepare(`SELECT COUNT(*) as count FROM mission_feedback_actions WHERE resolved = 0`).first() as Promise<{ count: number } | null>,
      ]);

      const byTypeMap: Record<string, { count: number; avg_rating: number }> = {};
      for (const row of (byType.results as { feedback_type: string; count: number; avg_rating: number }[])) {
        byTypeMap[row.feedback_type] = { count: row.count, avg_rating: row.avg_rating };
      }

      return {
        total_feedback: totalFeedback?.count ?? 0,
        average_rating: avgRating?.avg ?? 0,
        by_type: byTypeMap,
        open_actions: openActions?.count ?? 0,
      };
    } catch (e: unknown) {
      throw new Error(`getAdminOverview failed: ${(e as Error).message}`);
    }
  },
};
