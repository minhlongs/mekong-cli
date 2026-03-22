-- Migration: Tenant notification digest configuration and delivery tracking
-- Allows tenants to configure digest frequency, channels, and notification types

CREATE TABLE IF NOT EXISTS notification_digest_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  digest_frequency TEXT NOT NULL DEFAULT 'daily',
  channels_json TEXT NOT NULL DEFAULT '["email"]',
  include_types TEXT NOT NULL DEFAULT 'all',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_digest_deliveries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  items_count INTEGER NOT NULL DEFAULT 0,
  delivery_status TEXT NOT NULL DEFAULT 'pending',
  delivered_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_notification_digest_configs_tenant_id
  ON notification_digest_configs (tenant_id);

CREATE INDEX IF NOT EXISTS idx_notification_digest_deliveries_tenant_id
  ON notification_digest_deliveries (tenant_id);

CREATE INDEX IF NOT EXISTS idx_notification_digest_deliveries_config_id
  ON notification_digest_deliveries (config_id);
