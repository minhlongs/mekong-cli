/**
 * Tenant Webhooks V3 Service — CRUD for subscriptions, deliveries, event types, and stats.
 * Operates on webhook_subscriptions_v3, webhook_deliveries_v3, webhook_event_types tables.
 */

export const tenantWebhooksV3Service = {
  /** List all webhook subscriptions for a tenant */
  async listSubscriptions(db: any, tenantId: string) {
    const result = await db
      .prepare('SELECT * FROM webhook_subscriptions_v3 WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return result.results;
  },

  /** Create a new webhook subscription — auto-generates id and signing secret */
  async createSubscription(db: any, tenantId: string, data: Record<string, any>) {
    const id = crypto.randomUUID();
    const secret = crypto.randomUUID().replace(/-/g, '');
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO webhook_subscriptions_v3
          (id, tenant_id, url, events_json, secret, status, retry_policy, max_retries, timeout_ms, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        data.url,
        data.events_json ?? '["*"]',
        data.secret ?? secret,
        data.status ?? 'active',
        data.retry_policy ?? 'exponential',
        data.max_retries ?? 5,
        data.timeout_ms ?? 30000,
        now,
        now
      )
      .run();
    return { id, secret: data.secret ?? secret };
  },

  /** Get a single subscription — verifies tenant ownership */
  async getSubscription(db: any, tenantId: string, id: string) {
    return db
      .prepare('SELECT * FROM webhook_subscriptions_v3 WHERE id = ? AND tenant_id = ?')
      .bind(id, tenantId)
      .first();
  },

  /** Update allowed fields on a subscription */
  async updateSubscription(db: any, tenantId: string, id: string, data: Record<string, any>) {
    const fields: string[] = [];
    const values: any[] = [];
    const allowed = ['url', 'events_json', 'status', 'retry_policy', 'max_retries', 'timeout_ms'];
    for (const key of allowed) {
      if (data[key] !== undefined) {
        fields.push(`${key} = ?`);
        values.push(data[key]);
      }
    }
    if (!fields.length) return null;
    fields.push('updated_at = ?');
    values.push(new Date().toISOString(), id, tenantId);
    await db
      .prepare(`UPDATE webhook_subscriptions_v3 SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`)
      .bind(...values)
      .run();
    return this.getSubscription(db, tenantId, id);
  },

  /** Delete a subscription (tenant-scoped) */
  async deleteSubscription(db: any, tenantId: string, id: string) {
    await db
      .prepare('DELETE FROM webhook_subscriptions_v3 WHERE id = ? AND tenant_id = ?')
      .bind(id, tenantId)
      .run();
  },

  /** Create a test delivery record for a subscription */
  async testSubscription(db: any, tenantId: string, id: string) {
    const sub = await this.getSubscription(db, tenantId, id);
    if (!sub) return null;
    const deliveryId = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO webhook_deliveries_v3
          (id, subscription_id, event_type, payload_json, status, created_at)
         VALUES (?, ?, 'test.ping', ?, 'pending', ?)`
      )
      .bind(deliveryId, id, JSON.stringify({ event: 'test.ping', timestamp: new Date().toISOString() }), new Date().toISOString())
      .run();
    return { delivery_id: deliveryId, subscription_id: id };
  },

  /** List deliveries for a subscription (tenant-scoped via join) */
  async listDeliveries(db: any, tenantId: string, subscriptionId: string, filters?: Record<string, any>) {
    let query = `SELECT d.* FROM webhook_deliveries_v3 d
      JOIN webhook_subscriptions_v3 s ON s.id = d.subscription_id
      WHERE d.subscription_id = ? AND s.tenant_id = ?`;
    const binds: any[] = [subscriptionId, tenantId];
    if (filters?.status) { query += ' AND d.status = ?'; binds.push(filters.status); }
    query += ' ORDER BY d.created_at DESC LIMIT 100';
    const result = await db.prepare(query).bind(...binds).all();
    return result.results;
  },

  /** Reset a delivery to pending for re-processing */
  async retryDelivery(db: any, deliveryId: string) {
    await db
      .prepare(`UPDATE webhook_deliveries_v3 SET status = 'pending', attempts = 0 WHERE id = ?`)
      .bind(deliveryId)
      .run();
  },

  /** List all registered event types */
  async listEventTypes(db: any) {
    const result = await db.prepare('SELECT * FROM webhook_event_types ORDER BY category, event_name').all();
    return result.results;
  },

  /** Delivery success/failure stats for a tenant */
  async getDeliveryStats(db: any, tenantId: string) {
    const result = await db
      .prepare(
        `SELECT d.status, COUNT(*) as count FROM webhook_deliveries_v3 d
         JOIN webhook_subscriptions_v3 s ON s.id = d.subscription_id
         WHERE s.tenant_id = ? GROUP BY d.status`
      )
      .bind(tenantId)
      .all();
    return result.results;
  },

  /** Admin: global counts across all tenants */
  async getAdminOverview(db: any) {
    const [subs, deliveries] = await Promise.all([
      db.prepare('SELECT COUNT(*) as total, status, COUNT(DISTINCT tenant_id) as tenants FROM webhook_subscriptions_v3 GROUP BY status').all(),
      db.prepare('SELECT status, COUNT(*) as count FROM webhook_deliveries_v3 GROUP BY status').all(),
    ]);
    return { subscriptions: subs.results, deliveries: deliveries.results };
  },
};
