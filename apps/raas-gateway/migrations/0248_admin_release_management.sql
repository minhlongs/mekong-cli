-- Migration: Admin Release Management
-- Tables: platform_releases, platform_release_notes

CREATE TABLE IF NOT EXISTS platform_releases (
  id           TEXT NOT NULL PRIMARY KEY,
  version      TEXT NOT NULL,
  title        TEXT NOT NULL,
  description  TEXT,
  release_type TEXT NOT NULL DEFAULT 'minor',
  status       TEXT NOT NULL DEFAULT 'draft',
  released_at  TEXT,
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_releases_version ON platform_releases(version);

CREATE TABLE IF NOT EXISTS platform_release_notes (
  id         TEXT NOT NULL PRIMARY KEY,
  release_id TEXT NOT NULL,
  category   TEXT NOT NULL DEFAULT 'feature',
  note       TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_release_notes_release ON platform_release_notes(release_id);
