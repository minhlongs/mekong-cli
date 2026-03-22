/**
 * Tenant API Event Sourcing Service — append-only event store + snapshot management
 *
 * Operations: listEvents, createEvent, getSnapshots, getAdminOverview
 * Storage: D1 tables api_event_store + api_event_snapshots
 */

export const tenantApiEventSourcingService = {
  /** List events for a tenant, optional ?aggregate_id + ?aggregate_type filters, newest first */
  async listEvents(
    db: any,
    tenantId: string,
    opts: { aggregateId?: string; aggregateType?: string; limit?: number } = {}
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const safeLimit = Math.min(Math.max(opts.limit ?? 100, 1), 500);
      const conditions: string[] = ['tenant_id = ?'];
      const bindings: any[] = [tenantId];

      if (opts.aggregateId) {
        conditions.push('aggregate_id = ?');
        bindings.push(opts.aggregateId);
      }
      if (opts.aggregateType) {
        conditions.push('aggregate_type = ?');
        bindings.push(opts.aggregateType);
      }

      bindings.push(safeLimit);
      const query = `SELECT * FROM api_event_store WHERE ${conditions.join(' AND ')} ORDER BY version ASC LIMIT ?`;
      const { results } = await db.prepare(query).bind(...bindings).all();
      return { success: true, data: results };
    } catch (e) {
      return { success: false, error: String(e) };
    }
  },

  /** Append a new event to the store for a tenant */
  async createEvent(
    db: any,
    tenantId: string,
    body: {
      aggregate_id: string;
      aggregate_type: string;
      event_type: string;
      event_data: string;
      version?: number;
    }
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      const version = body.version ?? 1;

      await db
        .prepare(
          `INSERT INTO api_event_store
             (id, tenant_id, aggregate_id, aggregate_type, event_type, event_data, version, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(id, tenantId, body.aggregate_id, body.aggregate_type, body.event_type, body.event_data, version, now)
        .run();

      const row = await db.prepare('SELECT * FROM api_event_store WHERE id = ?').bind(id).first();
      return { success: true, data: row };
    } catch (e) {
      return { success: false, error: String(e) };
    }
  },

  /** List snapshots for a tenant, optional ?aggregate_id + ?aggregate_type filters */
  async getSnapshots(
    db: any,
    tenantId: string,
    opts: { aggregateId?: string; aggregateType?: string; limit?: number } = {}
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const safeLimit = Math.min(Math.max(opts.limit ?? 50, 1), 200);
      const conditions: string[] = ['tenant_id = ?'];
      const bindings: any[] = [tenantId];

      if (opts.aggregateId) {
        conditions.push('aggregate_id = ?');
        bindings.push(opts.aggregateId);
      }
      if (opts.aggregateType) {
        conditions.push('aggregate_type = ?');
        bindings.push(opts.aggregateType);
      }

      bindings.push(safeLimit);
      const query = `SELECT * FROM api_event_snapshots WHERE ${conditions.join(' AND ')} ORDER BY version DESC LIMIT ?`;
      const { results } = await db.prepare(query).bind(...bindings).all();
      return { success: true, data: results };
    } catch (e) {
      return { success: false, error: String(e) };
    }
  },

  /** Admin overview: event + snapshot counts across all tenants */
  async getAdminOverview(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const [evtRow, snapRow] = await db.batch([
        db.prepare(
          `SELECT COUNT(*) as total_events,
                  COUNT(DISTINCT tenant_id) as tenants_with_events,
                  COUNT(DISTINCT aggregate_type) as aggregate_types
           FROM api_event_store`
        ),
        db.prepare(
          `SELECT COUNT(*) as total_snapshots,
                  COUNT(DISTINCT tenant_id) as tenants_with_snapshots
           FROM api_event_snapshots`
        ),
      ]);

      const evt = (evtRow.results as any[])[0] ?? {};
      const snap = (snapRow.results as any[])[0] ?? {};

      return {
        success: true,
        data: {
          events_total: evt.total_events ?? 0,
          tenants_with_events: evt.tenants_with_events ?? 0,
          aggregate_types: evt.aggregate_types ?? 0,
          snapshots_total: snap.total_snapshots ?? 0,
          tenants_with_snapshots: snap.tenants_with_snapshots ?? 0,
        },
      };
    } catch (e) {
      return { success: false, error: String(e) };
    }
  },
};
