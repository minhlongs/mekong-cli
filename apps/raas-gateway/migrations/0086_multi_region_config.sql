-- Multi-Region Configuration: region configs + endpoints for tenant-aware routing
CREATE TABLE IF NOT EXISTS region_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  primary_region TEXT DEFAULT 'auto',
  allowed_regions TEXT DEFAULT '["us","eu","ap"]',
  data_residency TEXT DEFAULT 'none',
  routing_strategy TEXT DEFAULT 'latency',
  failover_regions TEXT DEFAULT '[]',
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE(tenant_id)
);

CREATE TABLE IF NOT EXISTS region_endpoints (
  id TEXT PRIMARY KEY,
  region_code TEXT NOT NULL,
  region_name TEXT NOT NULL,
  base_url TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  latency_ms INTEGER,
  last_health_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(region_code)
);

CREATE INDEX IF NOT EXISTS idx_region_config_tenant ON region_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_region_endpoints ON region_endpoints(region_code);
