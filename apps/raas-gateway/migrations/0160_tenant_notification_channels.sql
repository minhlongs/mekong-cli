-- Wave 61: Tenant Notification Channels
-- Tables: notification_channels, notification_deliveries

CREATE TABLE IF NOT EXISTS notification_channels (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel_type TEXT NOT NULL,
  config_json TEXT,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_deliveries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  payload_json TEXT,
  delivered_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_notification_channels_tenant_id ON notification_channels(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notification_deliveries_tenant_id ON notification_deliveries(tenant_id);
