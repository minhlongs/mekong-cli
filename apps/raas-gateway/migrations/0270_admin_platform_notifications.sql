-- Migration: platform_notifications + platform_notification_deliveries
-- Admin-managed broadcast notifications to tenants with delivery tracking

CREATE TABLE IF NOT EXISTS platform_notifications (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  notification_type TEXT NOT NULL DEFAULT 'info',
  target_audience TEXT NOT NULL DEFAULT 'all',
  read_count INTEGER DEFAULT 0,
  published_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_notifications_type ON platform_notifications(notification_type);

CREATE TABLE IF NOT EXISTS platform_notification_deliveries (
  id TEXT PRIMARY KEY,
  notification_id TEXT NOT NULL,
  tenant_id TEXT,
  channel TEXT NOT NULL DEFAULT 'in-app',
  delivered_at TEXT,
  read_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_notification_deliveries_notif ON platform_notification_deliveries(notification_id);
