-- Migration 0096: Platform Announcements
-- System-wide announcements, maintenance windows, and banners for tenants

CREATE TABLE IF NOT EXISTS platform_announcements (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  type TEXT NOT NULL DEFAULT 'info', -- info, warning, maintenance, feature, critical
  priority INTEGER DEFAULT 0, -- higher = more important
  target_audience TEXT DEFAULT 'all', -- all, free, pro, enterprise
  starts_at TEXT NOT NULL DEFAULT (datetime('now')),
  ends_at TEXT,
  is_active INTEGER DEFAULT 1,
  created_by TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX idx_announcements_active ON platform_announcements(is_active, starts_at);
CREATE INDEX idx_announcements_type ON platform_announcements(type);

CREATE TABLE IF NOT EXISTS announcement_dismissals (
  id TEXT PRIMARY KEY,
  announcement_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  dismissed_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(announcement_id, tenant_id)
);
CREATE INDEX idx_dismissals_tenant ON announcement_dismissals(tenant_id);
