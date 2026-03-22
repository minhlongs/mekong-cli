-- Migration 0128: Admin Feature Flags
-- Tables: feature_flags, feature_flag_overrides, feature_flag_history

CREATE TABLE IF NOT EXISTS feature_flags (
  id                   TEXT PRIMARY KEY,
  flag_key             TEXT NOT NULL UNIQUE,
  name                 TEXT NOT NULL,
  description          TEXT,
  flag_type            TEXT DEFAULT 'boolean',
  default_value        TEXT DEFAULT 'false',
  rollout_percentage   INTEGER DEFAULT 0,
  targeting_rules_json TEXT DEFAULT '[]',
  status               TEXT DEFAULT 'inactive',
  created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at           TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feature_flag_overrides (
  id             TEXT PRIMARY KEY,
  flag_id        TEXT NOT NULL,
  tenant_id      TEXT NOT NULL,
  override_value TEXT NOT NULL,
  reason         TEXT,
  created_by     TEXT,
  created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (flag_id, tenant_id)
);

CREATE TABLE IF NOT EXISTS feature_flag_history (
  id          TEXT PRIMARY KEY,
  flag_id     TEXT NOT NULL,
  change_type TEXT NOT NULL,
  old_value   TEXT,
  new_value   TEXT,
  changed_by  TEXT,
  created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_feature_flags_flag_key   ON feature_flags (flag_key);
CREATE INDEX IF NOT EXISTS idx_feature_flags_status     ON feature_flags (status);
CREATE INDEX IF NOT EXISTS idx_ff_overrides_tenant_flag ON feature_flag_overrides (tenant_id, flag_id);
CREATE INDEX IF NOT EXISTS idx_ff_history_flag_id       ON feature_flag_history (flag_id);
