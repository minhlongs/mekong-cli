/**
 * Tenant API Rate Burst Service — token-bucket config management + event logging
 *
 * Operations: listConfigs, createConfig, getEvents, getAdminOverview
 * Storage: D1 tables rate_burst_configs + rate_burst_events
 */

export const tenantApiRateBurstService = {
  /** List active burst configs for a tenant */
  async listConfigs(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare('SELECT * FROM rate_burst_configs WHERE tenant_id = ? AND is_active = 1 ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return results as any[];
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'DB error listing configs');
    }
  },

  /** Insert a new burst config for a tenant */
  async createConfig(
    db: any,
    tenantId: string,
    body: {
      endpoint_pattern: string;
      bucket_size?: number;
      refill_rate?: number;
      refill_interval_ms?: number;
    }
  ) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    try {
      await db
        .prepare(
          `INSERT INTO rate_burst_configs
             (id, tenant_id, endpoint_pattern, bucket_size, refill_rate, refill_interval_ms, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          body.endpoint_pattern,
          body.bucket_size ?? 100,
          body.refill_rate ?? 10,
          body.refill_interval_ms ?? 1000,
          now,
          now
        )
        .run();
      return { id, tenant_id: tenantId, endpoint_pattern: body.endpoint_pattern };
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'DB error creating config');
    }
  },

  /** Fetch burst events for a tenant, newest first, optional limit */
  async getEvents(db: any, tenantId: string, limit = 100) {
    const safeLimit = Math.min(Math.max(limit, 1), 500);
    try {
      const { results } = await db
        .prepare(
          'SELECT * FROM rate_burst_events WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
        )
        .bind(tenantId, safeLimit)
        .all();
      return results as any[];
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'DB error fetching events');
    }
  },

  /** Admin overview: total configs, active configs, total events, throttled count */
  async getAdminOverview(db: any) {
    try {
      const [cfgRow, evtRow] = await db.batch([
        db.prepare('SELECT COUNT(*) as total, SUM(is_active) as active FROM rate_burst_configs'),
        db.prepare('SELECT COUNT(*) as total, SUM(was_throttled) as throttled FROM rate_burst_events'),
      ]);
      const cfg = (cfgRow.results as any[])[0] ?? {};
      const evt = (evtRow.results as any[])[0] ?? {};
      return {
        configs_total: cfg.total ?? 0,
        configs_active: cfg.active ?? 0,
        events_total: evt.total ?? 0,
        events_throttled: evt.throttled ?? 0,
      };
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'DB error fetching overview');
    }
  },
};
