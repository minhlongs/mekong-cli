/**
 * API Gateway Caching Analytics Service — stats, analytics recording, admin overview
 *
 * Functions: getCacheStats, getCacheAnalytics, recordCacheAnalytics, getAdminCacheOverview
 */

import type { D1Database } from '@cloudflare/workers-types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CacheStatsResult {
  total_entries: number;
  total_size_bytes: number;
  total_hits: number;
  hit_rate: number; // percentage with 2 decimals
  top_paths: { path: string; hit_count: number }[];
}

export interface CacheAnalyticsRow {
  date: string;
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  bytes_saved: number;
  avg_latency_ms: number;
}

export interface AdminCacheOverview {
  total_configs: number;
  total_entries: number;
  total_size_bytes: number;
  global_hit_rate: number;
  top_tenants: { tenant_id: string; entry_count: number; total_hits: number }[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function calcHitRate(hits: number, entries: number): number {
  if (hits + entries === 0) return 0;
  return Math.round((hits / (hits + entries)) * 10000) / 100;
}

// ---------------------------------------------------------------------------
// Stats & Analytics
// ---------------------------------------------------------------------------

/** Hit rate, total size, top cached paths for a tenant */
export async function getCacheStats(
  db: D1Database,
  tenantId: string
): Promise<CacheStatsResult> {
  const summary = await db
    .prepare(
      `SELECT COUNT(*) as total_entries,
              COALESCE(SUM(size_bytes), 0) as total_size_bytes,
              COALESCE(SUM(hit_count), 0) as total_hits
       FROM cache_entries
       WHERE tenant_id = ? AND expires_at > datetime('now')`
    )
    .bind(tenantId)
    .first<{ total_entries: number; total_size_bytes: number; total_hits: number }>();

  const { results: topPaths } = await db
    .prepare(
      `SELECT path, SUM(hit_count) as hit_count
       FROM cache_entries
       WHERE tenant_id = ? AND expires_at > datetime('now')
       GROUP BY path ORDER BY hit_count DESC LIMIT 10`
    )
    .bind(tenantId)
    .all<{ path: string; hit_count: number }>();

  const totalEntries = summary?.total_entries ?? 0;
  const totalHits = summary?.total_hits ?? 0;

  return {
    total_entries: totalEntries,
    total_size_bytes: summary?.total_size_bytes ?? 0,
    total_hits: totalHits,
    hit_rate: calcHitRate(totalHits, totalEntries),
    top_paths: topPaths,
  };
}

/** Retrieve daily analytics rows for a tenant, optionally filtered by date range */
export async function getCacheAnalytics(
  db: D1Database,
  tenantId: string,
  from?: string,
  to?: string
): Promise<CacheAnalyticsRow[]> {
  let query = 'SELECT date, total_requests, cache_hits, cache_misses, bytes_saved, avg_latency_ms FROM cache_analytics WHERE tenant_id = ?';
  const binds: unknown[] = [tenantId];

  if (from) { query += ' AND date >= ?'; binds.push(from); }
  if (to)   { query += ' AND date <= ?'; binds.push(to); }
  query += ' ORDER BY date DESC LIMIT 90';

  const { results } = await db.prepare(query).bind(...binds).all<CacheAnalyticsRow>();
  return results;
}

/** Record a cache hit or miss for a tenant on today's date */
export async function recordCacheAnalytics(
  db: D1Database,
  tenantId: string,
  hit: boolean,
  bytesSaved: number = 0
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO cache_analytics (tenant_id, date, total_requests, cache_hits, cache_misses, bytes_saved)
       VALUES (?, date('now'), 1, ?, ?, ?)
       ON CONFLICT(tenant_id, date) DO UPDATE SET
         total_requests = total_requests + 1,
         cache_hits     = cache_hits + excluded.cache_hits,
         cache_misses   = cache_misses + excluded.cache_misses,
         bytes_saved    = bytes_saved + excluded.bytes_saved`
    )
    .bind(tenantId, hit ? 1 : 0, hit ? 0 : 1, bytesSaved)
    .run();
}

/** Platform-wide cache overview for admin */
export async function getAdminCacheOverview(db: D1Database): Promise<AdminCacheOverview> {
  const configs = await db
    .prepare('SELECT COUNT(*) as total_configs FROM cache_configs')
    .first<{ total_configs: number }>();

  const entries = await db
    .prepare(
      `SELECT COUNT(*) as total_entries,
              COALESCE(SUM(size_bytes), 0) as total_size_bytes,
              COALESCE(SUM(hit_count), 0) as total_hits
       FROM cache_entries WHERE expires_at > datetime('now')`
    )
    .first<{ total_entries: number; total_size_bytes: number; total_hits: number }>();

  const { results: topTenants } = await db
    .prepare(
      `SELECT tenant_id, COUNT(*) as entry_count, SUM(hit_count) as total_hits
       FROM cache_entries WHERE expires_at > datetime('now')
       GROUP BY tenant_id ORDER BY total_hits DESC LIMIT 10`
    )
    .all<{ tenant_id: string; entry_count: number; total_hits: number }>();

  const totalEntries = entries?.total_entries ?? 0;
  const totalHits = entries?.total_hits ?? 0;

  return {
    total_configs: configs?.total_configs ?? 0,
    total_entries: totalEntries,
    total_size_bytes: entries?.total_size_bytes ?? 0,
    global_hit_rate: calcHitRate(totalHits, totalEntries),
    top_tenants: topTenants,
  };
}
