-- Migration 0049: Event Bus tables for mission lifecycle pub/sub

CREATE TABLE IF NOT EXISTS event_bus (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  payload TEXT DEFAULT '{}',
  processed INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_event_bus_tenant ON event_bus(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_event_bus_unprocessed ON event_bus(processed, created_at);
CREATE INDEX IF NOT EXISTS idx_event_bus_type ON event_bus(type);

CREATE TABLE IF NOT EXISTS event_subscriptions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  event_types TEXT NOT NULL,
  webhook_url TEXT NOT NULL,
  active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_event_subs_tenant ON event_subscriptions(tenant_id, active);
