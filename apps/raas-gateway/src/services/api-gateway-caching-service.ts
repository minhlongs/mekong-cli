/**
 * API Gateway Caching Service — cache config CRUD + entry lookup/store/invalidate
 *
 * Analytics functions: see api-gateway-caching-analytics-service.ts
 */

import type { D1Database } from '@cloudflare/workers-types';

// ── Types ────────────────────────────────────────────────────────────────────

export interface CacheConfig {
  id: string; tenant_id: string; path_pattern: string; method: string;
  ttl_seconds: number; vary_headers: string; vary_query_params: string;
  is_active: number; cache_scope: string; max_size_bytes: number;
  created_at: string; updated_at: string;
}

export interface CacheEntry {
  id: string; cache_key: string; tenant_id: string; path: string;
  method: string; response_body: string; response_headers: string;
  status_code: number; size_bytes: number; hit_count: number;
  expires_at: string; created_at: string; last_hit_at: string | null;
}

export interface CacheConfigInput {
  path_pattern: string; method?: string; ttl_seconds?: number;
  vary_headers?: string[]; vary_query_params?: string[];
  is_active?: boolean; cache_scope?: string; max_size_bytes?: number;
}

export interface CacheResponseInput {
  path: string; method?: string; response_body: string;
  response_headers?: Record<string, string>; status_code?: number;
}

// ── Config CRUD ───────────────────────────────────────────────────────────────

/** Create a cache rule for a tenant */
export async function createCacheConfig(db: D1Database, tenantId: string, config: CacheConfigInput): Promise<CacheConfig> {
  const row = await db.prepare(
    `INSERT INTO cache_configs (tenant_id, path_pattern, method, ttl_seconds, vary_headers, vary_query_params, is_active, cache_scope, max_size_bytes)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    tenantId, config.path_pattern, config.method ?? 'GET', config.ttl_seconds ?? 300,
    JSON.stringify(config.vary_headers ?? []), JSON.stringify(config.vary_query_params ?? []),
    config.is_active !== false ? 1 : 0, config.cache_scope ?? 'tenant', config.max_size_bytes ?? 1048576
  ).first<CacheConfig>();
  if (!row) throw new Error('Failed to create cache config');
  return row;
}

/** List all cache configs for a tenant */
export async function listCacheConfigs(db: D1Database, tenantId: string): Promise<CacheConfig[]> {
  const { results } = await db.prepare('SELECT * FROM cache_configs WHERE tenant_id = ? ORDER BY created_at DESC').bind(tenantId).all<CacheConfig>();
  return results;
}

/** Update a cache config (tenant-scoped) */
export async function updateCacheConfig(db: D1Database, configId: string, tenantId: string, updates: Partial<CacheConfigInput>): Promise<CacheConfig | null> {
  const fields: string[] = [];
  const values: unknown[] = [];
  if (updates.path_pattern !== undefined) { fields.push('path_pattern = ?'); values.push(updates.path_pattern); }
  if (updates.method !== undefined) { fields.push('method = ?'); values.push(updates.method); }
  if (updates.ttl_seconds !== undefined) { fields.push('ttl_seconds = ?'); values.push(updates.ttl_seconds); }
  if (updates.vary_headers !== undefined) { fields.push('vary_headers = ?'); values.push(JSON.stringify(updates.vary_headers)); }
  if (updates.vary_query_params !== undefined) { fields.push('vary_query_params = ?'); values.push(JSON.stringify(updates.vary_query_params)); }
  if (updates.is_active !== undefined) { fields.push('is_active = ?'); values.push(updates.is_active ? 1 : 0); }
  if (updates.cache_scope !== undefined) { fields.push('cache_scope = ?'); values.push(updates.cache_scope); }
  if (updates.max_size_bytes !== undefined) { fields.push('max_size_bytes = ?'); values.push(updates.max_size_bytes); }
  if (fields.length === 0) return null;
  fields.push("updated_at = datetime('now')");
  values.push(configId, tenantId);
  return db.prepare(`UPDATE cache_configs SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ? RETURNING *`).bind(...values).first<CacheConfig>();
}

/** Delete a cache config (tenant-scoped) */
export async function deleteCacheConfig(db: D1Database, configId: string, tenantId: string): Promise<boolean> {
  const result = await db.prepare('DELETE FROM cache_configs WHERE id = ? AND tenant_id = ?').bind(configId, tenantId).run();
  return (result.meta.changes ?? 0) > 0;
}

// ── Cache Entry Operations ────────────────────────────────────────────────────

/** Lookup cached response by key; increments hit_count if found and not expired */
export async function getCacheEntry(db: D1Database, cacheKey: string): Promise<CacheEntry | null> {
  const entry = await db.prepare("SELECT * FROM cache_entries WHERE cache_key = ? AND expires_at > datetime('now')").bind(cacheKey).first<CacheEntry>();
  if (!entry) return null;
  // Non-blocking hit count update
  db.prepare("UPDATE cache_entries SET hit_count = hit_count + 1, last_hit_at = datetime('now') WHERE cache_key = ?").bind(cacheKey).run().catch(() => {});
  return entry;
}

/** Store a response in cache with TTL; upserts on conflict */
export async function setCacheEntry(db: D1Database, tenantId: string, path: string, cacheKey: string, response: CacheResponseInput, ttlSeconds: number): Promise<CacheEntry> {
  const body = response.response_body;
  const sizeBytes = new TextEncoder().encode(body).length;
  const row = await db.prepare(
    `INSERT INTO cache_entries (cache_key, tenant_id, path, method, response_body, response_headers, status_code, size_bytes, expires_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+' || ? || ' seconds'))
     ON CONFLICT(cache_key) DO UPDATE SET
       response_body = excluded.response_body, response_headers = excluded.response_headers,
       status_code = excluded.status_code, size_bytes = excluded.size_bytes,
       expires_at = excluded.expires_at, hit_count = 0, last_hit_at = NULL
     RETURNING *`
  ).bind(
    cacheKey, tenantId, path, response.method ?? 'GET', body,
    JSON.stringify(response.response_headers ?? {}),
    response.status_code ?? 200, sizeBytes, String(ttlSeconds)
  ).first<CacheEntry>();
  if (!row) throw new Error('Failed to store cache entry');
  return row;
}

/** Invalidate cache entries for a tenant; optionally filter by path pattern */
export async function invalidateCache(db: D1Database, tenantId: string, pathPattern?: string): Promise<number> {
  const result = pathPattern
    ? await db.prepare('DELETE FROM cache_entries WHERE tenant_id = ? AND path LIKE ?').bind(tenantId, pathPattern.replace(/\*/g, '%')).run()
    : await db.prepare('DELETE FROM cache_entries WHERE tenant_id = ?').bind(tenantId).run();
  return result.meta.changes ?? 0;
}
