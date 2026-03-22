-- Admin platform changelog — tracks platform releases, features, and updates
CREATE TABLE IF NOT EXISTS platform_changelog_entries (
  id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  change_type TEXT NOT NULL DEFAULT 'feature',
  severity TEXT NOT NULL DEFAULT 'minor',
  author TEXT,
  published_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_changelog_entries_version ON platform_changelog_entries(version);

-- Subscribers who receive changelog notifications
CREATE TABLE IF NOT EXISTS platform_changelog_subscribers (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  email TEXT,
  notify_on TEXT NOT NULL DEFAULT 'all',
  subscribed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_changelog_subscribers_tenant ON platform_changelog_subscribers(tenant_id);
