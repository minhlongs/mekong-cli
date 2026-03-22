// Tenant Session Management Service — CRUD for sessions and session event history

export const tenantSessionManagementService = {
  async listSessions(db: any, tenantId: string): Promise<unknown[]> {
    try {
      const { results } = await db.prepare(
        `SELECT * FROM sessions WHERE tenant_id = ? ORDER BY created_at DESC`
      ).bind(tenantId).all();
      return results;
    } catch (e: unknown) {
      throw new Error(`listSessions failed: ${(e as Error).message}`);
    }
  },

  async createSession(db: any, tenantId: string, data: {
    user_id: string;
    device_info?: string;
    ip_address?: string;
    expires_at?: string;
  }): Promise<unknown> {
    try {
      if (!data.user_id) throw new Error('user_id is required');

      return db.prepare(
        `INSERT INTO sessions (id, tenant_id, user_id, device_info, ip_address, expires_at)
         VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
      ).bind(
        crypto.randomUUID(),
        tenantId,
        data.user_id,
        data.device_info ?? null,
        data.ip_address ?? null,
        data.expires_at ?? null
      ).first();
    } catch (e: unknown) {
      throw new Error(`createSession failed: ${(e as Error).message}`);
    }
  },

  async getEvents(db: any, tenantId: string): Promise<unknown[]> {
    try {
      const { results } = await db.prepare(
        `SELECT * FROM session_events WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 100`
      ).bind(tenantId).all();
      return results;
    } catch (e: unknown) {
      throw new Error(`getEvents failed: ${(e as Error).message}`);
    }
  },

  async getAdminOverview(db: any): Promise<unknown> {
    try {
      const [sessionsTotal, activeSessions, eventsTotal, expiredSessions] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM sessions`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM sessions WHERE is_active = 1`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM session_events`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM sessions WHERE is_active = 0`).first(),
      ]);

      return {
        sessions_total: (sessionsTotal as { count: number } | null)?.count ?? 0,
        sessions_active: (activeSessions as { count: number } | null)?.count ?? 0,
        events_total: (eventsTotal as { count: number } | null)?.count ?? 0,
        sessions_inactive: (expiredSessions as { count: number } | null)?.count ?? 0,
      };
    } catch (e: unknown) {
      throw new Error(`getAdminOverview failed: ${(e as Error).message}`);
    }
  },
};
