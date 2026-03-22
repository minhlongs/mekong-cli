/**
 * API Response Caching Service — cache rules CRUD + entry lookup/store/invalidate + analytics
 *
 * Tables: cache_rules, cache_entries, cache_analytics
 */

// ── Types ────────────────────────────────────────────────────────────────────

export interface CacheRule {
  id: string; path_pattern: string; method: string; ttl_seconds: number;
  vary_headers_json: string; enabled: number; priority: number;
  tenant_scoped: number; created_at: string; updated_at: string;
}

export interface CacheEntry {
  id: string; cache_key: string; path: string; response_json: string;
  status_code: number; headers_json: string; tenant_id: string | null;
  expires_at: string; created_at: string; hit_count: number;
}

export interface CacheAnalytics {
  id: string; period: string; total_requests: number; cache_hits: number;
  cache_misses: number; hit_rate: number; avg_response_time_ms: number;
  bytes_saved: number; created_at: string;
}

// ── Cache Rules ───────────────────────────────────────────────────────────────

/** List all cache rules ordered by priority desc */
export async function listRules(db: any): Promise<CacheRule[]> {
  const { results } = await db
    .prepare('SELECT * FROM cache_rules ORDER BY priority DESC, created_at DESC')
    .all();
  return (results ?? []) as CacheRule[];
}

