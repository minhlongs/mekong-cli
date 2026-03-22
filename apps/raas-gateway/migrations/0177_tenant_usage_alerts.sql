-- Migration 0177: Tenant Usage Alerts
-- Tables: usage_alert_rules, usage_alert_triggers

CREATE TABLE IF NOT EXISTS usage_alert_rules (
  id                   TEXT    PRIMARY KEY,
  tenant_id            TEXT    NOT NULL,
  metric_name          TEXT    NOT NULL,
  threshold            REAL    NOT NULL,
  comparison           TEXT    NOT NULL DEFAULT 'gt',
  notification_channel TEXT    NOT NULL,
  is_active            INTEGER NOT NULL DEFAULT 1,
  created_at           TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_alert_rules_tenant_id
  ON usage_alert_rules (tenant_id);

CREATE TABLE IF NOT EXISTS usage_alert_triggers (
  id            TEXT    PRIMARY KEY,
  tenant_id     TEXT    NOT NULL,
  rule_id       TEXT    NOT NULL,
  current_value REAL    NOT NULL,
  triggered_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  acknowledged  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_usage_alert_triggers_tenant_id
  ON usage_alert_triggers (tenant_id);
