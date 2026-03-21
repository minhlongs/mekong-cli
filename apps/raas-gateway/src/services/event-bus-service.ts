/**
 * Event Bus Service — internal pub/sub for mission lifecycle coordination.
 * Persists events to D1, supports subscriptions and webhook delivery.
 */

export type EventType =
  | 'mission.created' | 'mission.queued' | 'mission.running'
  | 'mission.completed' | 'mission.failed' | 'mission.cancelled'
  | 'tenant.upgraded' | 'tenant.suspended' | 'credit.low' | 'credit.depleted';

export interface BusEvent {
  id: string;
  type: EventType;
  tenant_id: string;
  payload: Record<string, any>;
  created_at: string;
  processed: boolean;
}

export interface EventSubscription {
  id: string;
  tenant_id: string;
  event_types: string[];
  webhook_url: string;
  active: boolean;
  created_at: string;
}

interface EventHistoryOptions {
  type?: string;
  limit?: number;
  offset?: number;
}

/** Insert a new event into the event_bus table. Returns the new event id. */
export async function emitEvent(
  db: D1Database,
  type: EventType,
  tenantId: string,
  payload: Record<string, any>,
): Promise<string> {
  const id = crypto.randomUUID();
  const createdAt = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO event_bus (id, type, tenant_id, payload, processed, created_at)
       VALUES (?, ?, ?, ?, 0, ?)`,
    )
    .bind(id, type, tenantId, JSON.stringify(payload), createdAt)
    .run();
  return id;
}

/** Fetch unprocessed events ordered by creation time (oldest first). */
export async function getUnprocessedEvents(
  db: D1Database,
  limit = 50,
): Promise<BusEvent[]> {
  const rows = await db
    .prepare(
      `SELECT id, type, tenant_id, payload, processed, created_at
       FROM event_bus WHERE processed = 0 ORDER BY created_at ASC LIMIT ?`,
    )
    .bind(limit)
    .all<Record<string, any>>();
  return (rows.results ?? []).map(mapRow);
}

/** Mark a batch of events as processed. */
export async function markProcessed(
  db: D1Database,
  eventIds: string[],
): Promise<void> {
  if (!eventIds.length) return;
  const placeholders = eventIds.map(() => '?').join(', ');
  await db
    .prepare(`UPDATE event_bus SET processed = 1 WHERE id IN (${placeholders})`)
    .bind(...eventIds)
    .run();
}

/** Paginated event history for a tenant, optionally filtered by type. */
export async function getEventHistory(
  db: D1Database,
  tenantId: string,
  options: EventHistoryOptions = {},
): Promise<{ events: BusEvent[]; total: number }> {
  const { type, limit = 20, offset = 0 } = options;
  const typeFilter = type ? 'AND type = ?' : '';
  const binds: any[] = type ? [tenantId, type, limit, offset] : [tenantId, limit, offset];

  const rows = await db
    .prepare(
      `SELECT id, type, tenant_id, payload, processed, created_at
       FROM event_bus WHERE tenant_id = ? ${typeFilter}
       ORDER BY created_at DESC LIMIT ? OFFSET ?`,
    )
    .bind(...binds)
    .all<Record<string, any>>();

  const countRow = await db
    .prepare(`SELECT COUNT(*) as cnt FROM event_bus WHERE tenant_id = ? ${typeFilter}`)
    .bind(...(type ? [tenantId, type] : [tenantId]))
    .first<{ cnt: number }>();

  return {
    events: (rows.results ?? []).map(mapRow),
    total: countRow?.cnt ?? 0,
  };
}

/** Count events by type for a tenant (or all tenants) across 24h / 7d / 30d windows. */
export async function getEventStats(
  db: D1Database,
  tenantId?: string,
): Promise<Record<string, { last_24h: number; last_7d: number; last_30d: number }>> {
  const tenantFilter = tenantId ? 'AND tenant_id = ?' : '';
  const binds = tenantId ? [tenantId] : [];

  const rows = await db
    .prepare(
      `SELECT type,
         SUM(CASE WHEN created_at >= datetime('now', '-1 day')  THEN 1 ELSE 0 END) as last_24h,
         SUM(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 ELSE 0 END) as last_7d,
         COUNT(*) as last_30d
       FROM event_bus
       WHERE created_at >= datetime('now', '-30 days') ${tenantFilter}
       GROUP BY type`,
    )
    .bind(...binds)
    .all<{ type: string; last_24h: number; last_7d: number; last_30d: number }>();

  return Object.fromEntries(
    (rows.results ?? []).map((r) => [
      r.type,
      { last_24h: r.last_24h, last_7d: r.last_7d, last_30d: r.last_30d },
    ]),
  );
}

/** Delete processed events older than daysOld days. Returns deleted count. */
export async function pruneOldEvents(
  db: D1Database,
  daysOld = 30,
): Promise<number> {
  const result = await db
    .prepare(
      `DELETE FROM event_bus
       WHERE created_at < datetime('now', '-${daysOld} days') AND processed = 1`,
    )
    .run();
  return result.meta?.changes ?? 0;
}

/** Register a webhook subscription for a tenant. Returns subscription id. */
export async function subscribeToEvents(
  db: D1Database,
  tenantId: string,
  eventTypes: string[],
  webhookUrl: string,
): Promise<string> {
  const id = crypto.randomUUID();
  const createdAt = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO event_subscriptions (id, tenant_id, event_types, webhook_url, active, created_at)
       VALUES (?, ?, ?, ?, 1, ?)`,
    )
    .bind(id, tenantId, JSON.stringify(eventTypes), webhookUrl, createdAt)
    .run();
  return id;
}

/** List active subscriptions for a tenant. */
export async function getSubscriptions(
  db: D1Database,
  tenantId: string,
): Promise<EventSubscription[]> {
  const rows = await db
    .prepare(
      `SELECT id, tenant_id, event_types, webhook_url, active, created_at
       FROM event_subscriptions WHERE tenant_id = ? AND active = 1 ORDER BY created_at DESC`,
    )
    .bind(tenantId)
    .all<Record<string, any>>();

  return (rows.results ?? []).map((r) => ({
    id: r.id as string,
    tenant_id: r.tenant_id as string,
    event_types: JSON.parse(r.event_types as string) as string[],
    webhook_url: r.webhook_url as string,
    active: Boolean(r.active),
    created_at: r.created_at as string,
  }));
}

// --- helpers ---

function mapRow(r: Record<string, any>): BusEvent {
  return {
    id: r.id as string,
    type: r.type as EventType,
    tenant_id: r.tenant_id as string,
    payload: JSON.parse(r.payload as string),
    processed: Boolean(r.processed),
    created_at: r.created_at as string,
  };
}
