-- Migration: 0277_tenant_api_changelog
-- Per-tenant API changelog entries and subscriber notification preferences

CREATE TABLE IF NOT EXISTS tenant_api_changelog_entries (
  id           TEXT    PRIMARY KEY,
  tenant_id    TEXT    NOT NULL,
  version      TEXT    NOT NULL,
  title        TEXT    NOT NULL,
  description  TEXT,
  change_type  TEXT    NOT NULL DEFAULT 'feature',
  published    INTEGER NOT NULL DEFAULT 0,
  published_at TEXT,
  created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenant_api_changelog_tenant
  ON tenant_api_changelog_entries (tenant_id);

CREATE TABLE IF NOT EXISTS tenant_api_changelog_subscriptions (
  id           TEXT PRIMARY KEY,
  tenant_id    TEXT NOT NULL,
  user_id      TEXT NOT NULL,
  notify_on    TEXT NOT NULL DEFAULT 'all',
  subscribed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenant_api_changelog_subs_tenant
  ON tenant_api_changelog_subscriptions (tenant_id);
