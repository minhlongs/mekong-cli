-- Admin Platform Maintenance Windows — schedule and track platform maintenance
CREATE TABLE IF NOT EXISTS platform_maintenance_windows (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  scheduled_start TEXT NOT NULL,
  scheduled_end TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled',
  affected_services TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_maintenance_status ON platform_maintenance_windows(status);

-- Maintenance notification log — track who was notified per window
CREATE TABLE IF NOT EXISTS platform_maintenance_notifications (
  id TEXT PRIMARY KEY,
  maintenance_id TEXT NOT NULL,
  notification_type TEXT NOT NULL DEFAULT 'email',
  sent_at TEXT,
  recipient_count INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_maintenance_notif_maint ON platform_maintenance_notifications(maintenance_id);
