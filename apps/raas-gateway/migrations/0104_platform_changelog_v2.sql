-- Platform Changelog V2: versioned entries, subscriptions, read tracking
CREATE TABLE IF NOT EXISTS changelog_entries_v2 (
  id TEXT PRIMARY KEY DEFAULT ('cle_' || lower(hex(randomblob(8)))),
  version TEXT NOT NULL, -- semantic version e.g. '2.1.0'
  title TEXT NOT NULL,
  content TEXT NOT NULL, -- markdown
  category TEXT NOT NULL DEFAULT 'feature', -- feature, improvement, bugfix, breaking, security, deprecation
  severity TEXT NOT NULL DEFAULT 'minor', -- major, minor, patch
  tags TEXT DEFAULT '[]', -- JSON array
  is_published INTEGER NOT NULL DEFAULT 0,
  published_at TEXT,
  author TEXT,
  related_api_versions TEXT DEFAULT '[]', -- JSON array of affected API versions
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cle_version ON changelog_entries_v2(version);
CREATE INDEX IF NOT EXISTS idx_cle_category ON changelog_entries_v2(category);
CREATE INDEX IF NOT EXISTS idx_cle_published ON changelog_entries_v2(is_published, published_at);

CREATE TABLE IF NOT EXISTS changelog_subscriptions (
  id TEXT PRIMARY KEY DEFAULT ('cls_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  categories TEXT DEFAULT '["feature","breaking","security"]', -- JSON array
  notify_via TEXT NOT NULL DEFAULT 'in_app', -- in_app, email, webhook
  webhook_url TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cls_tenant ON changelog_subscriptions(tenant_id);

CREATE TABLE IF NOT EXISTS changelog_reads (
  id TEXT PRIMARY KEY DEFAULT ('clr_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  entry_id TEXT NOT NULL,
  read_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_clr_tenant ON changelog_reads(tenant_id, entry_id);
