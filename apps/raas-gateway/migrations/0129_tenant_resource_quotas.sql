-- Migration: Tenant Resource Quotas
-- Wave 50 — flexible per-resource quota definitions, per-tenant limits, alerts

CREATE TABLE IF NOT EXISTS resource_quota_definitions (
  id TEXT PRIMARY KEY,
  resource_type TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  description TEXT,
  default_limit INTEGER NOT NULL,
  unit TEXT DEFAULT 'count',
  enforcement TEXT DEFAULT 'soft',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_quotas (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  quota_limit INTEGER NOT NULL,
  current_usage INTEGER DEFAULT 0,
  last_reset_at TEXT,
  reset_period TEXT DEFAULT 'monthly',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(tenant_id, resource_type)
);

CREATE TABLE IF NOT EXISTS quota_alerts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  threshold_pct INTEGER NOT NULL,
  alert_type TEXT DEFAULT 'warning',
  message TEXT,
  triggered_at TEXT DEFAULT CURRENT_TIMESTAMP,
  acknowledged_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tenant_quotas_tenant ON tenant_quotas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_quotas_resource ON tenant_quotas(resource_type);
CREATE INDEX IF NOT EXISTS idx_quota_alerts_tenant ON quota_alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_quota_alerts_resource ON quota_alerts(resource_type);

-- Seed default quota definitions
INSERT OR IGNORE INTO resource_quota_definitions (id, resource_type, display_name, description, default_limit, unit, enforcement)
VALUES
  ('def_missions_per_month',    'missions_per_month',   'Missions per Month',    'Max AI missions a tenant can run per calendar month', 100,   'count', 'soft'),
  ('def_api_calls_per_day',     'api_calls_per_day',    'API Calls per Day',     'Max API requests a tenant can make per day',          10000, 'count', 'hard'),
  ('def_storage_mb',            'storage_mb',           'Storage (MB)',          'Max storage allocated to tenant in megabytes',        5000,  'mb',    'soft'),
  ('def_concurrent_missions',   'concurrent_missions',  'Concurrent Missions',   'Max number of missions running simultaneously',       10,    'count', 'hard'),
  ('def_team_members',          'team_members',         'Team Members',          'Max number of team members in the tenant org',        25,    'count', 'soft');
