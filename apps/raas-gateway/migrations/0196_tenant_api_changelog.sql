-- Migration: 0196_tenant_api_changelog
-- Tables for per-tenant API changelog entries and email subscriptions

CREATE TABLE IF NOT EXISTS api_changelog_entries (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL,
  change_type TEXT NOT NULL DEFAULT 'update',
  endpoint    TEXT NOT NULL,
  description TEXT NOT NULL,
  breaking    INTEGER NOT NULL DEFAULT 0,
  version     TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_changelog_entries_tenant_id
  ON api_changelog_entries (tenant_id);

CREATE TABLE IF NOT EXISTS api_changelog_subscriptions (
  id             TEXT PRIMARY KEY,
  tenant_id      TEXT NOT NULL,
  email          TEXT NOT NULL,
  notify_breaking INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_changelog_subscriptions_tenant_id
  ON api_changelog_subscriptions (tenant_id);
