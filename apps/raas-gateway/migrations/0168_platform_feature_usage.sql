-- Migration: Platform Feature Usage
-- Tracks per-tenant feature usage counts and platform-wide adoption rates

CREATE TABLE IF NOT EXISTS feature_usage (
  id TEXT PRIMARY KEY,
  feature_name TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  usage_count INTEGER NOT NULL DEFAULT 0,
  last_used_at TEXT,
  period TEXT NOT NULL DEFAULT 'monthly',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feature_usage_feature_name ON feature_usage (feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_usage_tenant_id ON feature_usage (tenant_id);

CREATE TABLE IF NOT EXISTS feature_adoption (
  id TEXT PRIMARY KEY,
  feature_name TEXT NOT NULL,
  total_tenants INTEGER NOT NULL DEFAULT 0,
  active_tenants INTEGER NOT NULL DEFAULT 0,
  adoption_rate REAL NOT NULL DEFAULT 0,
  measured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feature_adoption_feature_name ON feature_adoption (feature_name);
