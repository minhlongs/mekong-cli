-- Migration 0134: Admin Platform Config
-- Tables: platform_configs, config_overrides, config_history

CREATE TABLE IF NOT EXISTS platform_configs (
  id          TEXT PRIMARY KEY,
  config_key  TEXT NOT NULL UNIQUE,
  config_value TEXT NOT NULL,
  value_type  TEXT DEFAULT 'string',
  description TEXT,
  category    TEXT DEFAULT 'general',
  is_sensitive INTEGER DEFAULT 0,
  created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_overrides (
  id             TEXT PRIMARY KEY,
  config_key     TEXT NOT NULL,
  environment    TEXT NOT NULL,
  override_value TEXT NOT NULL,
  created_by     TEXT,
  created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (config_key, environment)
);

CREATE TABLE IF NOT EXISTS config_history (
  id            TEXT PRIMARY KEY,
  config_key    TEXT NOT NULL,
  old_value     TEXT,
  new_value     TEXT NOT NULL,
  changed_by    TEXT,
  change_reason TEXT,
  created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_platform_configs_key      ON platform_configs (config_key);
CREATE INDEX IF NOT EXISTS idx_platform_configs_category ON platform_configs (category);
CREATE INDEX IF NOT EXISTS idx_config_overrides_key      ON config_overrides (config_key);
CREATE INDEX IF NOT EXISTS idx_config_overrides_env      ON config_overrides (environment);
CREATE INDEX IF NOT EXISTS idx_config_history_key        ON config_history (config_key);

-- Seed default configs
INSERT INTO platform_configs (id, config_key, config_value, value_type, description, category)
VALUES
  ('cfg_maintenance_mode',         'maintenance_mode',          'false',  'boolean', 'Global maintenance mode toggle',                  'system'),
  ('cfg_max_missions_per_minute',  'max_missions_per_minute',   '100',    'number',  'Maximum missions processed per minute per tenant', 'limits'),
  ('cfg_default_mission_timeout',  'default_mission_timeout_ms','300000', 'number',  'Default mission execution timeout in milliseconds','missions'),
  ('cfg_signup_enabled',           'signup_enabled',            'true',   'boolean', 'Whether new user signups are allowed',             'auth'),
  ('cfg_api_rate_limit_default',   'api_rate_limit_default',    '1000',   'number',  'Default API rate limit requests per hour',         'limits')
ON CONFLICT (config_key) DO NOTHING;
