-- Migration: Tenant API Load Balancing
-- Tables: api_load_balancer_configs, api_load_balancer_targets

CREATE TABLE IF NOT EXISTS api_load_balancer_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_name TEXT NOT NULL,
  algorithm TEXT NOT NULL DEFAULT 'round-robin',
  health_check_interval_ms INTEGER NOT NULL DEFAULT 30000,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_load_balancer_configs_tenant ON api_load_balancer_configs(tenant_id);

CREATE TABLE IF NOT EXISTS api_load_balancer_targets (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  target_url TEXT NOT NULL,
  weight INTEGER NOT NULL DEFAULT 1,
  healthy INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_load_balancer_targets_config ON api_load_balancer_targets(config_id);
