-- Migration: Tenant API Caching Config
-- Stores per-tenant endpoint caching rules and aggregate cache hit/miss stats

CREATE TABLE IF NOT EXISTS api_caching_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  ttl_seconds INTEGER NOT NULL DEFAULT 300,
  cache_key_template TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_caching_configs_tenant ON api_caching_configs(tenant_id);

CREATE TABLE IF NOT EXISTS api_cache_stats (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0,
  misses INTEGER NOT NULL DEFAULT 0,
  hit_rate REAL,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_cache_stats_tenant ON api_cache_stats(tenant_id);
