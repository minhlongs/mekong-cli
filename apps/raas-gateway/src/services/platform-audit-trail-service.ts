/**
 * Platform Audit Trail Service — admin action logging, change tracking, compliance audit
 */

export interface AuditEntry {
  actorType: string;
  actorId: string;
  action: string;
  resourceType: string;
  resourceId?: string;
  changes?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
}

export interface AuditFilters {
  actorId?: string;
  action?: string;
  resourceType?: string;
  resourceId?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
}

/** Insert a new audit entry */
export async function logAction(db: D1Database, entry: AuditEntry): Promise<{ id: string }> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO platform_audit_entries
      (id, actor_type, actor_id, action, resource_type, resource_id, changes, metadata, ip_address, user_agent)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id,
    entry.actorType,
    entry.actorId,
    entry.action,
    entry.resourceType,
    entry.resourceId ?? null,
    JSON.stringify(entry.changes ?? {}),
    JSON.stringify(entry.metadata ?? {}),
    entry.ipAddress ?? null,
    entry.userAgent ?? null,
  ).run();
  return { id };
}

/** Query audit log with optional filters + pagination */
export async function getAuditLog(db: D1Database, filters: AuditFilters = {}) {
  const conditions: string[] = [];
  const params: unknown[] = [];

  if (filters.actorId) { conditions.push('actor_id = ?'); params.push(filters.actorId); }
  if (filters.action) { conditions.push('action = ?'); params.push(filters.action); }
  if (filters.resourceType) { conditions.push('resource_type = ?'); params.push(filters.resourceType); }
  if (filters.resourceId) { conditions.push('resource_id = ?'); params.push(filters.resourceId); }
  if (filters.dateFrom) { conditions.push('created_at >= ?'); params.push(filters.dateFrom); }
  if (filters.dateTo) { conditions.push('created_at <= ?'); params.push(filters.dateTo); }

  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  const limit = filters.limit ?? 50;
  const offset = filters.offset ?? 0;
  params.push(limit, offset);

  const { results } = await db.prepare(
    `SELECT * FROM platform_audit_entries ${where} ORDER BY created_at DESC LIMIT ? OFFSET ?`
  ).bind(...params).all();
  return results;
}

/** All actions by a specific actor */
export async function getActorHistory(db: D1Database, actorId: string, limit = 100) {
  const { results } = await db.prepare(
    'SELECT * FROM platform_audit_entries WHERE actor_id = ? ORDER BY created_at DESC LIMIT ?'
  ).bind(actorId, limit).all();
  return results;
}

/** All changes to a specific resource */
export async function getResourceHistory(db: D1Database, resourceType: string, resourceId: string) {
  const { results } = await db.prepare(
    'SELECT * FROM platform_audit_entries WHERE resource_type = ? AND resource_id = ? ORDER BY created_at DESC'
  ).bind(resourceType, resourceId).all();
  return results;
}

/** Text search across action, resource_type, and changes */
export async function searchAuditLog(db: D1Database, query: string) {
  const q = `%${query}%`;
  const { results } = await db.prepare(
    `SELECT * FROM platform_audit_entries
     WHERE action LIKE ? OR resource_type LIKE ? OR changes LIKE ?
     ORDER BY created_at DESC LIMIT 200`
  ).bind(q, q, q).all();
  return results;
}

/** Aggregate stats: actions per day, top actors, actions, resource types */
export async function getAuditStats(db: D1Database, days = 30) {
  const since = new Date(Date.now() - days * 86400000).toISOString();
  const [perDay, topActors, topActions, topResources] = await Promise.all([
    db.prepare(
      `SELECT substr(created_at,1,10) as day, COUNT(*) as count
       FROM platform_audit_entries WHERE created_at >= ?
       GROUP BY day ORDER BY day DESC`
    ).bind(since).all(),
    db.prepare(
      `SELECT actor_id, actor_type, COUNT(*) as count
       FROM platform_audit_entries WHERE created_at >= ?
       GROUP BY actor_id ORDER BY count DESC LIMIT 10`
    ).bind(since).all(),
    db.prepare(
      `SELECT action, COUNT(*) as count
       FROM platform_audit_entries WHERE created_at >= ?
       GROUP BY action ORDER BY count DESC LIMIT 10`
    ).bind(since).all(),
    db.prepare(
      `SELECT resource_type, COUNT(*) as count
       FROM platform_audit_entries WHERE created_at >= ?
       GROUP BY resource_type ORDER BY count DESC LIMIT 10`
    ).bind(since).all(),
  ]);
  return {
    days,
    perDay: perDay.results,
    topActors: topActors.results,
    topActions: topActions.results,
    topResources: topResources.results,
  };
}

/** Set retention config for a resource type */
export async function setRetentionConfig(
  db: D1Database,
  resourceType: string,
  retentionDays: number,
  immutable = false,
) {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO audit_retention_configs (id, resource_type, retention_days, is_immutable)
     VALUES (?, ?, ?, ?)
     ON CONFLICT(resource_type) DO UPDATE SET retention_days=excluded.retention_days, is_immutable=excluded.is_immutable`
  ).bind(id, resourceType, retentionDays, immutable ? 1 : 0).run();
  return { resourceType, retentionDays, immutable };
}

/** List all retention configs */
export async function getRetentionConfigs(db: D1Database) {
  const { results } = await db.prepare('SELECT * FROM audit_retention_configs ORDER BY resource_type').all();
  return results;
}

/** Delete entries past their retention period, skip immutable resource types */
export async function cleanExpiredEntries(db: D1Database): Promise<{ deleted: number }> {
  const { results: configs } = await db.prepare(
    'SELECT resource_type, retention_days FROM audit_retention_configs WHERE is_immutable = 0'
  ).all() as { results: Array<{ resource_type: string; retention_days: number }> };

  let deleted = 0;
  for (const cfg of configs) {
    const cutoff = new Date(Date.now() - cfg.retention_days * 86400000).toISOString();
    const result = await db.prepare(
      'DELETE FROM platform_audit_entries WHERE resource_type = ? AND created_at < ?'
    ).bind(cfg.resource_type, cutoff).run();
    deleted += result.meta?.changes ?? 0;
  }
  return { deleted };
}

/** Export filtered entries as array (for CSV/JSON export) */
export async function exportAuditLog(db: D1Database, filters: AuditFilters = {}) {
  return getAuditLog(db, { ...filters, limit: filters.limit ?? 10000, offset: filters.offset ?? 0 });
}
