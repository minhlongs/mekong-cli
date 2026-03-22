-- Migration 0095: Mission Webhooks V3
-- Per-mission callback URLs with configurable retry, delivery guarantees, and signing

CREATE TABLE IF NOT EXISTS webhook_subscriptions_v3 (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  secret TEXT, -- HMAC signing secret
  events TEXT NOT NULL DEFAULT '["mission.completed"]', -- JSON array
  retry_policy TEXT NOT NULL DEFAULT 'exponential', -- exponential, linear, none
  max_retries INTEGER DEFAULT 5,
  timeout_ms INTEGER DEFAULT 5000,
  is_active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX idx_wh_v3_tenant ON webhook_subscriptions_v3(tenant_id);

CREATE TABLE IF NOT EXISTS webhook_deliveries_v3 (
  id TEXT PRIMARY KEY,
  subscription_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, delivered, failed, retrying
  attempt_count INTEGER DEFAULT 0,
  last_attempt_at TEXT,
  next_retry_at TEXT,
  response_status INTEGER,
  response_body TEXT,
  duration_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_wh_del_v3_sub ON webhook_deliveries_v3(subscription_id);
CREATE INDEX idx_wh_del_v3_status ON webhook_deliveries_v3(status);
CREATE INDEX idx_wh_del_v3_tenant ON webhook_deliveries_v3(tenant_id, created_at);
