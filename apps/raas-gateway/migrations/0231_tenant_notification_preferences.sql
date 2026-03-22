-- Migration 0231: Tenant Notification Preferences
-- Stores per-tenant notification settings and channel configurations

CREATE TABLE IF NOT EXISTS notification_preferences (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel TEXT NOT NULL DEFAULT 'email',
  event_type TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  frequency TEXT NOT NULL DEFAULT 'immediate',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notification_preferences_tenant ON notification_preferences(tenant_id);

CREATE TABLE IF NOT EXISTS notification_channels (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel_type TEXT NOT NULL,
  config_json TEXT,
  verified INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notification_channels_tenant ON notification_channels(tenant_id);
