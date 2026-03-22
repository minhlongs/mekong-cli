// Platform Event Log Service — log, query, and manage platform events
// Covers: logEvent, getEvents, getEvent, categories, retention, purge, stats, overview

import { nanoid } from 'nanoid';

// --- Events ---

/** Log a new platform event */
export async function logEvent(
  db: any,
  data: {
    event_type: string;
    category?: string;
    source?: string;
    actor_id?: string;
    tenant_id?: string;
    payload?: Record<string, unknown>;
    severity?: string;
  }
): Promise<unknown> {
  const id = `evt_${nanoid(16)}`;
  return db.prepare(
    `INSERT INTO platform_events (id, event_type, category, source, actor_id, tenant_id, payload_json, severity)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id,
    data.event_type,
    data.category ?? 'system',
    data.source ?? 'gateway',
    data.actor_id ?? null,
    data.tenant_id ?? null,
    JSON.stringify(data.payload ?? {}),
    data.severity ?? 'info'
  ).first();
}

/** List events with optional filters */
export async function getEvents(
  db: any,
  filters?: {
    event_type?: string;
    category?: string;
    tenant_id?: string;
    severity?: string;
    since?: string;
    limit?: number;
  }
): Promise<unknown[]> {
  const conds: string[] = [];
  const binds: unknown[] = [];

  if (filters?.event_type) { conds.push('event_type = ?'); binds.push(filters.event_type); }
  if (filters?.category)   { conds.push('category = ?');   binds.push(filters.category); }
  if (filters?.tenant_id)  { conds.push('tenant_id = ?');  binds.push(filters.tenant_id); }
  if (filters?.severity)   { conds.push('severity = ?');   binds.push(filters.severity); }
  if (filters?.since)      { conds.push('created_at >= ?'); binds.push(filters.since); }

  const where = conds.length ? `WHERE ${conds.join(' AND ')}` : '';
  binds.push(Math.min(filters?.limit ?? 50, 500));

  const rows = await db.prepare(
    `SELECT * FROM platform_events ${where} ORDER BY created_at DESC LIMIT ?`
  ).bind(...binds).all();
  return rows.results;
}

/** Get a single event by id */
export async function getEvent(db: any, id: string): Promise<unknown | null> {
  return db.prepare('SELECT * FROM platform_events WHERE id = ?').bind(id).first();
}

// --- Categories ---

/** List all event categories */
export async function listCategories(db: any): Promise<unknown[]> {
  const rows = await db.prepare('SELECT * FROM event_categories ORDER BY name').all();
  return rows.results;
}

/** Create a new event category */
export async function createCategory(
  db: any,
  data: { name: string; description?: string; color?: string; icon?: string }
): Promise<unknown> {
  const id = `cat_${nanoid(10)}`;
  return db.prepare(
    `INSERT INTO event_categories (id, name, description, color, icon)
     VALUES (?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id,
    data.name,
    data.description ?? null,
    data.color ?? '#6B7280',
    data.icon ?? null
  ).first();
}

// --- Retention ---

/** Get all retention configs */
export async function getRetentionConfigs(db: any): Promise<unknown[]> {
  const rows = await db.prepare('SELECT * FROM event_retention_configs ORDER BY category').all();
  return rows.results;
}

/** Update retention config for a category */
export async function updateRetentionConfig(
  db: any,
  category: string,
  data: { retention_days?: number; archive_enabled?: number }
): Promise<unknown> {
  const updates: string[] = ['updated_at = CURRENT_TIMESTAMP'];
  const binds: unknown[] = [];

  if (data.retention_days !== undefined) { updates.push('retention_days = ?'); binds.push(data.retention_days); }
  if (data.archive_enabled !== undefined) { updates.push('archive_enabled = ?'); binds.push(data.archive_enabled); }

  binds.push(category);
  return db.prepare(
    `UPDATE event_retention_configs SET ${updates.join(', ')} WHERE category = ? RETURNING *`
  ).bind(...binds).first();
}

// --- Purge & Stats ---

/** Delete events older than their configured retention period */
export async function purgeExpired(db: any): Promise<{ purged: number }> {
  const configs = await getRetentionConfigs(db) as Array<{ category: string; retention_days: number }>;
  let total = 0;
  for (const cfg of configs) {
    const result = await db.prepare(
      `DELETE FROM platform_events
       WHERE category = ? AND created_at < datetime('now', ? || ' days')`
    ).bind(cfg.category, `-${cfg.retention_days}`).run();
    total += result.meta?.changes ?? 0;
  }
  return { purged: total };
}

/** Aggregate event counts by category and severity */
export async function getEventStats(db: any): Promise<unknown> {
  const [byCategory, bySeverity, recent] = await Promise.all([
    db.prepare(
      `SELECT category, COUNT(*) as count FROM platform_events GROUP BY category ORDER BY count DESC`
    ).all(),
    db.prepare(
      `SELECT severity, COUNT(*) as count FROM platform_events GROUP BY severity ORDER BY count DESC`
    ).all(),
    db.prepare(
      `SELECT COUNT(*) as count FROM platform_events WHERE created_at >= datetime('now', '-24 hours')`
    ).first(),
  ]);
  return {
    by_category: byCategory.results,
    by_severity: bySeverity.results,
    last_24h: (recent as any)?.count ?? 0,
  };
}

/** Admin overview: stats + recent events + categories */
export async function getAdminOverview(db: any): Promise<unknown> {
  const [stats, recentEvents, categories, retentionConfigs] = await Promise.all([
    getEventStats(db),
    getEvents(db, { limit: 10 }),
    listCategories(db),
    getRetentionConfigs(db),
  ]);
  return { stats, recent_events: recentEvents, categories, retention_configs: retentionConfigs };
}

export const platformEventLogService = {
  logEvent,
  getEvents,
  getEvent,
  listCategories,
  createCategory,
  getRetentionConfigs,
  updateRetentionConfig,
  purgeExpired,
  getEventStats,
  getAdminOverview,
};
