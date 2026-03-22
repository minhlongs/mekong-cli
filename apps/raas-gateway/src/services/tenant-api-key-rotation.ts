/**
 * Tenant API Key Rotation Service — schedule management + rotation history
 *
 * Operations: listRotations, createRotation, getHistory, getAdminOverview
 * Storage: D1 tables api_key_rotations + api_key_rotation_history
 */

export const tenantApiKeyRotationService = {
  /** List all rotation schedules for a tenant, newest first */
  async listRotations(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare(
          'SELECT * FROM api_key_rotations WHERE tenant_id = ? ORDER BY created_at DESC'
        )
        .bind(tenantId)
        .all();
      return { success: true, data: results as any[] };
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : 'DB error listing rotations' };
    }
  },

  /** Create a new API key rotation schedule for a tenant */
  async createRotation(
    db: any,
    tenantId: string,
    body: {
      key_name: string;
      rotation_interval_days?: number;
      next_rotation_at?: string;
    }
  ) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const intervalDays = body.rotation_interval_days ?? 90;

    // Compute next_rotation_at if not provided
    const nextRotation = body.next_rotation_at ?? (() => {
      const d = new Date();
      d.setDate(d.getDate() + intervalDays);
      return d.toISOString();
    })();

    try {
      await db
        .prepare(
          `INSERT INTO api_key_rotations
             (id, tenant_id, key_name, rotation_interval_days, next_rotation_at, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'active', ?, ?)`
        )
        .bind(id, tenantId, body.key_name, intervalDays, nextRotation, now, now)
        .run();
      return {
        success: true,
        data: { id, tenant_id: tenantId, key_name: body.key_name, rotation_interval_days: intervalDays, next_rotation_at: nextRotation },
      };
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : 'DB error creating rotation' };
    }
  },

  /** Fetch rotation history for a tenant, newest first */
  async getHistory(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare(
          'SELECT * FROM api_key_rotation_history WHERE tenant_id = ? ORDER BY created_at DESC'
        )
        .bind(tenantId)
        .all();
      return { success: true, data: results as any[] };
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : 'DB error fetching history' };
    }
  },

  /** Admin overview: total rotations, active count, recent rotation events */
  async getAdminOverview(db: any) {
    try {
      const [rotRow, histRow] = await db.batch([
        db.prepare("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active FROM api_key_rotations"),
        db.prepare('SELECT COUNT(*) as total FROM api_key_rotation_history'),
      ]);
      const rot = (rotRow.results as any[])[0] ?? {};
      const hist = (histRow.results as any[])[0] ?? {};

      const { results: recent } = await db
        .prepare('SELECT * FROM api_key_rotations ORDER BY updated_at DESC LIMIT 10')
        .all();

      return {
        success: true,
        data: {
          rotations_total: rot.total ?? 0,
          rotations_active: rot.active ?? 0,
          history_total: hist.total ?? 0,
          recent: recent as any[],
        },
      };
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : 'DB error fetching overview' };
    }
  },
};