/** Create a new cache rule */
export async function createRule(db: any, data: Partial<CacheRule>): Promise<CacheRule> {
  const id = crypto.randomUUID();
  const row = await db.prepare(
    `INSERT INTO cache_rules (id, path_pattern, method, ttl_seconds, vary_headers_json, enabled, priority, tenant_scoped)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id,
    data.path_pattern,
    data.method ?? 'GET',
    data.ttl_seconds ?? 300,
    data.vary_headers_json ?? '["Authorization"]',
    data.enabled !== undefined ? data.enabled : 1,
    data.priority ?? 0,
    data.tenant_scoped !== undefined ? data.tenant_scoped : 1,
  ).first() as CacheRule | null;
  if (!row) throw new Error('Failed to create cache rule');
  return row;
}

/** Update an existing cache rule */
export async function updateRule(db: any, id: string, data: Partial<CacheRule>): Promise<CacheRule> {
  const now = new Date().toISOString();
  const fields: string[] = [];
  const values: unknown[] = [];
  const allowed = ['path_pattern','method','ttl_seconds','vary_headers_json','enabled','priority','tenant_scoped'] as const;
  for (const key of allowed) {
    if (data[key] !== undefined) { fields.push(`${key} = ?`); values.push(data[key]); }
  }
  if (fields.length === 0) throw new Error('No fields to update');
  fields.push('updated_at = ?'); values.push(now); values.push(id);
  const row = await db.prepare(
    `UPDATE cache_rules SET ${fields.join(', ')} WHERE id = ? RETURNING *`
  ).bind(...values).first() as CacheRule | null;
  if (!row) throw new Error('Cache rule not found');
  return row;
}

/** Delete a cache rule by id */
export async function deleteRule(db: any, id: string): Promise<void> {
  await db.prepare('DELETE FROM cache_rules WHERE id = ?').bind(id).run();
}

// ── Cache Entries ─────────────────────────────────────────────────────────────

/** Get a single cache entry by cache_key; returns null if missing or expired */
export async function getCacheEntry(db: any, cacheKey: string): Promise<CacheEntry | null> {
  const row = await db
    .prepare('SELECT * FROM cache_entries WHERE cache_key = ? AND expires_at > datetime("now")')
    .bind(cacheKey).first() as CacheEntry | null;
  if (!row) return null;
  // Increment hit_count async (fire-and-forget acceptable)
  db.prepare('UPDATE cache_entries SET hit_count = hit_count + 1 WHERE cache_key = ?')
    .bind(cacheKey).run().catch(() => {/* non-critical */});
  return row;
}

/** Store or replace a cache entry */
export async function setCacheEntry(db: any, data: Omit<CacheEntry, 'id' | 'created_at' | 'hit_count'>): Promise<CacheEntry> {
  const id = crypto.randomUUID();
  const row = await db.prepare(
    `INSERT INTO cache_entries (id, cache_key, path, response_json, status_code, headers_json, tenant_id, expires_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(cache_key) DO UPDATE SET
       path=excluded.path, response_json=excluded.response_json,
       status_code=excluded.status_code, headers_json=excluded.headers_json,
       tenant_id=excluded.tenant_id, expires_at=excluded.expires_at, hit_count=0
     RETURNING *`
  ).bind(id, data.cache_key, data.path, data.response_json,
    data.status_code ?? 200, data.headers_json ?? '{}', data.tenant_id ?? null, data.expires_at
  ).first() as CacheEntry | null;
  if (!row) throw new Error('Failed to store cache entry');
  return row;
}

/** Delete cache entries whose path matches the given pattern (LIKE-style) */
export async function invalidateByPath(db: any, pathPattern: string): Promise<number> {
  const result = await db
    .prepare("DELETE FROM cache_entries WHERE path LIKE ?")
    .bind(pathPattern).run();
  return result.meta?.changes ?? 0;
}

/** Delete all cache entries for a specific tenant */
export async function invalidateByTenant(db: any, tenantId: string): Promise<number> {
  const result = await db
    .prepare('DELETE FROM cache_entries WHERE tenant_id = ?')
    .bind(tenantId).run();
  return result.meta?.changes ?? 0;
}

/** Remove all expired cache entries */
export async function purgeExpired(db: any): Promise<number> {
  const result = await db
    .prepare('DELETE FROM cache_entries WHERE expires_at <= datetime("now")')
    .run();
  return result.meta?.changes ?? 0;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

/** Get analytics rows; optionally filter by period prefix */
export async function getAnalytics(db: any, period?: string): Promise<CacheAnalytics[]> {
  const query = period
    ? 'SELECT * FROM cache_analytics WHERE period LIKE ? ORDER BY created_at DESC'
    : 'SELECT * FROM cache_analytics ORDER BY created_at DESC LIMIT 100';
  const stmt = period
    ? db.prepare(query).bind(`${period}%`)
    : db.prepare(query);
  const { results } = await stmt.all();
  return (results ?? []) as CacheAnalytics[];
}

/** Insert an analytics record */
export async function recordAnalytics(db: any, data: Partial<CacheAnalytics>): Promise<CacheAnalytics> {
  if (!data.period) throw new Error('period is required');
  const id = crypto.randomUUID();
  const row = await db.prepare(
    `INSERT INTO cache_analytics (id, period, total_requests, cache_hits, cache_misses, hit_rate, avg_response_time_ms, bytes_saved)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id, data.period,
    data.total_requests ?? 0, data.cache_hits ?? 0, data.cache_misses ?? 0,
    data.hit_rate ?? 0, data.avg_response_time_ms ?? 0, data.bytes_saved ?? 0,
  ).first() as CacheAnalytics | null;
  if (!row) throw new Error('Failed to record analytics');
  return row;
}

/** Admin overview: rule count, entry count, expired count, latest analytics */
export async function getAdminOverview(db: any): Promise<Record<string, unknown>> {
  const [rules, entries, expired, analytics] = await db.batch([
    db.prepare('SELECT COUNT(*) as total, SUM(enabled) as active FROM cache_rules'),
    db.prepare('SELECT COUNT(*) as total, SUM(hit_count) as total_hits FROM cache_entries'),
    db.prepare('SELECT COUNT(*) as total FROM cache_entries WHERE expires_at <= datetime("now")'),
    db.prepare('SELECT * FROM cache_analytics ORDER BY created_at DESC LIMIT 5'),
  ]);
  return {
    rules: rules.results?.[0] ?? {},
    entries: entries.results?.[0] ?? {},
    expired: expired.results?.[0] ?? {},
    recent_analytics: analytics.results ?? [],
  };
}

export const apiResponseCachingService = {
  listRules, createRule, updateRule, deleteRule,
  getCacheEntry, setCacheEntry, invalidateByPath, invalidateByTenant,
  purgeExpired, getAnalytics, recordAnalytics, getAdminOverview,
};
