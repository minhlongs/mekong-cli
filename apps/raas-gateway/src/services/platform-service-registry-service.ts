/**
 * Platform Service Registry Service — CRUD for platform_services + health check log queries
 * Functions: listServices, registerService, getHealthChecks, getDashboard
 */

export const platformServiceRegistryService = {
  /** List all registered platform services ordered by created_at desc */
  async listServices(db: any) {
    try {
      const result = await db.prepare(
        'SELECT * FROM platform_services ORDER BY created_at DESC'
      ).all();
      return result.results ?? [];
    } catch (err) {
      throw new Error(`listServices failed: ${String(err)}`);
    }
  },

  /** Register a new platform service */
  async registerService(db: any, data: any) {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db.prepare(
        `INSERT INTO platform_services
          (id, service_name, service_type, endpoint_url, health_check_url, status, version, metadata_json, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(
        id,
        data.service_name,
        data.service_type,
        data.endpoint_url,
        data.health_check_url ?? null,
        data.status ?? 'active',
        data.version ?? '1.0.0',
        data.metadata_json ?? '{}',
        now,
        now
      ).run();
      return { id, ...data, created_at: now, updated_at: now };
    } catch (err) {
      throw new Error(`registerService failed: ${String(err)}`);
    }
  },

  /** Get health check history for a specific service (latest 50) */
  async getHealthChecks(db: any, serviceId?: string) {
    try {
      let result;
      if (serviceId) {
        result = await db.prepare(
          'SELECT * FROM service_health_checks WHERE service_id = ? ORDER BY checked_at DESC LIMIT 50'
        ).bind(serviceId).all();
      } else {
        result = await db.prepare(
          'SELECT * FROM service_health_checks ORDER BY checked_at DESC LIMIT 50'
        ).all();
      }
      return result.results ?? [];
    } catch (err) {
      throw new Error(`getHealthChecks failed: ${String(err)}`);
    }
  },

  /** Dashboard summary: total/active/inactive services + recent health check counts */
  async getDashboard(db: any) {
    try {
      const [total, active, inactive, recentChecks] = await Promise.all([
        db.prepare('SELECT COUNT(*) as count FROM platform_services').first(),
        db.prepare("SELECT COUNT(*) as count FROM platform_services WHERE status = 'active'").first(),
        db.prepare("SELECT COUNT(*) as count FROM platform_services WHERE status != 'active'").first(),
        db.prepare(
          "SELECT COUNT(*) as count FROM service_health_checks WHERE checked_at >= datetime('now', '-1 hour')"
        ).first(),
      ]);
      return {
        services: {
          total: total?.count ?? 0,
          active: active?.count ?? 0,
          inactive: inactive?.count ?? 0,
        },
        health_checks: {
          last_hour: recentChecks?.count ?? 0,
        },
      };
    } catch (err) {
      throw new Error(`getDashboard failed: ${String(err)}`);
    }
  },
};
