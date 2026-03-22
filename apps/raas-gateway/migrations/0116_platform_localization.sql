-- Migration 0116: Platform Localization
-- i18n support: locale configs, translation keys, translations

CREATE TABLE IF NOT EXISTS locale_configs (
  id TEXT PRIMARY KEY DEFAULT ('lc_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL UNIQUE,
  default_locale TEXT NOT NULL DEFAULT 'en',
  supported_locales TEXT NOT NULL DEFAULT '["en"]', -- JSON array
  timezone TEXT NOT NULL DEFAULT 'UTC',
  date_format TEXT NOT NULL DEFAULT 'YYYY-MM-DD',
  number_format TEXT NOT NULL DEFAULT 'en-US',
  currency_locale TEXT NOT NULL DEFAULT 'en-US',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_locale_cfg_tenant ON locale_configs(tenant_id);

CREATE TABLE IF NOT EXISTS translation_keys (
  id TEXT PRIMARY KEY DEFAULT ('tk_' || lower(hex(randomblob(8)))),
  key_path TEXT NOT NULL, -- e.g. 'missions.status.completed'
  namespace TEXT NOT NULL DEFAULT 'common', -- common, missions, billing, errors
  default_value TEXT NOT NULL,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_trans_key_path ON translation_keys(key_path, namespace);

CREATE TABLE IF NOT EXISTS translations (
  id TEXT PRIMARY KEY DEFAULT ('tr_' || lower(hex(randomblob(8)))),
  key_id TEXT NOT NULL,
  locale TEXT NOT NULL,
  value TEXT NOT NULL,
  is_verified INTEGER NOT NULL DEFAULT 0,
  translated_by TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_trans_unique ON translations(key_id, locale);
CREATE INDEX IF NOT EXISTS idx_trans_locale ON translations(locale);
