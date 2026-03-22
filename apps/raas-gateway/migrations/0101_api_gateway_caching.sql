-- Migration 0101: API Gateway Caching
-- Response caching layer with TTL management, cache invalidation, and analytics

CREATE TABLE IF NOT EXISTS cache_configs (
  id TEXT PRIMARY KEY DEFAULT ('cc_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  path_pattern TEXT NOT NULL, -- e.g. '/v1/missions/*'
  method TEXT NOT NULL DEFAULT 'GET',
  ttl_seconds INTEGER NOT NULL DEFAULT 300,
  vary_headers TEXT DEFAULT '[]', -- JSON array
  vary_query_params TEXT DEFAULT '[]', -- JSON array
  is_active INTEGER NOT NULL DEFAULT 1,
  cache_scope TEXT NOT NULL DEFAULT 'tenant', -- tenant, global, user
  max_size_bytes INTEGER DEFAULT 1048576, -- 1MB default
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cache_cfg_tenant ON cache_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cache_cfg_path ON cache_configs(path_pattern, method);

CREATE TABLE IF NOT EXISTS cache_entries (
  id TEXT PRIMARY KEY DEFAULT ('ce_' || lower(hex(randomblob(8)))),
  cache_key TEXT NOT NULL UNIQUE,
  tenant_id TEXT NOT NULL,
  path TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'GET',
  response_body TEXT NOT NULL,
  response_headers TEXT DEFAULT '{}', -- JSON
  status_code INTEGER NOT NULL DEFAULT 200,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  hit_count INTEGER NOT NULL DEFAULT 0,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_hit_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_tenant ON cache_entries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at);

CREATE TABLE IF NOT EXISTS cache_analytics (
  id TEXT PRIMARY KEY DEFAULT ('ca_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  date TEXT NOT NULL,
  total_requests INTEGER NOT NULL DEFAULT 0,
  cache_hits INTEGER NOT NULL DEFAULT 0,
  cache_misses INTEGER NOT NULL DEFAULT 0,
  bytes_saved INTEGER NOT NULL DEFAULT 0,
  avg_latency_ms REAL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_analytics_unique ON cache_analytics(tenant_id, date);
CREATE INDEX IF NOT EXISTS idx_cache_analytics ON cache_analytics(tenant_id, date);
