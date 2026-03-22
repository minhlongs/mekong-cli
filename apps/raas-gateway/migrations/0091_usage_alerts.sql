-- Migration 0091: Usage Alerts & Budget Controls
-- Tenants set spending limits and alert thresholds

CREATE TABLE IF NOT EXISTS usage_alert_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_type TEXT NOT NULL, -- credits_threshold, daily_limit, monthly_limit, rate_spike
  threshold_value REAL NOT NULL,
  action TEXT NOT NULL DEFAULT 'notify', -- notify, warn, block
  channel TEXT DEFAULT 'email', -- email, webhook, telegram
  is_active INTEGER DEFAULT 1,
  last_triggered_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_alert_rules_tenant ON usage_alert_rules(tenant_id);

CREATE TABLE IF NOT EXISTS usage_alert_history (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  rule_type TEXT NOT NULL,
  threshold_value REAL,
  current_value REAL,
  action_taken TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_alert_history_tenant ON usage_alert_history(tenant_id, created_at);

CREATE TABLE IF NOT EXISTS budget_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  monthly_budget REAL,
  daily_budget REAL,
  hard_limit INTEGER DEFAULT 0, -- 0=soft (warn), 1=hard (block)
  rollover_unused INTEGER DEFAULT 0,
  budget_period_start TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX idx_budget_tenant ON budget_configs(tenant_id);
