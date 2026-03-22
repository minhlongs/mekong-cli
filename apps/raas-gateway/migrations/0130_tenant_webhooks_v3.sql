-- Migration 0130: Tenant Webhooks V3 — full subscription management for RaaS Gateway
-- Tables: webhook_subscriptions_v3, webhook_deliveries_v3, webhook_event_types

CREATE TABLE IF NOT EXISTS webhook_subscriptions_v3 (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  url TEXT NOT NULL,
  events_json TEXT DEFAULT '["*"]',
  secret TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  retry_policy TEXT DEFAULT 'exponential',
  max_retries INTEGER DEFAULT 5,
  timeout_ms INTEGER DEFAULT 30000,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wsv3_tenant_id ON webhook_subscriptions_v3(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wsv3_status ON webhook_subscriptions_v3(status);

CREATE TABLE IF NOT EXISTS webhook_deliveries_v3 (
  id TEXT PRIMARY KEY,
  subscription_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  attempts INTEGER DEFAULT 0,
  last_attempt_at TEXT,
  response_status INTEGER,
  response_body TEXT,
  duration_ms INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wdv3_subscription_id ON webhook_deliveries_v3(subscription_id);
CREATE INDEX IF NOT EXISTS idx_wdv3_status ON webhook_deliveries_v3(status);
CREATE INDEX IF NOT EXISTS idx_wdv3_event_type ON webhook_deliveries_v3(event_type);

CREATE TABLE IF NOT EXISTS webhook_event_types (
  id TEXT PRIMARY KEY,
  event_name TEXT NOT NULL UNIQUE,
  description TEXT,
  category TEXT DEFAULT 'general',
  schema_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Seed 8 standard event types
INSERT OR IGNORE INTO webhook_event_types (id, event_name, description, category) VALUES
  ('evt_mission_created',        'mission.created',           'A new mission was created',                 'mission'),
  ('evt_mission_completed',      'mission.completed',         'A mission completed successfully',           'mission'),
  ('evt_mission_failed',         'mission.failed',            'A mission failed after all retries',         'mission'),
  ('evt_payment_received',       'payment.received',          'A payment was received',                    'billing'),
  ('evt_sub_activated',          'subscription.activated',    'A subscription was activated',              'billing'),
  ('evt_sub_cancelled',          'subscription.cancelled',    'A subscription was cancelled',              'billing'),
  ('evt_team_member_added',      'team.member_added',         'A team member was added',                   'team'),
  ('evt_team_member_removed',    'team.member_removed',       'A team member was removed',                 'team');
