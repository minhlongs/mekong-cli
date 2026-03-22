-- Wave 64: Admin Traffic Shaping
-- Tables: traffic_rules, traffic_events

CREATE TABLE IF NOT EXISTS traffic_rules (
  id TEXT PRIMARY KEY,
  rule_name TEXT NOT NULL,
  target_pattern TEXT NOT NULL,
  max_rps INTEGER NOT NULL,
  burst_size INTEGER DEFAULT 10,
  priority INTEGER DEFAULT 5,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS traffic_events (
  id TEXT PRIMARY KEY,
  rule_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  source_ip TEXT,
  path TEXT,
  action_taken TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_traffic_rules_rule_name ON traffic_rules(rule_name);
CREATE INDEX IF NOT EXISTS idx_traffic_events_rule_id ON traffic_events(rule_id);
