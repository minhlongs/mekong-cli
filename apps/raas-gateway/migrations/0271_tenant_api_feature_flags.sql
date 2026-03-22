-- Migration: tenant_api_feature_flags
-- Feature flag management per tenant with rollout percentage and evaluation tracking

CREATE TABLE IF NOT EXISTS tenant_feature_flags (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  flag_key TEXT NOT NULL,
  flag_value INTEGER NOT NULL DEFAULT 0,
  description TEXT,
  rollout_percentage INTEGER DEFAULT 100,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_feature_flags_tenant ON tenant_feature_flags(tenant_id);

CREATE TABLE IF NOT EXISTS tenant_feature_flag_evaluations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  flag_id TEXT NOT NULL,
  user_id TEXT,
  result INTEGER NOT NULL,
  context_json TEXT,
  evaluated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_feature_flag_evaluations_tenant ON tenant_feature_flag_evaluations(tenant_id);
