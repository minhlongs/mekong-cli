CREATE TABLE IF NOT EXISTS marketplace_plugins (
  id TEXT PRIMARY KEY,
  developer_id TEXT NOT NULL REFERENCES stakeholders(id),
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  category TEXT DEFAULT 'integration' CHECK (category IN ('integration','ai_agent','template','analytics','automation')),
  version TEXT DEFAULT '1.0.0',
  pricing_type TEXT DEFAULT 'free' CHECK (pricing_type IN ('free','one_time','subscription','usage')),
  price_credits INTEGER DEFAULT 0,
  install_count INTEGER DEFAULT 0,
  rating_avg REAL DEFAULT 0,
  rating_count INTEGER DEFAULT 0,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft','review','published','suspended')),
  webhook_url TEXT,
  config_schema JSON DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS plugin_installs (
  id TEXT PRIMARY KEY,
  plugin_id TEXT NOT NULL REFERENCES marketplace_plugins(id),
  tenant_id TEXT NOT NULL REFERENCES tenants(id),
  installed_by TEXT NOT NULL REFERENCES stakeholders(id),
  config JSON DEFAULT '{}',
  status TEXT DEFAULT 'active' CHECK (status IN ('active','disabled','uninstalled')),
  installed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS plugin_reviews (
  id TEXT PRIMARY KEY,
  plugin_id TEXT NOT NULL REFERENCES marketplace_plugins(id),
  reviewer_id TEXT NOT NULL REFERENCES stakeholders(id),
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  review_text TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(plugin_id, reviewer_id)
);
