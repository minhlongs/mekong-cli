-- Admin Platform Scaling — auto-scaling rules and event history

CREATE TABLE IF NOT EXISTS scaling_rules (
  id                TEXT PRIMARY KEY,
  rule_name         TEXT NOT NULL,
  metric_trigger    TEXT NOT NULL,
  scale_direction   TEXT NOT NULL DEFAULT 'up',
  threshold         REAL NOT NULL,
  cooldown_seconds  INTEGER NOT NULL DEFAULT 300,
  max_instances     INTEGER NOT NULL DEFAULT 10,
  is_active         INTEGER NOT NULL DEFAULT 1,
  created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scaling_events (
  id              TEXT PRIMARY KEY,
  rule_id         TEXT NOT NULL,
  previous_count  INTEGER NOT NULL,
  new_count       INTEGER NOT NULL,
  trigger_value   REAL NOT NULL,
  status          TEXT NOT NULL DEFAULT 'completed',
  created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scaling_rules_metric_trigger ON scaling_rules (metric_trigger);
CREATE INDEX IF NOT EXISTS idx_scaling_events_rule_id ON scaling_events (rule_id);
CREATE INDEX IF NOT EXISTS idx_scaling_events_status ON scaling_events (status);
