-- Migration 0056: API Versioning tables
-- Stores changelog entries and usage tracking per API version

CREATE TABLE IF NOT EXISTS api_version_changelog (
  id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  change_type TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_changelog_version ON api_version_changelog(version, created_at);

CREATE TABLE IF NOT EXISTS api_version_usage (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  api_version TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_version_usage_version ON api_version_usage(api_version, created_at);
CREATE INDEX IF NOT EXISTS idx_version_usage_tenant ON api_version_usage(tenant_id);
