-- Migration: Tenant Quotas & Limits
-- Wave 40.1 — resource quotas per tenant, enforced by tier

CREATE TABLE IF NOT EXISTS tenant_quotas (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  max_projects INTEGER DEFAULT 5,
  max_team_members INTEGER DEFAULT 3,
  max_api_keys INTEGER DEFAULT 5,
  max_missions_per_day INTEGER DEFAULT 100,
  max_templates INTEGER DEFAULT 20,
  max_webhooks INTEGER DEFAULT 10,
  max_storage_mb INTEGER DEFAULT 100,
  custom_overrides TEXT, -- JSON for per-tenant overrides
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX idx_quotas_tenant ON tenant_quotas(tenant_id);

CREATE TABLE IF NOT EXISTS quota_usage_snapshots (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  resource_type TEXT NOT NULL, -- projects, team_members, api_keys, missions_today, etc.
  current_usage INTEGER DEFAULT 0,
  quota_limit INTEGER DEFAULT 0,
  snapshot_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_quota_usage_tenant ON quota_usage_snapshots(tenant_id, resource_type);
