/**
 * Audit Streaming Service — manages stream configs and delivery records.
 * Supports webhook, s3, syslog destinations with event-type filtering.
 */

import type { D1Database } from '@cloudflare/workers-types';

interface StreamConfig {
  stream_type: string;
  destination_url: string;
  auth_header?: string;
  event_filters?: string[];
}

interface StreamConfigRow {
  id: string;
  tenant_id: string;
  stream_type: string;
  destination_url: string;
  auth_header: string | null;
  event_filters: string;
  is_active: number;
  created_at: string;
  updated_at: string;
}

interface DeliveryRow {
  id: string;
  config_id: string;
  event_type: string;
  payload: string;
  status: string;
  attempts: number;
  last_error: string | null;
  created_at: string;
  delivered_at: string | null;
}

/** Create a new stream destination config for a tenant */
export async function createStreamConfig(
  db: D1Database,
  tenantId: string,
  config: StreamConfig,
): Promise<StreamConfigRow> {
  const id = crypto.randomUUID();
  const filters = JSON.stringify(config.event_filters ?? []);
  await db
    .prepare(
      `INSERT INTO audit_stream_configs
        (id, tenant_id, stream_type, destination_url, auth_header, event_filters)
       VALUES (?, ?, ?, ?, ?, ?)`,
    )
    .bind(id, tenantId, config.stream_type, config.destination_url, config.auth_header ?? null, filters)
    .run();

  return db
    .prepare('SELECT * FROM audit_stream_configs WHERE id = ?')
    .bind(id)
    .first<StreamConfigRow>() as Promise<StreamConfigRow>;
}

/** List all stream configs for a tenant */
export async function getStreamConfigs(db: D1Database, tenantId: string): Promise<StreamConfigRow[]> {
  const result = await db
    .prepare('SELECT * FROM audit_stream_configs WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all<StreamConfigRow>();
  return result.results;
}

/** Update stream config fields (only provided fields are updated) */
export async function updateStreamConfig(
  db: D1Database,
  tenantId: string,
  configId: string,
  updates: Partial<StreamConfig & { is_active: number }>,
): Promise<StreamConfigRow | null> {
  const fields: string[] = [];
  const values: unknown[] = [];

  if (updates.stream_type !== undefined) { fields.push('stream_type = ?'); values.push(updates.stream_type); }
  if (updates.destination_url !== undefined) { fields.push('destination_url = ?'); values.push(updates.destination_url); }
  if (updates.auth_header !== undefined) { fields.push('auth_header = ?'); values.push(updates.auth_header); }
  if (updates.event_filters !== undefined) { fields.push('event_filters = ?'); values.push(JSON.stringify(updates.event_filters)); }
  if (updates.is_active !== undefined) { fields.push('is_active = ?'); values.push(updates.is_active); }

  if (fields.length === 0) return null;

  fields.push("updated_at = datetime('now')");
  values.push(configId, tenantId);

  await db
    .prepare(`UPDATE audit_stream_configs SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`)
    .bind(...values)
    .run();

  return db
    .prepare('SELECT * FROM audit_stream_configs WHERE id = ? AND tenant_id = ?')
    .bind(configId, tenantId)
    .first<StreamConfigRow>();
}

/** Delete a stream config owned by the tenant */
export async function deleteStreamConfig(db: D1Database, tenantId: string, configId: string): Promise<boolean> {
  const result = await db
    .prepare('DELETE FROM audit_stream_configs WHERE id = ? AND tenant_id = ?')
    .bind(configId, tenantId)
    .run();
  return (result.meta?.changes ?? 0) > 0;
}

/** Publish an event: create delivery records for matching active configs */
export async function publishEvent(
  db: D1Database,
  tenantId: string,
  eventType: string,
  payload: Record<string, unknown>,
): Promise<string[]> {
  const configs = await db
    .prepare('SELECT * FROM audit_stream_configs WHERE tenant_id = ? AND is_active = 1')
    .bind(tenantId)
    .all<StreamConfigRow>();

  const deliveryIds: string[] = [];
  const payloadStr = JSON.stringify(payload);

  for (const cfg of configs.results) {
    const filters: string[] = JSON.parse(cfg.event_filters || '[]');
    // Empty filters = accept all events
    if (filters.length > 0 && !filters.includes(eventType)) continue;

    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO audit_stream_deliveries (id, config_id, event_type, payload)
         VALUES (?, ?, ?, ?)`,
      )
      .bind(id, cfg.id, eventType, payloadStr)
      .run();
    deliveryIds.push(id);
  }

  return deliveryIds;
}

/** Get pending deliveries for admin processing (up to limit) */
export async function getPendingDeliveries(db: D1Database, limit = 50): Promise<DeliveryRow[]> {
  const cap = Math.min(limit, 200);
  const result = await db
    .prepare("SELECT * FROM audit_stream_deliveries WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?")
    .bind(cap)
    .all<DeliveryRow>();
  return result.results;
}

/** Mark a delivery as successfully delivered */
export async function markDelivered(db: D1Database, deliveryId: string): Promise<boolean> {
  const result = await db
    .prepare("UPDATE audit_stream_deliveries SET status = 'delivered', delivered_at = datetime('now') WHERE id = ?")
    .bind(deliveryId)
    .run();
  return (result.meta?.changes ?? 0) > 0;
}

/** Mark a delivery as failed, increment attempts, record error */
export async function markFailed(db: D1Database, deliveryId: string, error: string): Promise<boolean> {
  const result = await db
    .prepare(
      `UPDATE audit_stream_deliveries
       SET status = 'failed', attempts = attempts + 1, last_error = ?
       WHERE id = ?`,
    )
    .bind(error.slice(0, 500), deliveryId)
    .run();
  return (result.meta?.changes ?? 0) > 0;
}

/** Get delivery success/fail statistics for a tenant */
export async function getDeliveryStats(
  db: D1Database,
  tenantId: string,
): Promise<{ total: number; delivered: number; failed: number; pending: number }> {
  const row = await db
    .prepare(
      `SELECT
         COUNT(*) as total,
         SUM(CASE WHEN d.status = 'delivered' THEN 1 ELSE 0 END) as delivered,
         SUM(CASE WHEN d.status = 'failed' THEN 1 ELSE 0 END) as failed,
         SUM(CASE WHEN d.status = 'pending' THEN 1 ELSE 0 END) as pending
       FROM audit_stream_deliveries d
       JOIN audit_stream_configs c ON d.config_id = c.id
       WHERE c.tenant_id = ?`,
    )
    .bind(tenantId)
    .first<{ total: number; delivered: number; failed: number; pending: number }>();

  return {
    total: row?.total ?? 0,
    delivered: row?.delivered ?? 0,
    failed: row?.failed ?? 0,
    pending: row?.pending ?? 0,
  };
}

/** Reset all failed deliveries for a config back to pending for retry */
export async function retryFailedDeliveries(db: D1Database, configId: string): Promise<number> {
  const result = await db
    .prepare(
      "UPDATE audit_stream_deliveries SET status = 'pending', last_error = NULL WHERE config_id = ? AND status = 'failed'",
    )
    .bind(configId)
    .run();
  return result.meta?.changes ?? 0;
}
