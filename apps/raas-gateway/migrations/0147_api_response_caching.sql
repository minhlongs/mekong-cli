-- Wave 56: API Response Caching for RaaS Gateway
-- Tables: cache_rules, cache_entries, cache_analytics

CREATE TABLE IF NOT EXISTS cache_rules (
  id TEXT PRIMARY KEY,
  path_pattern TEXT NOT NULL,
  method TEXT DEFAULT 'GET',
  ttl_seconds INTEGER DEFAULT 300,
  vary_headers_json TEXT DEFAULT '["Authorization"]',
  enabled INTEGER DEFAULT 1,
  priority INTEGER DEFAULT 0,
  tenant_scoped INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cache_entries (
  id TEXT PRIMARY KEY,
  cache_key TEXT NOT NULL UNIQUE,
  path TEXT NOT NULL,
  response_json TEXT NOT NULL,
  status_code INTEGER DEFAULT 200,
  headers_json TEXT DEFAULT '{}',
  tenant_id TEXT,
  expires_at TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  hit_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cache_analytics (
  id TEXT PRIMARY KEY,
  period TEXT NOT NULL,
  total_requests INTEGER DEFAULT 0,
  cache_hits INTEGER DEFAULT 0,
  cache_misses INTEGER DEFAULT 0,
  hit_rate REAL DEFAULT 0,
  avg_response_time_ms INTEGER DEFAULT 0,
  bytes_saved INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for cache_rules
CREATE INDEX IF NOT EXISTS idx_cache_rules_path_pattern ON cache_rules(path_pattern);

-- Indexes for cache_entries
CREATE INDEX IF NOT EXISTS idx_cache_entries_cache_key ON cache_entries(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_entries_path ON cache_entries(path);
CREATE INDEX IF NOT EXISTS idx_cache_entries_tenant_id ON cache_entries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cache_entries_expires_at ON cache_entries(expires_at);

-- Indexes for cache_analytics
CREATE INDEX IF NOT EXISTS idx_cache_analytics_period ON cache_analytics(period);
