-- Migration: admin_system_configuration
-- Platform-level key/value configuration store with full audit history

CREATE TABLE IF NOT EXISTS system_configurations (
  id TEXT PRIMARY KEY,
  config_key TEXT NOT NULL UNIQUE,
  config_value TEXT NOT NULL,
  config_type TEXT NOT NULL DEFAULT 'string',
  description TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_configurations_key ON system_configurations(config_key);

CREATE TABLE IF NOT EXISTS system_configuration_history (
  id TEXT PRIMARY KEY,
  config_id TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT NOT NULL,
  changed_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_configuration_history_config ON system_configuration_history(config_id);
